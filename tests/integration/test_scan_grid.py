"""Integração: encontrar as 49 células nas folhas reais digitalizadas."""
from pathlib import Path

import numpy as np
import pytest

from petricor.scan.grid import GridSlicer
from petricor.scan.loader import SheetLoader

SCANS = Path(__file__).resolve().parents[2] / "sources" / "scans"


@pytest.mark.parametrize("name", ["maiusculas.jpeg", "minusculas.jpeg"])
class TestGridSlicerOnRealScans:
    def test_grade_ajustada_tem_49_celulas_regulares(self, name):
        cells = GridSlicer().slice(SheetLoader.load(SCANS / name))
        assert len(cells) == 49
        xs = np.array([[cells[(r, c)].x for c in range(7)] for r in range(7)])
        pitch = np.diff(xs, axis=1)
        assert np.all(np.abs(pitch - pitch.mean()) < 6)

    def test_cada_celula_tem_linha_de_base_dentro_dela(self, name):
        for cell in GridSlicer().slice(SheetLoader.load(SCANS / name)).values():
            assert 0.6 * cell.h < cell.baseline < 0.85 * cell.h
