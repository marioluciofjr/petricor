"""Testes da caneta de esqueletos, das receitas e das famílias."""
import numpy as np
import pytest

from petricor.design import recipes as R
from petricor.design.letter_builder import TAN_LOW, CursiveBuilder
from petricor.design.skeleton_pen import Corner, HandJitter, SkeletonPen
from petricor.model import GlyphSkeleton
from petricor.outline.family import FamilySpec
from petricor.skeleton.store import SkeletonStore
from petricor.build.specimen import SimpleShaper


class TestSkeletonPen:
    def test_spline_passa_por_todos_os_pontos(self):
        pts = [(0, 0), (100, 80), (200, 0), (300, 90)]
        s = SkeletonPen.spline(pts)
        nodes = [s.segments[0].p0] + [seg.p3 for seg in s.segments]
        assert np.allclose(nodes, pts)

    def test_canto_quebra_a_tangente(self):
        s = SkeletonPen.spline([(0, 0), Corner(100, 200), (200, 0)])
        a, b = s.segments
        t_in = np.subtract(a.p3, a.p2)
        t_out = np.subtract(b.p1, b.p0)
        cos = t_in @ t_out / np.linalg.norm(t_in) / np.linalg.norm(t_out)
        assert cos < 0.5  # quina de verdade

    def test_spline_fechado_volta_ao_inicio(self):
        s = SkeletonPen.spline([(0, 0), (100, 0), (100, 100), (0, 100)], closed=True)
        assert s.closed and s.segments[-1].p3 == s.segments[0].p0

    def test_tremor_preserva_pontas_protegidas(self):
        s = SkeletonPen.spline([(0, 110), (200, 300), (400, 110)])
        j = HandJitter(amplitude=6).apply(s, "teste", protect=[(0, 110), (400, 110)])
        assert np.allclose(j.segments[0].p0, (0, 110))
        assert np.allclose(j.segments[-1].p3, (400, 110))

    def test_tremor_e_deterministico(self):
        s = SkeletonPen.spline([(0, 0), (200, 300), (400, 0)])
        a = HandJitter().apply(s, "n").nodes()
        b = HandJitter().apply(s, "n").nodes()
        assert a == b


class TestCursiveBuilder:
    @pytest.mark.parametrize("letter", list(R.CURSIVE))
    def test_entrada_e_saida_nas_alturas_padrao(self, letter):
        g = CursiveBuilder().build(letter)
        main = g.strokes[0]
        assert np.allclose(main.segments[0].p0, (0, R.JOIN_LOW), atol=0.01)
        exit_y = R.JOIN_HIGH if letter in R.HIGH_EXIT else R.JOIN_LOW
        assert main.segments[-1].p3[1] == pytest.approx(exit_y, abs=0.01)
        assert g.advance == pytest.approx(g.anchors["exit"][0])

    def test_entrada_baixa_sobe_a_35_graus(self):
        seg = CursiveBuilder().build("n").strokes[0].segments[0]
        t = np.subtract(seg.p1, seg.p0)
        assert np.allclose(t / np.linalg.norm(t), TAN_LOW, atol=0.02)

    def test_variante_hi_entra_pela_juncao_alta_e_sem_unicode(self):
        g = CursiveBuilder().build("a", high_entry=True)
        assert g.name == "a.hi" and g.unicodes == []
        assert g.strokes[0].segments[0].p0[1] == pytest.approx(R.JOIN_HIGH)


class TestFamilies:
    def test_camada_de_cima_sobrescreve_a_base(self, tmp_path):
        base, top = tmp_path / "base", tmp_path / "top"
        SkeletonStore(base).save(GlyphSkeleton("a", [97], advance=100))
        SkeletonStore(base).save(GlyphSkeleton("A", [65], advance=500))
        SkeletonStore(top).save(GlyphSkeleton("a", [97], advance=300))
        glyphs = FamilySpec("Teste", "Teste", (top, base)).glyphs()
        assert glyphs["a"].advance == 300 and glyphs["A"].advance == 500

    def test_shaper_usa_variante_hi_depois_de_saida_alta(self):
        shaper = SimpleShaper({"o": "o", "n": "n"}, {"o", "n", "n.hi"}, {"o"})
        assert shaper.shape("onn") == ["o", "n.hi", "n"]
