"""Testes da etapa skeleton: afinamento, grafo de traços, ajuste Bézier e JSON."""
import cv2
import numpy as np

from petricor.model import Cubic, GlyphSkeleton, Stroke
from petricor.skeleton.fitter import BezierFitter, CornerDetector
from petricor.skeleton.skeletonizer import Skeletonizer
from petricor.skeleton.store import SkeletonStore
from petricor.skeleton.tracer import PixelPath, StrokeTracer


class Shapes:
    """Fábrica de máscaras sintéticas desenhadas com 'caneta' de 7 px."""

    PEN = 7

    @classmethod
    def canvas(cls):
        return np.zeros((240, 240), np.uint8)

    @classmethod
    def line(cls, pts):
        m = cls.canvas()
        for a, b in zip(pts[:-1], pts[1:]):
            cv2.line(m, a, b, 1, cls.PEN)
        return m.astype(bool)

    @classmethod
    def ring(cls):
        m = cls.canvas()
        cv2.circle(m, (120, 120), 70, 1, cls.PEN)
        return m.astype(bool)

    @classmethod
    def trace(cls, mask):
        res = Skeletonizer().run(mask)
        return StrokeTracer().trace(res.skeleton, res.stroke_width), res


class TestSkeletonizer:
    def test_mede_a_espessura_da_caneta(self):
        mask = Shapes.line([(20, 120), (220, 120)])
        real_width = mask[:, 120].sum()  # o OpenCV desenha um pouco mais grosso que PEN
        res = Skeletonizer().run(mask)
        assert abs(res.stroke_width - real_width) <= 1

    def test_esqueleto_tem_um_pixel_de_largura(self):
        res = Skeletonizer().run(Shapes.line([(20, 120), (220, 120)]))
        assert res.skeleton[:, 120].sum() <= 1


class TestStrokeTracer:
    def test_linha_simples_vira_um_traco(self):
        paths, _ = Shapes.trace(Shapes.line([(20, 120), (220, 120)]))
        assert len(paths) == 1
        assert paths[0].length() > 180

    def test_x_vira_duas_diagonais_que_se_cruzam(self):
        m = Shapes.line([(30, 30), (210, 210)]) | Shapes.line([(210, 30), (30, 210)])
        paths, _ = Shapes.trace(m)
        assert len(paths) == 2
        assert all(p.length() > 200 for p in paths)

    def test_t_tem_barra_inteira_e_haste_separada(self):
        m = Shapes.line([(30, 40), (210, 40)]) | Shapes.line([(120, 40), (120, 220)])
        paths, _ = Shapes.trace(m)
        lengths = sorted(p.length() for p in paths)
        assert len(paths) == 2
        assert lengths[-1] > 160  # barra atravessa o cruzamento

    def test_anel_vira_traco_fechado(self):
        paths, _ = Shapes.trace(Shapes.ring())
        assert len(paths) == 1 and paths[0].closed


class TestBezierFitter:
    def test_arco_e_ajustado_dentro_da_tolerancia(self):
        t = np.linspace(0, np.pi / 2, 120)
        pts = np.column_stack([100 * np.cos(t), 100 * np.sin(t)])
        stroke = BezierFitter(tolerance=1.0, smooth_sigma=0.5).fit(PixelPath(pts))
        sampled = stroke.sample(64)
        err = np.abs(np.hypot(sampled[:, 0], sampled[:, 1]) - 100).max()
        assert err < 1.5

    def test_v_e_dividido_no_vertice(self):
        a = np.column_stack([np.linspace(0, 60, 61), np.linspace(0, 120, 61)])
        b = np.column_stack([np.linspace(60, 120, 61), np.linspace(120, 0, 61)])
        pts = np.vstack([a, b[1:]])
        assert len(CornerDetector().find(pts, closed=False)) == 1
        stroke = BezierFitter().fit(PixelPath(pts))
        joints = [np.array(s.p0) for s in stroke.segments[1:]]
        assert any(np.linalg.norm(j - [60, 120]) < 4 for j in joints)

    def test_anel_fechado_termina_onde_comeca(self):
        paths, _ = Shapes.trace(Shapes.ring())
        stroke = BezierFitter().fit(paths[0])
        assert stroke.closed
        assert np.allclose(stroke.segments[0].p0, stroke.segments[-1].p3, atol=1e-6)


class TestSkeletonStore:
    def test_ida_e_volta_pelo_json_preserva_o_glifo(self, tmp_path):
        g = GlyphSkeleton("A", [65], [Stroke([Cubic((0, 0), (10, 50), (20, 50), (30, 0))])],
                          advance=400, anchors={"top": (15, 700)})
        store = SkeletonStore(tmp_path)
        store.save(g)
        back = store.load("A")
        assert back.name == "A" and back.unicodes == [65]
        assert back.strokes[0].nodes() == [(0, 0), (10, 50), (20, 50), (30, 0)]
        assert back.anchors["top"] == (15, 700)

    def test_maiuscula_e_minuscula_nao_colidem_no_windows(self, tmp_path):
        store = SkeletonStore(tmp_path)
        assert store.path_for("A").name != store.path_for("a").name.upper()
        assert store.path_for("A").name.lower() != store.path_for("a").name.lower()
