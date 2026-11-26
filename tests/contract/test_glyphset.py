"""Contrato com o Google Fonts: cobertura do GF Latin Core nas duas famílias."""
from pathlib import Path

import glyphsets
import pytest

from petricor.outline.family import Families

ROOT = Path(__file__).resolve().parents[2]
FAMILIES = Families(ROOT / "sources" / "skeletons")


@pytest.mark.parametrize("family", FAMILIES.all(), ids=lambda f: f.file_stem)
class TestGlyphSetContract:
    def test_cobre_100_por_cento_do_gf_latin_core(self, family):
        have = {u for g in family.glyphs().values() for u in g.unicodes}
        core = set(glyphsets.unicodes_per_glyphset("GF_Latin_Core"))
        missing = sorted(core - have)
        assert not missing, "Faltam: " + " ".join(f"U+{u:04X}" for u in missing)

    def test_nenhum_unicode_duplicado(self, family):
        seen = {}
        for g in family.glyphs().values():
            for u in g.unicodes:
                assert u not in seen, f"U+{u:04X} em {g.name} e {seen[u]}"
                seen[u] = g.name

    def test_componentes_apontam_para_glifos_existentes(self, family):
        glyphs = family.glyphs()
        for g in glyphs.values():
            for c in g.components:
                assert c.base in glyphs, f"{g.name} usa {c.base}, que não existe"
