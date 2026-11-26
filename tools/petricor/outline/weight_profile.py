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


@dataclass(frozen=True)
class LoopInflation:
    """Laço que cresce com o peso, para continuar aberto com caneta grossa.

    Pontos a menos de r0 do centro afastam-se dele pelo fator
    1 + rate·(caneta − 20); entre r0 e r1 o efeito some aos poucos.
    Só muda posições (não a estrutura), então os masters seguem compatíveis.
    """

    center: tuple[float, float]
    r0: float = 78.0
    r1: float = 100.0
    rate: float = 0.0032

    def fn(self, pen: float):
        cx, cy = self.center
        k = self.rate * max(pen - 20.0, 0.0)

        def inflate(p):
            dx, dy = p[0] - cx, p[1] - cy
            d = float(np.hypot(dx, dy))
            w = 1.0 if d <= self.r0 else max(0.0, (self.r1 - d) / (self.r1 - self.r0))
            s = 1 + k * w
            return (cx + dx * s, cy + dy * s)

        return inflate


# Só para letras CURSIVAS (com âncora de saída): o 'o' de forma não tem laço.
CURSIVE_LOOPS = {"o": LoopInflation((225.0, 340.0), r0=95.0, r1=115.0, rate=0.0018)}


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

        loop = CURSIVE_LOOPS.get(g.name.split(".")[0]) if "exit" in g.anchors else None
        pre = loop.fn(prof.pen) if loop else (lambda p: p)

        def fn(p):
            q = pre(p)
            return (q[0] * fx, fy(q[1]))

        return fn

    @staticmethod
    def _lowest_is_dot(g: GlyphSkeleton) -> bool:
        lowest = min(g.strokes, key=lambda s: s.sample(8)[:, 1].min())
        return all(np.ptp(seg.as_array(), axis=0).max() < 0.5 for seg in lowest.segments)
