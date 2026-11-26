"""Monta o glifo final de um peso: esqueleto → compensação → expansão → espaçamento."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..design.spacer import Spacer
from ..model import Component, Cubic, GlyphSkeleton
from .anchors import AnchorCalculator
from .stroke_expander import Piece, StrokeExpander
from .weight_profile import MAX_PEN, WeightProfile, ZoneCompensator


@dataclass
class OutlineGlyph:
    """Glifo pronto para virar UFO: contornos fechados + largura de avanço."""

    name: str
    unicodes: list[int]
    contours: list[list[Cubic]]
    advance: float
    components: list[Component] = field(default_factory=list)
    anchors: dict = field(default_factory=dict)

    def bounds(self):
        if not self.contours:
            return None
        pts = np.vstack([c.sample(12) for cont in self.contours for c in cont])
        return pts[:, 0].min(), pts[:, 1].min(), pts[:, 0].max(), pts[:, 1].max()


class OutlineGlyphFactory:
    def __init__(self, compensator: ZoneCompensator | None = None, spacer: Spacer | None = None,
                 anchors: AnchorCalculator | None = None):
        self.compensator = compensator or ZoneCompensator()
        self.expander = StrokeExpander(MAX_PEN)
        self.spacer = spacer or Spacer()
        self.anchors = anchors or AnchorCalculator()

    def build(self, skel: GlyphSkeleton, prof: WeightProfile) -> OutlineGlyph:
        fn = self.compensator.transform_fn(skel, prof)
        g = skel.transformed(fn)
        contours = []
        for stroke in skel.strokes:
            # A divisão em cápsulas é decidida no esqueleto ORIGINAL (igual em todos os pesos)
            # e só depois cada pedaço recebe a compensação do peso: masters compatíveis.
            for piece in self.expander.pieces(stroke):
                moved = Piece([seg.transformed(fn) for seg in piece.segments], piece.is_dot)
                contours.append(self.expander.capsule(moved, prof.pen, prof.dot_pen))
        anchors = {**self.anchors.compute(g), **g.anchors}
        # âncoras de acento ('_top'...) marcam a BORDA visual: não passam pela compensação de peso
        anchors.update({k: v for k, v in skel.anchors.items() if k.startswith("_")})
        out = OutlineGlyph(g.name, list(g.unicodes), contours, 0.0, list(g.components), anchors)
        return self.spacer.space(out, prof)
