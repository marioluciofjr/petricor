"""Testes da expansão do traço (espessura monolinear e compatibilidade entre pesos)."""
import numpy as np
import pytest

from petricor.model import Cubic, Stroke
from petricor.outline.stroke_expander import CapBuilder, StrokeExpander


class Geometry:
    """Utilidades de medição sobre contornos."""

    @staticmethod
    def polygon(contour, n=24):
        return np.vstack([c.sample(n)[:-1] for c in contour])

    @classmethod
    def signed_area(cls, contour):
        p = cls.polygon(contour)
        x, y = p[:, 0], p[:, 1]
        return 0.5 * float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))

    @staticmethod
    def hline(x0=0, x1=300, y=100):
        return Stroke([Cubic((x0, y), (x0 + (x1 - x0) / 3, y), (x0 + 2 * (x1 - x0) / 3, y), (x1, y))])

    @staticmethod
    def arc(r=200, start=0.0, end=np.pi):
        """Semicírculo aproximado por 2 cúbicas (traço curvo)."""
        segs = []
        for a, b in [(start, (start + end) / 2), ((start + end) / 2, end)]:
            k = 4 / 3 * np.tan((b - a) / 4) * r
            p0 = np.array([np.cos(a), np.sin(a)]) * r
            p3 = np.array([np.cos(b), np.sin(b)]) * r
            p1 = p0 + k * np.array([-np.sin(a), np.cos(a)])
            p2 = p3 - k * np.array([-np.sin(b), np.cos(b)])
            segs.append(Cubic(tuple(p0), tuple(p1), tuple(p2), tuple(p3)))
        return Stroke(segs)


class TestStrokeExpander:
    def test_linha_reta_vira_capsula_com_a_espessura_certa(self):
        contour = StrokeExpander(max_pen=180).expand(Geometry.hline(), pen=60)[0]
        p = Geometry.polygon(contour)
        assert p[:, 1].max() == pytest.approx(130, abs=0.5)
        assert p[:, 1].min() == pytest.approx(70, abs=0.5)
        assert p[:, 0].min() == pytest.approx(-30, abs=0.5)  # ponta redonda
        assert p[:, 0].max() == pytest.approx(330, abs=0.5)

    def test_contorno_externo_e_anti_horario(self):
        for stroke in (Geometry.hline(), Geometry.arc()):
            for c in StrokeExpander(max_pen=180).expand(stroke, pen=60):
                assert Geometry.signed_area(c) > 0

    def test_arco_mantem_espessura_constante(self):
        contour = StrokeExpander(max_pen=180).expand(Geometry.arc(r=200), pen=80)
        p = np.vstack([Geometry.polygon(c) for c in contour])
        rr = np.hypot(p[:, 0], p[:, 1])
        ring = rr[(p[:, 1] > 30)]  # longe das pontas
        assert ring.max() == pytest.approx(240, abs=3)
        assert ring.min() == pytest.approx(160, abs=3)

    @pytest.mark.parametrize("stroke", [Geometry.hline(), Geometry.arc(), Geometry.arc(r=40)])
    def test_estrutura_identica_em_todos_os_pesos(self, stroke):
        ex = StrokeExpander(max_pen=180)
        shapes = [[len(c) for c in ex.expand(stroke, pen=w)] for w in (16, 64, 180)]
        assert shapes[0] == shapes[1] == shapes[2]

    def test_ponto_vira_circulo(self):
        dot = Stroke([Cubic((50, 50), (50, 50), (50, 50), (50, 50))])
        contour = StrokeExpander(max_pen=180).expand(dot, pen=60, dot_pen=90)[0]
        p = Geometry.polygon(contour)
        assert np.hypot(p[:, 0] - 50, p[:, 1] - 50).max() == pytest.approx(45, abs=0.5)

    def test_contorno_e_continuo(self):
        for c in StrokeExpander(max_pen=180).expand(Geometry.arc(), pen=60):
            for a, b in zip(c, c[1:] + c[:1]):
                assert a.p3 == b.p0

    def test_curva_mais_fechada_que_o_black_e_dividida(self):
        ex = StrokeExpander(max_pen=180)
        assert len(ex.pieces(Geometry.arc(r=40))) > 1  # raio 40 < 90 (meia caneta do Black)
        assert len(ex.pieces(Geometry.arc(r=200))) == 1

    def test_alca_minuscula_nao_gera_espora(self):
        # caso real do 'E': segmento que termina com alça de ~2 unidades
        seg = Stroke([Cubic((371, 699), (354, 704), (18, 689), (16, 688)),
                      Cubic((16, 688), (3, 666), (13, 573), (13, 543))])
        for c in StrokeExpander(max_pen=150).expand(seg, pen=60):
            p = Geometry.polygon(c)
            assert p[:, 1].max() < 704 + 31  # nada sobe além do traço + meia caneta
            assert p[:, 0].max() < 371 + 31

    def test_circulo_tem_quatro_arcos(self):
        assert len(CapBuilder.circle((0, 0), 10)) == 4
