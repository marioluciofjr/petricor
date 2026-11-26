"""Testes da montagem de acentos (catálogo, âncoras e compostos)."""
import pytest

from petricor.design.accents import AccentCatalog
from petricor.model import Component, Cubic, GlyphSkeleton, Stroke
from petricor.outline.composer import Composer, MasterGlyphSet
from petricor.outline.glyph_factory import OutlineGlyph
from petricor.outline.weight_profile import profile


class TestAccentCatalog:
    @pytest.mark.parametrize("case", [
        (0xE3, "atilde", "a", "tildecomb", "top"),
        (0xED, "iacute", "idotless", "acutecomb", "top"),       # í usa o i sem pingo
        (0x137, "uni0137", "k", "commaaccentcomb", "bottom"),     # ķ: vírgula, não cedilha
        (0x10F, "dcaron", "d", "caroncomb.alt", "caron"),         # ď: apóstrofo à direita
        (0xE7, "ccedilla", "c", "cedillacomb", "bottom"),
    ])
    def test_decomposicao_e_convencoes(self, case):
        u, name, base, mark, role = case
        g = AccentCatalog().composites([u])[0]
        assert g.unicodes == [u]
        assert [c.base for c in g.components] == [base, mark]
        assert g.components[1].anchor == role

    def test_variante_hi_so_quando_a_base_tem_hi(self):
        comps = AccentCatalog().composites([0xE1, 0xC1])  # á, Á
        hi = AccentCatalog.high_variants(comps, has_hi=lambda n: n == "a.hi")
        assert [g.name for g in hi] == ["aacute.hi"]


class TestComposer:
    def test_acento_alinha_ancoras(self):
        base = OutlineGlyph("a", [97], [], 400, anchors={"top": (200, 495)})
        mark = OutlineGlyph("acutecomb", [], [], 0, anchors={"_top": (0, 0)})
        skel = GlyphSkeleton("aacute", [0xE1], components=[Component("a"), Component("acutecomb", anchor="top")])
        out = Composer.resolve(skel, {"a": base, "acutecomb": mark})
        assert (out.components[1].dx, out.components[1].dy) == (200, 495)
        assert out.advance == 400

    def test_ligadura_coloca_o_segundo_depois_do_primeiro(self):
        a = OutlineGlyph("a", [], [], 400)
        e = OutlineGlyph("e", [], [], 380)
        skel = GlyphSkeleton("ae", [0xE6], components=[Component("a"), Component("e", 90, 0, "after")])
        out = Composer.resolve(skel, {"a": a, "e": e})
        assert out.components[1].dx == 310 and out.advance == 690

    def test_algarismos_tabulares_tem_largura_igual(self):
        line = Stroke([Cubic((0, 0), (0, 200), (0, 400), (0, 680))])
        glyphs = {n: GlyphSkeleton(n, [], [line if n != "one" else line]) for n in
                  ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]}
        built = MasterGlyphSet().build(glyphs, profile("Regular"))
        widths = {built[f"{d}.tf"].advance for d in glyphs}
        assert len(widths) == 1
