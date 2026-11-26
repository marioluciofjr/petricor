"""Integração: vetorização das folhas reais gera esqueletos plausíveis."""
from pathlib import Path

import pytest

from petricor.skeleton.sheet_tracer import SheetTracer

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def traced(tmp_path_factory):
    out = tmp_path_factory.mktemp("raw")
    report = SheetTracer(ROOT / "sources" / "scans", out).run()
    return report, out


class TestSheetTracer:
    def test_vetoriza_os_98_caracteres(self, traced):
        report, out = traced
        assert len(report["glyphs"]) == 98
        assert len(list(out.glob("*.json"))) == 98

    def test_escala_coloca_maiusculas_em_700_unidades(self, traced):
        report, _ = traced
        assert 3.0 < report["scale"] < 5.5

    def test_todo_glifo_tem_ao_menos_um_traco(self, traced):
        report, _ = traced
        assert all(g["strokes"] >= 1 for g in report["glyphs"].values())

    def test_i_tem_pingo_separado_acima_da_haste(self, traced):
        from petricor.skeleton.store import SkeletonStore
        _, out = traced
        strokes = SkeletonStore(out).load("i").strokes
        tops = sorted((s.sample(8)[:, 1].min(), s.sample(8)[:, 1].max()) for s in strokes)
        dot_bottom = tops[-1][0]
        assert all(top < dot_bottom for _, top in tops[:-1])

    def test_dois_pontos_tem_dois_tracos(self, traced):
        report, _ = traced
        assert report["glyphs"]["colon"]["strokes"] == 2
