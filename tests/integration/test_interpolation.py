"""Integração: os 3 masters de cada família têm a MESMA estrutura (interpoláveis)."""
from pathlib import Path

import pytest

from petricor.outline.composer import MasterGlyphSet
from petricor.outline.family import Families

ROOT = Path(__file__).resolve().parents[2]


def _structure(glyph):
    """Assinatura estrutural: nº de segmentos por contorno + componentes."""
    return ([len(c) for c in glyph.contours], [c.base for c in glyph.components])


@pytest.mark.parametrize("family", Families(ROOT / "sources" / "skeletons").all(), ids=lambda f: f.file_stem)
class TestMastersCompatibility:
    def test_todos_os_glifos_tem_estrutura_igual_nos_masters(self, family):
        skel = family.glyphs()
        built = [MasterGlyphSet().build(skel, p) for p in family.masters()]
        bad = [n for n in built[0] if len({repr(_structure(b[n])) for b in built}) > 1]
        assert not bad, f"Glifos incompatíveis entre Thin/Regular/Black: {bad[:15]}"
