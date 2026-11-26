"""Caneta de esqueletos: desenha traços por código, passando por pontos.

Usamos um spline (curva suave que passa por todos os pontos): em cada
ponto a tangente é a média das direções vizinhas; num CANTO (Corner)
cada lado usa a própria direção, criando uma quina. As alças medem 1/3
da distância entre os pontos, o que evita 'barrigas' exageradas.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..model import Cubic, Stroke


@dataclass(frozen=True)
class Corner:
    """Ponto onde o traço faz quina (muda de direção bruscamente)."""

    x: float
    y: float


def _unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else np.zeros(2)


class SkeletonPen:
    @staticmethod
    def xy(p) -> np.ndarray:
        """Coordenadas de um ponto de receita (tupla ou Corner)."""
        return np.array([p.x, p.y], float) if isinstance(p, Corner) else np.array(p, float)

    @classmethod
    def spline(cls, points, closed: bool = False, start_tangent=None, end_tangent=None) -> Stroke:
        P = [cls.xy(p) for p in points]
        corner = [isinstance(p, Corner) for p in points]
        n = len(P)
        if n == 1:
            return cls.dot(P[0])

        def smooth(i):
            a, b, c = P[(i - 1) % n], P[i], P[(i + 1) % n]
            return _unit(_unit(b - a) + _unit(c - b))

        def out_tan(i):
            if not closed and i == 0:
                return _unit(np.array(start_tangent, float)) if start_tangent is not None else _unit(P[1] - P[0])
            if corner[i]:
                return _unit(P[(i + 1) % n] - P[i])
            return smooth(i)

        def in_tan(j):
            if not closed and j == n - 1:
                return _unit(np.array(end_tangent, float)) if end_tangent is not None else _unit(P[j] - P[j - 1])
            if corner[j]:
                return _unit(P[j] - P[j - 1])
            return smooth(j)

        segs = []
        for i in range(n if closed else n - 1):
            j = (i + 1) % n
            a, b = P[i], P[j]
            d = np.linalg.norm(b - a) / 3
            c1, c2 = a + out_tan(i) * d, b - in_tan(j) * d
            segs.append(Cubic(tuple(a), tuple(c1), tuple(c2), tuple(b)))
        return Stroke(segs, closed)

    @staticmethod
    def dot(p) -> Stroke:
        q = tuple(float(v) for v in (p.x, p.y)) if isinstance(p, Corner) else tuple(map(float, p))
        return Stroke([Cubic(q, q, q, q)])

    @staticmethod
    def line(a, b) -> Stroke:
        a, b = np.array(a, float), np.array(b, float)
        return Stroke([Cubic(tuple(a), tuple(a + (b - a) / 3), tuple(a + 2 * (b - a) / 3), tuple(b))])


class HandJitter:
    """Ondulação suave e determinística: devolve 'vida' a curvas desenhadas por código.

    A amplitude é pequena (padrão 4 un) e some perto das pontas protegidas
    (entrada e saída da cursiva), para as conexões continuarem exatas.
    """

    def __init__(self, amplitude: float = 4.0, wavelength: float = 260.0):
        self.amplitude = amplitude
        self.wavelength = wavelength

    def apply(self, stroke: Stroke, seed: str, protect=()) -> Stroke:
        rng = np.random.default_rng(self._seed(seed))
        ph = rng.uniform(0, 2 * np.pi, 4)
        A, L = self.amplitude, self.wavelength
        prot = [np.array(p, float) for p in protect]

        def fn(p):
            x, y = p
            w = 1.0
            for q in prot:
                w = min(w, np.linalg.norm(np.array(p) - q) / 80.0)
            dx = A * np.sin(2 * np.pi * y / L + ph[0]) + 0.5 * A * np.sin(2 * np.pi * x / (0.7 * L) + ph[1])
            dy = A * np.sin(2 * np.pi * x / L + ph[2]) + 0.5 * A * np.sin(2 * np.pi * y / (0.7 * L) + ph[3])
            return (x + w * dx, y + w * dy)

        return stroke.transformed(fn)

    @staticmethod
    def _seed(text: str) -> int:
        """Semente estável entre execuções (hash() do Python muda a cada execução)."""
        return sum((i + 1) * ord(ch) for i, ch in enumerate(text)) % (2 ** 32)
