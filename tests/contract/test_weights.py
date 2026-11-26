"""Contrato dos pesos: Petricor 100–900 (9 instâncias); Caligrafia 100–600 (6 instâncias)."""
from pathlib import Path

from petricor.outline.family import Families

FAMILIES = Families(Path(__file__).resolve().parents[2] / "sources" / "skeletons")


class TestWeightRanges:
    def test_petricor_tem_nove_pesos(self):
        fam = FAMILIES.petricor()
        assert [p.wght for p in fam.instances()] == list(range(100, 1000, 100))
        assert [p.name for p in fam.masters()] == ["Thin", "Regular", "Black"]

    def test_caligrafia_vai_ate_o_semibold(self):
        fam = FAMILIES.caligrafia()
        assert [p.wght for p in fam.instances()] == list(range(100, 700, 100))
        assert [p.name for p in fam.masters()] == ["Thin", "Regular", "SemiBold"]

    def test_eixo_sempre_inclui_o_regular_400(self):
        for fam in FAMILIES.all():
            assert 400 in [p.wght for p in fam.instances()]
