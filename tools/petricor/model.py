"""Tipos compartilhados por todas as etapas (o "vocabulário" do projeto).

Coordenadas:
- Na imagem (pixels), y cresce para BAIXO.
- Na fonte (unidades, UPM 1000), y cresce para CIMA e a linha de base é y = 0.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np

Point = tuple[float, float]
Transform = Callable[[Point], Point]


@dataclass(frozen=True)
class Cubic:
    """Segmento Bézier cúbico: começa em p0, termina em p3; p1/p2 'puxam' a curva."""

    p0: Point
    p1: Point
    p2: Point
    p3: Point

    def as_array(self) -> np.ndarray:
        return np.array([self.p0, self.p1, self.p2, self.p3], float)

    def point(self, t: float) -> np.ndarray:
        p = self.as_array()
        mt = 1 - t
        return mt ** 3 * p[0] + 3 * mt ** 2 * t * p[1] + 3 * mt * t ** 2 * p[2] + t ** 3 * p[3]

    def derivative(self, t: float) -> np.ndarray:
        p = self.as_array()
        mt = 1 - t
        return 3 * mt ** 2 * (p[1] - p[0]) + 6 * mt * t * (p[2] - p[1]) + 3 * t ** 2 * (p[3] - p[2])

    def split(self, t: float) -> tuple["Cubic", "Cubic"]:
        """Divide a curva em duas no parâmetro t (algoritmo de De Casteljau)."""
        p = self.as_array()
        a = p[:-1] + t * (p[1:] - p[:-1])
        b = a[:-1] + t * (a[1:] - a[:-1])
        c = b[0] + t * (b[1] - b[0])
        left = Cubic(tuple(p[0]), tuple(a[0]), tuple(b[0]), tuple(c))
        right = Cubic(tuple(c), tuple(b[1]), tuple(a[2]), tuple(p[3]))
        return left, right

    def transformed(self, fn: Transform) -> "Cubic":
        return Cubic(fn(self.p0), fn(self.p1), fn(self.p2), fn(self.p3))

    def sample(self, n: int = 16) -> np.ndarray:
        return np.array([self.point(t) for t in np.linspace(0, 1, n)])


@dataclass
class Stroke:
    """Um traço de caneta: segmentos cúbicos encadeados (fim de um = início do próximo)."""

    segments: list[Cubic]
    closed: bool = False

    def nodes(self) -> list[Point]:
        """Lista plana: p0, (p1, p2, p3) por segmento — formato do JSON."""
        out = [self.segments[0].p0]
        for s in self.segments:
            out += [s.p1, s.p2, s.p3]
        return out

    @classmethod
    def from_nodes(cls, nodes: list[Point], closed: bool = False) -> "Stroke":
        if (len(nodes) - 1) % 3:
            raise ValueError("Um traço precisa de 1 + 3n pontos")
        pts = [tuple(map(float, p)) for p in nodes]
        segs = [Cubic(pts[i], pts[i + 1], pts[i + 2], pts[i + 3]) for i in range(0, len(pts) - 1, 3)]
        return cls(segs, closed)

    def transformed(self, fn: Transform) -> "Stroke":
        return Stroke([s.transformed(fn) for s in self.segments], self.closed)

    def sample(self, n_per_segment: int = 16) -> np.ndarray:
        return np.vstack([s.sample(n_per_segment) for s in self.segments])


@dataclass
class Component:
    """Referência a outro glifo (usada em compostos, ex.: 'ã' = 'a' + 'tildecomb').

    anchor = papel do componente na montagem:
      None      → posição fixa (dx, dy)
      'top', 'bottom', 'ogonek', 'caron' → encaixa o acento na âncora da base
      'after'   → vem logo depois do componente anterior (æ = a + e); dx = sobreposição
    """

    base: str
    dx: float = 0.0
    dy: float = 0.0
    anchor: str | None = None


@dataclass
class GlyphSkeleton:
    """Esqueleto de um glifo: a fonte da verdade do desenho."""

    name: str
    unicodes: list[int] = field(default_factory=list)
    strokes: list[Stroke] = field(default_factory=list)
    advance: float = 0.0
    anchors: dict[str, Point] = field(default_factory=dict)
    components: list[Component] = field(default_factory=list)
    locked: bool = False  # True = editado à mão; etapas automáticas não sobrescrevem

    def bounds(self) -> tuple[float, float, float, float] | None:
        """(xmin, ymin, xmax, ymax) da linha central (sem espessura)."""
        if not self.strokes:
            return None
        pts = np.vstack([s.sample(24) for s in self.strokes])
        return float(pts[:, 0].min()), float(pts[:, 1].min()), float(pts[:, 0].max()), float(pts[:, 1].max())

    def transformed(self, fn: Transform) -> "GlyphSkeleton":
        return GlyphSkeleton(self.name, list(self.unicodes), [s.transformed(fn) for s in self.strokes],
                             self.advance, {k: fn(v) for k, v in self.anchors.items()},
                             list(self.components), self.locked)
