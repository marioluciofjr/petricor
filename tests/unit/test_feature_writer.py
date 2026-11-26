"""Testes das regras OpenType geradas (calt, ccmp, tnum)."""
from petricor.outline.feature_writer import FeatureWriter


class TestFeatureWriter:
    NAMES = {"o", "n", "n.hi", "a", "a.hi", "i", "idotless", "acutecomb", "zero", "zero.tf", "one", "one.tf"}

    def test_calt_troca_pela_variante_hi_depois_de_saida_alta(self):
        fea = FeatureWriter(self.NAMES, {"o"}).write()
        assert "@HighExit = [o];" in fea
        assert "@LowEntry = [a n];" in fea and "@HighEntry = [a.hi n.hi];" in fea
        assert "sub @HighExit @LowEntry' by @HighEntry;" in fea

    def test_sem_variantes_hi_nao_gera_calt(self):
        fea = FeatureWriter({"o", "n"}, {"o"}).write()
        assert "feature calt" not in fea

    def test_ccmp_tira_o_pingo_do_i_acentuado(self):
        fea = FeatureWriter(self.NAMES, set()).write()
        assert "sub [i]' @TopMarks by [idotless];" in fea

    def test_tnum_mapeia_algarismos(self):
        fea = FeatureWriter(self.NAMES, set()).write()
        assert "sub [zero one] by [zero.tf one.tf];" in fea
