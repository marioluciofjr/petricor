"""Acentos (marcas combinantes) no estilo do Mário + catálogo de letras acentuadas.

Convenção dos desenhos (coordenadas visuais):
- acento de CIMA: centrado em x = 0, borda de baixo em y = 0;
- acento de BAIXO: centrado em x = 0, borda de cima em y = 0.
A âncora do acento ('_top', '_bottom'...) fica em (0, 0); a da letra-base
fica onde o acento deve pousar. Assim, encaixar = alinhar as âncoras.
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass

import numpy as np
from fontTools.agl import UV2AGL

from ..model import Component, GlyphSkeleton, Stroke
from ..skeleton.store import SkeletonStore
from .skeleton_pen import Corner as K
from .skeleton_pen import HandJitter, SkeletonPen


@dataclass(frozen=True)
class MarkSpec:
    name: str
    unicode: int | None
    role: str               # 'top', 'bottom', 'ogonek', 'caron'
    recipe: list | None     # lista de traços (pontos); None = derivado de um glifo do Mário
    source: str | None = None
    size: float = 1.0       # escala aplicada ao glifo-fonte


MARKS = [
    MarkSpec("gravecomb", 0x0300, "top", [[(38, 0), (5, 62), (-38, 125)]]),
    MarkSpec("acutecomb", 0x0301, "top", [[(-38, 0), (-5, 62), (38, 125)]]),
    MarkSpec("circumflexcomb", 0x0302, "top", [[(-75, 0), K(0, 115), (75, 0)]]),
    MarkSpec("tildecomb", 0x0303, "top", None, "asciitilde", 0.62),
    MarkSpec("macroncomb", 0x0304, "top", [[(-85, 0), (0, 6), (85, 2)]]),
    MarkSpec("brevecomb", 0x0306, "top", [[(-70, 110), (-45, 25), (0, 0), (45, 25), (70, 110)]]),
    MarkSpec("dotaccentcomb", 0x0307, "top", [[(0, 0)]]),
    MarkSpec("dieresiscomb", 0x0308, "top", [[(-60, 0)], [(60, 0)]]),
    MarkSpec("ringcomb", 0x030A, "top", None, "degree", 1.2),
    MarkSpec("hungarumlautcomb", 0x030B, "top", [[(-75, 0), (-50, 60), (-28, 120)], [(15, 0), (40, 60), (62, 120)]]),
    MarkSpec("caroncomb", 0x030C, "top", [[(-75, 115), K(0, 0), (75, 115)]]),
    MarkSpec("commaaccentcomb", 0x0326, "bottom", None, "comma", 1.0),
    MarkSpec("cedillacomb", 0x0327, "bottom", [[(0, 0), (8, -45), (55, -75), (45, -125), (-25, -135)]]),
    MarkSpec("ogonekcomb", 0x0328, "ogonek", [[(0, 0), (-45, -55), (-30, -120), (30, -130)]]),
    MarkSpec("caroncomb.alt", None, "caron", None, "comma", 0.9),
    MarkSpec("commaturnedabovecomb", None, "top", None, "comma", 0.9),
]
MARK_NAMES = {m.name for m in MARKS}
MARK_ROLE = {m.name: m.role for m in MARKS}
TOP_MARKS = {0x0300, 0x0301, 0x0302, 0x0303, 0x0304, 0x0306, 0x0307, 0x0308, 0x030A, 0x030B, 0x030C}
COMB = {m.unicode: m.name for m in MARKS if m.unicode}


class MarkBuilder:
    """Constrói os esqueletos dos acentos (próprios ou derivados de glifos do Mário)."""

    def __init__(self, base: SkeletonStore, jitter: HandJitter | None = None):
        self.base = base
        self.jitter = jitter or HandJitter(amplitude=2.0)

    def build(self, spec: MarkSpec) -> GlyphSkeleton:
        strokes = self._from_recipe(spec) if spec.recipe else self._from_source(spec)
        return GlyphSkeleton(spec.name, [spec.unicode] if spec.unicode else [], strokes, advance=0.0,
                             anchors={"_" + spec.role: (0.0, 0.0)})

    def _from_recipe(self, spec):
        out = []
        for pts in spec.recipe:
            s = SkeletonPen.dot(pts[0]) if len(pts) == 1 else SkeletonPen.spline(pts)
            out.append(s if len(pts) == 1 else self.jitter.apply(s, spec.name))
        return out

    def _from_source(self, spec):
        src = self.base.load(spec.source)
        pts = np.vstack([s.sample(16) for s in src.strokes])
        cx = (pts[:, 0].min() + pts[:, 0].max()) / 2
        k = spec.size
        if spec.name == "commaturnedabovecomb":  # vírgula girada 180°, pousada em y = 0
            top = pts[:, 1].max()
            return [s.transformed(lambda p: (-(p[0] - cx) * k, (top - p[1]) * k)) for s in src.strokes]
        if spec.role in ("bottom",):  # topo em y = −40 (pequena folga sob a letra)
            top = pts[:, 1].max()
            return [s.transformed(lambda p: ((p[0] - cx) * k, (p[1] - top) * k - 40)) for s in src.strokes]
        if spec.role == "caron":  # apóstrofo: canto inferior esquerdo em (0, 0)
            x0, y0 = pts[:, 0].min(), pts[:, 1].min()
            return [s.transformed(lambda p: ((p[0] - x0) * k, (p[1] - y0) * k)) for s in src.strokes]
        bottom = pts[:, 1].min()
        return [s.transformed(lambda p: ((p[0] - cx) * k, (p[1] - bottom) * k)) for s in src.strokes]


class GlyphNamer:
    """Nomes de produção: AGL quando existe; senão uniXXXX."""

    SPECIAL = {0x0131: "idotless", 0x0237: "jdotless", 0x1E9E: "uni1E9E"}

    @classmethod
    def name(cls, u: int) -> str:
        if u in cls.SPECIAL:
            return cls.SPECIAL[u]
        if u in COMB:
            return COMB[u]
        return UV2AGL.get(u, f"uni{u:04X}")


class AccentCatalog:
    """Lista as letras acentuadas a montar, a partir da decomposição Unicode."""

    COMMA_INSTEAD_OF_CEDILLA = set("GKLNkln")
    CARON_AS_APOSTROPHE = set("dlLt")

    def composites(self, codepoints) -> list[GlyphSkeleton]:
        out = []
        for u in codepoints:
            d = unicodedata.decomposition(chr(u))
            if not d or d.startswith("<"):
                continue
            base_u, mark_u = (int(x, 16) for x in d.split())
            out.append(self._compose(u, chr(base_u), mark_u))
        return out

    def _compose(self, u: int, base: str, mark_u: int) -> GlyphSkeleton:
        mark, role = COMB[mark_u], MARK_ROLE[COMB[mark_u]]
        base_name = GlyphNamer.name(ord(base))
        if mark_u == 0x0327 and base == "g":
            mark, role = "commaturnedabovecomb", "top"
        elif mark_u == 0x0327 and base in self.COMMA_INSTEAD_OF_CEDILLA:
            mark, role = "commaaccentcomb", "bottom"
        elif mark_u == 0x030C and base in self.CARON_AS_APOSTROPHE:
            mark, role = "caroncomb.alt", "caron"
        if base == "i" and mark_u in TOP_MARKS:
            base_name = "idotless"
        return GlyphSkeleton(GlyphNamer.name(u), [u], components=[Component(base_name), Component(mark, anchor=role)])

    @staticmethod
    def dotless_iogonek() -> GlyphSkeleton:
        """'į' sem pingo: usado quando į recebe acento em cima (lituano)."""
        return GlyphSkeleton("iogonek.dotless", [], components=[Component("idotless"),
                                                               Component("ogonekcomb", anchor="ogonek")])

    @staticmethod
    def high_variants(composites: list[GlyphSkeleton], has_hi) -> list[GlyphSkeleton]:
        """Para a Caligrafia: 'aacute.hi' = 'a.hi' + acento (entrada pela junção alta)."""
        out = []
        for g in composites:
            base = g.components[0].base
            if has_hi(base + ".hi"):
                comps = [Component(base + ".hi")] + [Component(c.base, c.dx, c.dy, c.anchor) for c in g.components[1:]]
                out.append(GlyphSkeleton(g.name + ".hi", [], components=comps))
        return out


SPACING_MARKS = {  # sinais de acento soltos (com largura própria)
    0x0060: ("gravecomb", 520), 0x005E: ("circumflexcomb", 470), 0x00B4: ("acutecomb", 480),
    0x00A8: ("dieresiscomb", 490), 0x00AF: ("macroncomb", 500), 0x00B8: ("cedillacomb", 0),
    0x02C6: ("circumflexcomb", 480), 0x02C7: ("caroncomb", 480), 0x02D8: ("brevecomb", 480),
    0x02D9: ("dotaccentcomb", 490), 0x02DA: ("ringcomb", 480), 0x02DB: ("ogonekcomb", 0),
    0x02DC: ("tildecomb", 490), 0x02DD: ("hungarumlautcomb", 480),
}


class SpacingMarkBuilder:
    @staticmethod
    def build(u: int) -> GlyphSkeleton:
        mark, dy = SPACING_MARKS[u]
        return GlyphSkeleton(GlyphNamer.name(u), [u], advance=320.0, components=[Component(mark, 160, dy)])


def is_dot_stroke(stroke: Stroke) -> bool:
    return all(np.ptp(seg.as_array(), axis=0).max() < 0.5 for seg in stroke.segments)
