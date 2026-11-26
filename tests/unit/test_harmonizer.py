"""Testes da harmonização leve."""
import numpy as np
import pytest

from petricor.design.harmonizer import Extent, Harmonizer
from petricor.design.metrics import DEFAULT_METRICS as M
from petricor.model import Cubic, GlyphSkeleton, Stroke


class Glyphs:
    """Glifos sintéticos com tamanhos 'tortos', como na escrita à mão."""

    @staticmethod
    def line(x0, y0, x1, y1):
        return Stroke([Cubic((x0, y0), (x0 + (x1 - x0) / 3, y0 + (y1 - y0) / 3),
                             (x0 + 2 * (x1 - x0) / 3, y0 + 2 * (y1 - y0) / 3), (x1, y1))])

    @classmethod
    def make(cls, name, lo, hi, x=100):
        return GlyphSkeleton(name, [], [cls.line(x, lo, x, hi), cls.line(x, hi, x + 200, lo)])


class TestHarmonizer:
    @pytest.mark.parametrize("case", [
        ("H", 18, 660, 0, M.cap_height),
        ("n", 27, 300, 0, M.x_height),
        ("l", 40, 690, 0, M.ascender),
        ("p", -190, 360, M.descender, M.x_height),
        ("seven", 76, 700, 0, M.digit_height),
    ])
    def test_cada_classe_cai_nas_linhas_alvo(self, case):
        name, lo, hi, t_lo, t_hi = case  # (glifo, base medida, topo medido, base alvo, topo alvo)
        g = Glyphs.make(name, lo, hi)
        out = Harmonizer().harmonize(g, {})
        e = Extent.of(out.strokes)
        assert e.lo == pytest.approx(t_lo, abs=1)
        assert e.hi == pytest.approx(t_hi, abs=1)

    def test_glifo_comeca_em_x_zero(self):
        out = Harmonizer().harmonize(Glyphs.make("H", 18, 660, x=350), {})
        assert Extent.of(out.strokes).xmin == pytest.approx(0, abs=0.5)

    def test_largura_acompanha_so_metade_da_correcao_individual(self):
        h = Harmonizer()
        g = Glyphs.make("n", 0, 215)  # metade da altura-x: precisa dobrar na vertical
        out = h.harmonize(g, {h.classifier.rule_for("n"): 1.0})
        width = out.bounds()[2] - out.bounds()[0]
        assert width == pytest.approx(200 * np.sqrt(2), rel=0.02)

    def test_pingo_do_i_nao_entra_na_medicao(self):
        g = GlyphSkeleton("i", [], [Glyphs.line(100, 20, 100, 300), Glyphs.line(100, 420, 104, 430)])
        out = Harmonizer().harmonize(g, {})
        stem = Extent.of(out.strokes[:1])
        assert stem.hi == pytest.approx(M.x_height, abs=1)
        assert Extent.of(out.strokes[1:]).lo > M.x_height  # pingo continua acima

    def test_barra_do_5_conta_na_altura(self):
        # a bandeira do 5 é um traço separado no topo, mas é longa: não é pingo
        g = GlyphSkeleton("five", [], [Glyphs.line(100, 76, 100, 560), Glyphs.line(100, 600, 300, 610)])
        out = Harmonizer().harmonize(g, {})
        assert Extent.of(out.strokes).hi == pytest.approx(M.digit_height, abs=1)

    def test_pontuacao_so_desloca_sem_mudar_tamanho(self):
        g = Glyphs.make("period", 30, 60)
        out = Harmonizer().harmonize(g, {})
        e = Extent.of(out.strokes)
        assert e.lo == pytest.approx(0, abs=0.5) and e.hi - e.lo == pytest.approx(30, abs=0.5)
