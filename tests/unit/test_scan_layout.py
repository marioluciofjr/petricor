"""Testes do mapa célula → caractere das folhas do fontmaker.co."""
from petricor.scan.layout import SheetLayout


class TestSheetLayout:
    """Garante que a ordem dos caracteres bate com as folhas impressas."""

    def test_cada_folha_tem_49_celulas(self):
        for layout in (SheetLayout.uppercase_sheet(), SheetLayout.lowercase_sheet()):
            assert len(layout.cells) == 49

    def test_ordem_das_celulas_segue_as_linhas_da_folha(self):
        upper = SheetLayout.uppercase_sheet()
        assert upper.char_at(0, 0) == "A"
        assert upper.char_at(0, 6) == "G"
        assert upper.char_at(3, 5) == "0"
        assert upper.char_at(6, 6) == "@"
        lower = SheetLayout.lowercase_sheet()
        assert lower.char_at(0, 0) == "a"
        assert lower.char_at(4, 1) == "€"
        assert lower.char_at(6, 6) == "°"

    def test_nomes_de_glifo_seguem_o_padrao_agl(self):
        lower = {c.char: c.glyph_name for c in SheetLayout.lowercase_sheet().cells}
        assert lower["€"] == "Euro"
        assert lower["~"] == "asciitilde"
        assert lower["°"] == "degree"
        upper = {c.char: c.glyph_name for c in SheetLayout.uppercase_sheet().cells}
        assert upper["0"] == "zero"
        assert upper["_"] == "underscore"

    def test_nenhum_caractere_repetido_entre_as_folhas(self):
        chars = [c.char for c in SheetLayout.uppercase_sheet().cells]
        chars += [c.char for c in SheetLayout.lowercase_sheet().cells]
        assert len(chars) == len(set(chars))
