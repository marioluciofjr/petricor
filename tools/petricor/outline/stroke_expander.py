"""Expansão do traço: dá espessura à linha central, como uma caneta de ponta redonda.

Ideia: cada trecho LISO do traço vira uma "cápsula" fechada:
    lado direito (ida) → ponta redonda → lado esquerdo (volta) → ponta redonda.
Nos cantos e nas curvas muito fechadas, o traço é dividido em várias
cápsulas que se sobrepõem; as pontas redondas fazem a junção, como a
esferográfica faria no papel.

Regra de ouro para a fonte variável: a QUANTIDADE e a ORDEM dos pontos
dependem só do esqueleto, nunca da espessura. Assim o Thin, o Regular e
o Black têm contornos compatíveis e podem ser interpolados.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..model import Cubic, Stroke

KAPPA = 0.5523  # alça que aproxima um quarto de círculo com uma cúbica

Contour = list[Cubic]


def _v(p) -> np.ndarray:
    return np.asarray(p, float)


def _unit(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else np.zeros(2)


def _cross(a, b) -> float:
    return float(a[0] * b[1] - a[1] * b[0])


class CubicGeometry:
    """Tangentes e curvaturas nas pontas de uma cúbica (com casos degenerados)."""

    @staticmethod
    def start_tangent(c: Cubic) -> np.ndarray:
        p = c.as_array()
        for q in (p[1], p[2], p[3]):
            if np.linalg.norm(q - p[0]) > 1e-6:
                return _unit(q - p[0])
        return np.array([1.0, 0.0])

    @staticmethod
    def end_tangent(c: Cubic) -> np.ndarray:
        p = c.as_array()
        for q in (p[2], p[1], p[0]):
            if np.linalg.norm(p[3] - q) > 1e-6:
                return _unit(p[3] - q)
        return np.array([1.0, 0.0])

    # Alça menor que 8% da corda: a fórmula de curvatura 'explode' (divide por h³).
    # Nesses casos tratamos a ponta como reta (curvatura 0).
    MIN_HANDLE_RATIO = 0.08

    @classmethod
    def _handle_ok(cls, p, h) -> bool:
        return h > max(1e-3, cls.MIN_HANDLE_RATIO * np.linalg.norm(p[3] - p[0]))

    @classmethod
    def start_curvature(cls, c: Cubic) -> float:
        p = c.as_array()
        h = np.linalg.norm(p[1] - p[0])
        return 2 / 3 * _cross(p[1] - p[0], p[2] - p[1]) / h ** 3 if cls._handle_ok(p, h) else 0.0

    @classmethod
    def end_curvature(cls, c: Cubic) -> float:
        p = c.as_array()
        h = np.linalg.norm(p[3] - p[2])
        return 2 / 3 * _cross(p[2] - p[1], p[3] - p[2]) / h ** 3 if cls._handle_ok(p, h) else 0.0

    @staticmethod
    def is_point(c: Cubic, eps: float = 0.5) -> bool:
        p = c.as_array()
        return float(np.ptp(p, axis=0).max()) < eps

    @staticmethod
    def turning(c: Cubic) -> float:
        """Ângulo (graus) entre a tangente inicial e a final."""
        a, b = CubicGeometry.start_tangent(c), CubicGeometry.end_tangent(c)
        return float(np.degrees(np.arccos(np.clip(a @ b, -1, 1))))

    @staticmethod
    def min_radius(c: Cubic, n: int = 33) -> tuple[float, float]:
        """Menor raio de curvatura ao longo da cúbica e o t onde ocorre."""
        best, best_t = np.inf, 0.5
        for t in np.linspace(0.02, 0.98, n):
            d1 = c.derivative(t)
            p = c.as_array()
            d2 = 6 * (1 - t) * (p[2] - 2 * p[1] + p[0]) + 6 * t * (p[3] - 2 * p[2] + p[1])
            speed = np.linalg.norm(d1)
            k = abs(_cross(d1, d2)) / speed ** 3 if speed > 1e-9 else 0
            r = 1 / k if k > 1e-12 else np.inf
            if r < best:
                best, best_t = r, t
        return best, best_t


@dataclass
class Piece:
    """Trecho liso de um traço (vira uma cápsula) ou um ponto (vira um círculo)."""

    segments: list[Cubic]
    is_dot: bool = False


class PieceSplitter:
    """Divide o traço em trechos lisos que aguentam a espessura máxima.

    Depende de max_pen (a caneta mais grossa, do Black), e não da caneta
    de cada peso: assim a divisão é igual em todos os masters.
    """

    def __init__(self, max_pen: float, corner_deg: float = 25.0, max_turn_deg: float = 60.0):
        self.max_r = max_pen / 2
        self.corner_deg = corner_deg
        self.max_turn_deg = max_turn_deg

    def split(self, stroke: Stroke) -> list[Piece]:
        segs = [s for s in stroke.segments if not CubicGeometry.is_point(s)]
        if not segs:
            return [Piece([stroke.segments[0]], is_dot=True)]
        segs = [part for s in segs for part in self._subdivide(s)]
        pieces, cur = [], [segs[0]]
        for prev, nxt in zip(segs[:-1], segs[1:]):
            angle = np.degrees(np.arccos(np.clip(CubicGeometry.end_tangent(prev) @ CubicGeometry.start_tangent(nxt), -1, 1)))
            if angle > self.corner_deg:
                pieces.append(cur)
                cur = []
            cur.append(nxt)
        pieces.append(cur)
        if stroke.closed and len(pieces) == 1:
            pieces = self._halve(pieces[0])
        out = []
        for p in pieces:
            for q in self._cut_tight(p):
                out += self._cut_long_turns(q)
        return [Piece(p) for p in out if p]

    MAX_PIECE_TURN = 270.0

    def _cut_long_turns(self, segs: list[Cubic]) -> list[list[Cubic]]:
        """Trecho que gira mais de 270° acabaria passando por cima de si mesmo
        (cápsula que se cruza). Cortamos antes disso; as pontas redondas unem."""
        out, cur, turn = [], [], 0.0
        for s in segs:
            t = CubicGeometry.turning(s)
            if cur and turn + t > self.MAX_PIECE_TURN:
                out.append(cur)
                cur, turn = [], 0.0
            cur.append(s)
            turn += t
        out.append(cur)
        return out

    def _subdivide(self, c: Cubic, depth: int = 0) -> list[Cubic]:
        """Divide cúbicas que viram demais (o deslocamento fica impreciso)."""
        if depth < 3 and CubicGeometry.turning(c) > self.max_turn_deg:
            a, b = c.split(0.5)
            return self._subdivide(a, depth + 1) + self._subdivide(b, depth + 1)
        return [c]

    @staticmethod
    def _halve(segs: list[Cubic]) -> list[list[Cubic]]:
        if len(segs) >= 2:
            k = len(segs) // 2
            return [segs[:k], segs[k:]]
        a, b = segs[0].split(0.5)
        return [[a], [b]]

    def _cut_tight(self, segs: list[Cubic]) -> list[list[Cubic]]:
        """Curva mais fechada que a caneta do Black? Corta ali (vira 'canto' redondo)."""
        out, cur = [], []
        for s in segs:
            r, t = CubicGeometry.min_radius(s)
            if r < self.max_r and 0.05 < t < 0.95:
                a, b = s.split(t)
                cur.append(a)
                out.append(cur)
                cur = [b]
            else:
                cur.append(s)
        out.append(cur)
        return out


class CubicOffsetter:
    """Desloca uma cúbica para o lado (aproximação clássica por escala das alças).

    s > 0 → lado direito do sentido do traço; s < 0 → lado esquerdo.
    Do lado de fora de uma curva o caminho fica mais longo (alça × (1 + s·κ));
    do lado de dentro, mais curto.
    """

    MIN_FACTOR = 0.1
    MAX_FACTOR = 3.0

    @staticmethod
    def right_normal(t: np.ndarray) -> np.ndarray:
        return np.array([t[1], -t[0]])

    def offset(self, c: Cubic, s: float) -> Cubic:
        p = c.as_array()
        t0, t1 = CubicGeometry.start_tangent(c), CubicGeometry.end_tangent(c)
        k0, k1 = CubicGeometry.start_curvature(c), CubicGeometry.end_curvature(c)
        q0 = p[0] + self.right_normal(t0) * s
        q3 = p[3] + self.right_normal(t1) * s
        f0 = float(np.clip(1 + s * k0, self.MIN_FACTOR, self.MAX_FACTOR))
        f1 = float(np.clip(1 + s * k1, self.MIN_FACTOR, self.MAX_FACTOR))
        q1 = q0 + (p[1] - p[0]) * f0
        q2 = q3 + (p[2] - p[3]) * f1
        return Cubic(*(tuple(map(float, q)) for q in (q0, q1, q2, q3)))


class CapBuilder:
    """Pontas redondas (meio círculo) e pontos (círculo inteiro)."""

    @staticmethod
    def half_circle(center, frm, direction, r) -> list[Cubic]:
        """De 'frm' até o ponto oposto, contornando 'center' pelo lado 'direction'."""
        c, a, u = _v(center), _v(frm), _unit(_v(direction))
        n = _unit(a - c)
        b, e = c + u * r, c - n * r
        arc1 = Cubic(tuple(a), tuple(a + u * r * KAPPA), tuple(b + n * r * KAPPA), tuple(b))
        arc2 = Cubic(tuple(b), tuple(b - n * r * KAPPA), tuple(e + u * r * KAPPA), tuple(e))
        return [arc1, arc2]

    @staticmethod
    def circle(center, r) -> Contour:
        """Círculo anti-horário (orientação de contorno externo no UFO)."""
        c = _v(center)
        pts = [c + r * np.array(d) for d in [(1, 0), (0, 1), (-1, 0), (0, -1)]]
        tans = [np.array(d) for d in [(0, 1), (-1, 0), (0, -1), (1, 0)]]
        out = []
        for i in range(4):
            a, b = pts[i], pts[(i + 1) % 4]
            ta, tb = tans[i], tans[(i + 1) % 4]
            out.append(Cubic(tuple(a), tuple(a + ta * r * KAPPA), tuple(b - tb * r * KAPPA), tuple(b)))
        return out


class StrokeExpander:
    """Fachada: Stroke + espessura → lista de contornos fechados (cúbicas)."""

    def __init__(self, max_pen: float):
        self.splitter = PieceSplitter(max_pen)
        self.offsetter = CubicOffsetter()

    def pieces(self, stroke: Stroke) -> list[Piece]:
        return self.splitter.split(stroke)

    def expand(self, stroke: Stroke, pen: float, dot_pen: float | None = None) -> list[Contour]:
        return [self.capsule(p, pen, dot_pen or pen) for p in self.pieces(stroke)]

    def capsule(self, piece: Piece, pen: float, dot_pen: float) -> Contour:
        if piece.is_dot:
            return CapBuilder.circle(piece.segments[0].p0, dot_pen / 2)
        r = pen / 2
        segs = piece.segments
        right = [self.offsetter.offset(s, +r) for s in segs]
        left = [self.offsetter.offset(s, -r) for s in reversed(segs)]
        left = [Cubic(c.p3, c.p2, c.p1, c.p0) for c in left]  # percorre de volta
        end_cap = CapBuilder.half_circle(segs[-1].p3, right[-1].p3, CubicGeometry.end_tangent(segs[-1]), r)
        start_cap = CapBuilder.half_circle(segs[0].p0, left[-1].p3, -CubicGeometry.start_tangent(segs[0]), r)
        contour = right + end_cap + left + start_cap
        return self._stitch(contour)

    @staticmethod
    def _stitch(contour: Contour) -> Contour:
        """Garante continuidade exata: cada segmento começa onde o anterior terminou."""
        out = [contour[0]]
        for c in contour[1:]:
            out.append(Cubic(out[-1].p3, c.p1, c.p2, c.p3))
        first = out[0]
        out[0] = Cubic(out[-1].p3, first.p1, first.p2, first.p3)
        return out
