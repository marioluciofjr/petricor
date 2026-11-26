"""Âncoras: pontos onde os acentos se encaixam em cada letra.

As alturas são FIXAS (a borda visual das letras não muda com o peso,
graças à compensação por zonas); só a posição horizontal é medida no
esqueleto, no centro da parte de cima (ou de baixo) da letra.
"""
from __future__ import annotations

import numpy as np

from ..design.accents import MARK_NAMES, is_dot_stroke
from ..design.metrics import DEFAULT_METRICS, Metrics
from ..model import GlyphSkeleton

LOWER_EXTRA = {"idotless", "jdotless"}


class AnchorCalculator:
    TOP_GAP_LOWER = 65
    TOP_GAP_UPPER = 55
    CONNECTOR_MARGIN = 50

    def __init__(self, metrics: Metrics = DEFAULT_METRICS):
        self.m = metrics

    def compute(self, g: GlyphSkeleton) -> dict:
        base = g.name.split(".")[0]
        if g.name in MARK_NAMES or not g.strokes or not self._is_letter(base):
            return {}
        upper = base[0].isupper() and base not in LOWER_EXTRA
        line = self.m.cap_height if upper else self.m.x_height
        pts = self._body_points(g)
        if len(pts) == 0:
            return {}
        out = {}
        top = pts[pts[:, 1] >= 0.72 * line]
        if len(top):
            gap = self.TOP_GAP_UPPER if upper else self.TOP_GAP_LOWER
            out["top"] = (float((top[:, 0].min() + top[:, 0].max()) / 2), line + gap)
        low = pts[pts[:, 1] <= 0.22 * line]
        if len(low):
            out["bottom"] = (float((low[:, 0].min() + low[:, 0].max()) / 2), 0.0)
            out["ogonek"] = (float(low[:, 0].max() - 15), 0.0)
        high = pts[pts[:, 1] >= 0.75 * pts[:, 1].max()]
        asc_line = {"t": self.m.t_height, "L": self.m.cap_height}.get(base, self.m.ascender)
        out["caron"] = (float(high[:, 0].max() + 45), asc_line - 160)
        return out

    @staticmethod
    def _is_letter(base: str) -> bool:
        return base in LOWER_EXTRA or (len(base) == 1 and base.isalpha())

    def _body_points(self, g: GlyphSkeleton) -> np.ndarray:
        """Pontos do traço, sem pingos e sem os conectores da cursiva."""
        strokes = [s for s in g.strokes if not is_dot_stroke(s)]
        if not strokes:
            return np.zeros((0, 2))
        pts = np.vstack([s.sample(24) for s in strokes])
        if "entry" in g.anchors:
            pts = pts[pts[:, 0] > g.anchors["entry"][0] + self.CONNECTOR_MARGIN]
        if "exit" in g.anchors:
            pts = pts[pts[:, 0] < g.anchors["exit"][0] - self.CONNECTOR_MARGIN]
        return pts
