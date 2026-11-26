"""Kerning óptico automático (ajuste de espaço entre pares específicos).

Para cada glifo calculamos um PERFIL: em faixas horizontais de 20 un,
onde fica a tinta mais à esquerda e mais à direita. Num par L+R, a
distância em cada faixa é (avanço de L − borda direita de L) + borda
esquerda de R. Se a média dessas distâncias for maior que a de um par
de referência ('HH' ou 'nn'), aproximamos (kerning negativo).

Grupos: os acentuados herdam o kerning da letra-base ('Á' usa o de 'A').
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

BAND = 20
Y_RANGE = (-250, 800)


@dataclass
class Profile:
    left: np.ndarray    # x mínimo de tinta por faixa (nan = sem tinta)
    right: np.ndarray   # x máximo de tinta por faixa
    advance: float


class ProfileBuilder:
    """Calcula perfis a partir dos OutlineGlyph (resolvendo componentes)."""

    def __init__(self, glyphs: dict):
        self.glyphs = glyphs
        self.edges = np.arange(Y_RANGE[0], Y_RANGE[1] + BAND, BAND)
        self.cache: dict[str, Profile] = {}

    def points(self, name: str, dx: float = 0.0, dy: float = 0.0) -> list[np.ndarray]:
        g = self.glyphs[name]
        out = [np.vstack([c.sample(12) for c in cont]) + [dx, dy] for cont in g.contours]
        for comp in g.components:
            out += self.points(comp.base, dx + comp.dx, dy + comp.dy)
        return out

    def get(self, name: str) -> Profile:
        if name not in self.cache:
            n = len(self.edges) - 1
            left, right = np.full(n, np.nan), np.full(n, np.nan)
            pts = self.points(name)
            if pts:
                p = np.vstack(pts)
                idx = np.clip(np.digitize(p[:, 1], self.edges) - 1, 0, n - 1)
                for i in np.unique(idx):
                    xs = p[idx == i, 0]
                    left[i], right[i] = xs.min(), xs.max()
            self.cache[name] = Profile(left, right, self.glyphs[name].advance)
        return self.cache[name]


class Kerner:
    STRENGTH = 0.6       # quanto da diferença para a referência é corrigida
    MIN_KERN = -130
    THRESHOLD = 15       # ignora ajustes pequenos (ruído)

    def __init__(self, glyphs: dict):
        self.profiles = ProfileBuilder(glyphs)

    def gap(self, left: str, right: str) -> float | None:
        L, R = self.profiles.get(left), self.profiles.get(right)
        d = (L.advance - L.right) + R.left
        both = ~np.isnan(d)
        if not both.any():
            return None
        return float(np.mean(np.sort(d[both])[: max(3, both.sum() // 2)]))  # metade mais próxima

    def pair(self, left: str, right: str, reference: float) -> int:
        g = self.gap(left, right)
        if g is None:
            return 0
        k = int(round(max(self.MIN_KERN, min(0.0, (reference - g) * self.STRENGTH))))
        return k if k <= -self.THRESHOLD else 0

    def kern_table(self, lefts: list[str], rights: list[str], reference_pair=("H", "H")) -> dict:
        ref = self.gap(*reference_pair) or 110.0
        table = {}
        for a in lefts:
            for b in rights:
                k = self.pair(a, b, ref)
                if k:
                    table[(a, b)] = k
        return table


class KerningGroups:
    """Grupos 'public.kern1/2': cada letra-base com seus acentuados."""

    @staticmethod
    def build(glyphs: dict, bases: list[str]) -> tuple[dict, dict]:
        members = {b: [b] for b in bases if b in glyphs}
        for name, g in glyphs.items():
            if g.components and not name.endswith((".hi", ".tf")):
                base = g.components[0].base
                if base in members and name not in members[base]:
                    members[base].append(name)
        groups = {}
        for b, names in members.items():
            groups[f"public.kern1.{b}"] = sorted(names)
            groups[f"public.kern2.{b}"] = sorted(names)
        return groups, {b: (f"public.kern1.{b}", f"public.kern2.{b}") for b in members}
