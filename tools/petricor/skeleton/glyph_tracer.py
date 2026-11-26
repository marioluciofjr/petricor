"""Orquestra a vetorização de UMA célula: recorte → tinta → esqueleto → Bézier → unidades."""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from ..model import GlyphSkeleton, Point
from ..scan.ink import InkExtractor
from .fitter import BezierFitter
from .skeletonizer import Skeletonizer
from .tracer import StrokeTracer


@dataclass(frozen=True)
class PixelToUnits:
    """Converte (x, y) da imagem para unidades da fonte.

    y é invertido (na imagem cresce para baixo) e a linha de base da
    célula vira y = 0.
    """

    scale: float
    origin_x: float
    baseline_y: float

    def __call__(self, p: Point) -> Point:
        return ((p[0] - self.origin_x) * self.scale, (self.baseline_y - p[1]) * self.scale)


class ComponentFilter:
    """Remove manchas pequenas em relação ao maior traço da célula.

    Ex.: o pontinho de caneta ao lado do 'B' some, mas o pingo do 'i'
    (bem maior em proporção) fica.
    """

    def __init__(self, rel_min_area: float = 0.03):
        self.rel_min_area = rel_min_area

    def apply(self, mask: np.ndarray) -> np.ndarray:
        n, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), connectivity=8)
        if n <= 2:
            return mask
        areas = stats[1:, cv2.CC_STAT_AREA]
        keep = np.zeros(n, bool)
        keep[1:] = areas >= self.rel_min_area * areas.max()
        return keep[labels]


@dataclass
class TracingParts:
    """As peças trocáveis da vetorização (injeção de dependência)."""

    ink: InkExtractor = None
    skeletonizer: Skeletonizer = None
    tracer: StrokeTracer = None
    fitter: BezierFitter = None

    def __post_init__(self):
        self.ink = self.ink or InkExtractor()
        self.skeletonizer = self.skeletonizer or Skeletonizer()
        self.tracer = self.tracer or StrokeTracer()
        self.fitter = self.fitter or BezierFitter()


class GlyphTracer:
    def __init__(self, parts: TracingParts | None = None, inset: int = 12):
        parts = parts or TracingParts()
        self.ink = parts.ink
        self.skeletonizer = parts.skeletonizer
        self.tracer = parts.tracer
        self.fitter = parts.fitter
        self.inset = inset
        self.filter = ComponentFilter()

    def ink_mask(self, cell_bgr: np.ndarray) -> np.ndarray:
        """Máscara da tinta com margem interna zerada (ignora restos de borda)."""
        mask = self.ink.extract(cell_bgr)
        i = self.inset
        mask[:i, :] = mask[-i:, :] = False
        mask[:, :i] = mask[:, -i:] = False
        return self.filter.apply(mask)

    def trace(self, cell_bgr: np.ndarray, to_units: PixelToUnits, name: str,
              unicodes: list[int]) -> tuple[GlyphSkeleton, float]:
        mask = self.ink_mask(cell_bgr)
        res = self.skeletonizer.run(mask)
        strokes = []
        for path in self.tracer.trace(res.skeleton, res.stroke_width):
            stroke = self.fitter.fit(path)
            if stroke is not None:
                strokes.append(stroke.transformed(to_units))
        glyph = GlyphSkeleton(name, unicodes, strokes)
        b = glyph.bounds()
        glyph.advance = (b[2] - b[0]) if b else 0.0
        return glyph, res.stroke_width
