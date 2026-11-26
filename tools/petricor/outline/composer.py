"""Montagem de compostos (á = a + ´) e conjunto completo de glifos de um peso."""
from __future__ import annotations

from ..model import Component, GlyphSkeleton
from .glyph_factory import OutlineGlyph, OutlineGlyphFactory
from .weight_profile import WeightProfile

DIGITS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]


class Composer:
    """Resolve as posições dos componentes alinhando âncoras (base ↔ acento)."""

    @staticmethod
    def resolve(skel: GlyphSkeleton, built: dict[str, OutlineGlyph]) -> OutlineGlyph:
        comps: list[Component] = []
        first = built[skel.components[0].base]
        x_cursor, last = 0.0, first
        comps.append(Component(first.name, 0.0, 0.0))
        for c in skel.components[1:]:
            g = built[c.base]
            if c.anchor == "after":  # ligadura: começa onde o anterior termina (menos a sobreposição)
                x_cursor += last.advance - c.dx
                comps.append(Component(g.name, x_cursor, 0.0))
                last = g
            elif c.anchor:
                bx, by = first.anchors[c.anchor]
                mx, my = g.anchors["_" + c.anchor]
                comps.append(Component(g.name, bx - mx, by - my))
            else:
                comps.append(Component(g.name, c.dx, c.dy))
        if any(c.anchor == "after" for c in skel.components):
            advance = x_cursor + last.advance
        else:
            advance = skel.advance or first.advance
        return OutlineGlyph(skel.name, list(skel.unicodes), [], advance, comps, dict(first.anchors))


class MasterGlyphSet:
    """Todos os glifos de uma família num peso: simples → compostos → algarismos tabulares."""

    def __init__(self, factory: OutlineGlyphFactory | None = None, composer: Composer | None = None):
        self.factory = factory or OutlineGlyphFactory()
        self.composer = composer or Composer()

    def build(self, glyphs: dict[str, GlyphSkeleton], prof: WeightProfile) -> dict[str, OutlineGlyph]:
        built = {n: self.factory.build(g, prof) for n, g in glyphs.items() if not g.components}
        pending = {n: g for n, g in glyphs.items() if g.components}
        while pending:
            ready = [n for n, g in pending.items() if all(c.base in built for c in g.components)]
            if not ready:
                raise ValueError(f"Componentes ausentes em: {sorted(pending)[:10]}")
            for n in ready:
                built[n] = self.composer.resolve(pending.pop(n), built)
        built.update(self._tabular(built))
        return built

    @staticmethod
    def _tabular(built: dict[str, OutlineGlyph]) -> dict[str, OutlineGlyph]:
        """Algarismos tabulares (tnum): mesma largura para todos, centralizados."""
        width = max(built[d].advance for d in DIGITS if d in built)
        return {f"{d}.tf": OutlineGlyph(f"{d}.tf", [], [], width, [Component(d, (width - built[d].advance) / 2, 0.0)])
                for d in DIGITS if d in built}
