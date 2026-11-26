"""Perfis de peso (Strategy): quanto a caneta engrossa em cada instância.

O traço é monolinear: só muda a espessura ('pen', em unidades).
Para a borda do traço continuar nas mesmas linhas (base, altura-x,
maiúsculas) em todos os pesos, a linha central é empurrada para dentro
em meia caneta, zona por zona (ZoneCompensator).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..design.accents import MARK_ROLE
from ..design.harmonizer import GlyphClassifier
from ..model import GlyphSkeleton


@dataclass(frozen=True)
class WeightProfile:
    name: str
    wght: int
    pen: float
    x_expand: float = 0.0  # alarga levemente os pesos pesados para os vazios não fecharem

    @property
    def dot_pen(self) -> float:
        """Pontos (pingo do i, ponto final) ficam um pouco maiores que o traço."""
        return self.pen * 1.25 + 30


INSTANCES = [
    WeightProfile("Thin", 100, 16, 0.00),
    WeightProfile("ExtraLight", 200, 28, 0.01),
    WeightProfile("Light", 300, 42, 0.02),
    WeightProfile("Regular", 400, 60, 0.03),
    WeightProfile("Medium", 500, 76, 0.045),
    WeightProfile("SemiBold", 600, 94, 0.06),
    WeightProfile("Bold", 700, 112, 0.08),
    WeightProfile("ExtraBold", 800, 131, 0.10),
    WeightProfile("Black", 900, 150, 0.12),
]
MASTERS = [INSTANCES[0], INSTANCES[3], INSTANCES[8]]
MAX_PEN = INSTANCES[-1].pen


def profile(name: str) -> WeightProfile:
    return next(p for p in INSTANCES if p.name == name)


class ZoneCompensator:
    """Aplica, para um peso, o deslocamento por zonas na linha central."""

    SNAP = 45  # distância máxima para 'grudar' numa linha conhecida

    def __init__(self, classifier: GlyphClassifier | None = None):
        self.classifier = classifier or GlyphClassifier()
        m = self.classifier.metrics
        self.lines_top = [m.x_height, m.t_height, m.cap_height, m.ascender]
        self.descender = m.descender

    def knots_for(self, g: GlyphSkeleton) -> list:
        if g.name in MARK_ROLE:  # acentos: a borda que encosta na letra fica fixa
            return [(0.0, 1)] if MARK_ROLE[g.name] in ("top", "caron") else [(0.0, -1)]
        knots = self.classifier.zones_for(g.name)
        return knots if knots is not None else self._infer(g)

    def _infer(self, g: GlyphSkeleton) -> list:
        """Glifo sem regra (Æ, ø, aspas...): gruda nas linhas mais próximas do seu contorno."""
        b = g.bounds()
        if b is None:
            return []
        knots = []
        if b[1] < self.descender + 80:
            knots.append((self.descender, 1))
        if abs(b[1]) < self.SNAP or b[1] < self.descender + 80:
            knots.append((0.0, 1))
        near = min(self.lines_top, key=lambda y: abs(y - b[3]))
        if abs(near - b[3]) < self.SNAP:
            knots.append((near, -1))
        return knots

    def apply(self, g: GlyphSkeleton, prof: WeightProfile) -> GlyphSkeleton:
        return g.transformed(self.transform_fn(g, prof))

    def transform_fn(self, g: GlyphSkeleton, prof: WeightProfile):
        """Função ponto → ponto da compensação (aplicável a qualquer pedaço do glifo)."""
        knots = self.knots_for(g)
        d = prof.pen / 2
        if g.strokes and knots and knots[0][1] == 1 and self._lowest_is_dot(g):
            d_bottom = prof.dot_pen / 2  # ponto final pousa na base pela borda
        else:
            d_bottom = d
        src = np.array([y for y, _ in knots], float)
        dst = np.array([y + (d_bottom if s == 1 and i == 0 else d * s) for i, (y, s) in enumerate(knots)], float)
        fx = 1 + prof.x_expand

        def fy(y):
            if len(src) == 0:
                return y
            if len(src) == 1 or y <= src[0]:
                return y + (dst[0] - src[0])
            if y >= src[-1]:
                return y + (dst[-1] - src[-1])
            return float(np.interp(y, src, dst))

        return lambda p: (p[0] * fx, fy(p[1]))

    @staticmethod
    def _lowest_is_dot(g: GlyphSkeleton) -> bool:
        lowest = min(g.strokes, key=lambda s: s.sample(8)[:, 1].min())
        return all(np.ptp(seg.as_array(), axis=0).max() < 0.5 for seg in lowest.segments)
