"""Testes do kerning óptico automático."""
from petricor.design.kerner import Kerner, KerningGroups
from petricor.model import Component, Cubic
from petricor.outline.glyph_factory import OutlineGlyph


class Shapes:
    """Glifos-caixa simples: retângulos e um 'V' (largo em cima, estreito embaixo)."""

    @staticmethod
    def rect(x0, y0, x1, y1):
        pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        return [Cubic(a, a, b, b) for a, b in zip(pts, pts[1:] + pts[:1])]

    @classmethod
    def glyphs(cls):
        H = OutlineGlyph("H", [72], [cls.rect(50, 0, 100, 700), cls.rect(300, 0, 350, 700)], 400)
        V = OutlineGlyph("V", [86], [cls.rect(50, 600, 450, 700), cls.rect(220, 0, 280, 600)], 500)
        A = OutlineGlyph("A", [65], [cls.rect(220, 600, 280, 700), cls.rect(50, 0, 450, 100)], 500)
        Aacute = OutlineGlyph("Aacute", [193], [], 500, [Component("A")])
        return {"H": H, "V": V, "A": A, "Aacute": Aacute}


class TestKerner:
    def test_par_reto_nao_recebe_kerning(self):
        k = Kerner(Shapes.glyphs())
        assert k.kern_table(["H"], ["H"]) == {}

    def test_av_e_aproximado(self):
        table = Kerner(Shapes.glyphs()).kern_table(["A"], ["V"])
        assert table[("A", "V")] < 0

    def test_grupos_incluem_os_acentuados(self):
        groups, _ = KerningGroups.build(Shapes.glyphs(), ["A"])
        assert groups["public.kern1.A"] == ["A", "Aacute"]
