"""Mapa das folhas do fontmaker.co: qual caractere está em cada célula.

As duas folhas têm uma grade de 7 linhas × 7 colunas. Esta classe só
guarda a ORDEM dos caracteres; a posição em pixels é descoberta pelo
GridSlicer. Separar as duas coisas mantém cada classe com uma única
responsabilidade (alta coesão).
"""
from __future__ import annotations

from dataclasses import dataclass

from fontTools.agl import UV2AGL

ROWS = 7
COLS = 7


@dataclass(frozen=True)
class CellSpec:
    """Uma célula da folha: posição na grade + caractere esperado."""

    row: int
    col: int
    char: str

    @property
    def glyph_name(self) -> str:
        """Nome de produção do glifo (padrão AGL, ex.: '€' → 'Euro')."""
        return UV2AGL.get(ord(self.char), f"uni{ord(self.char):04X}")


class SheetLayout:
    """Ordem dos caracteres de uma folha, linha a linha."""

    def __init__(self, sheet_id: str, rows: list[str]):
        if len(rows) != ROWS or any(len(r) != COLS for r in rows):
            raise ValueError("Cada folha precisa de 7 linhas com 7 caracteres")
        self.sheet_id = sheet_id
        self.cells = [CellSpec(r, c, ch) for r, line in enumerate(rows) for c, ch in enumerate(line)]

    def char_at(self, row: int, col: int) -> str:
        return self.cells[row * COLS + col].char

    # --- Fábricas das duas folhas usadas pelo Mário -----------------------
    @classmethod
    def uppercase_sheet(cls) -> "SheetLayout":
        """Folha 1/2: maiúsculas, algarismos e pontuação básica."""
        return cls("maiusculas", [
            "ABCDEFG",
            "HIJKLMN",
            "OPQRSTU",
            "VWXYZ01",
            "2345678",
            "9!?.,;:",
            "'\"()_&@",
        ])

    @classmethod
    def lowercase_sheet(cls) -> "SheetLayout":
        """Folha 2/2: minúsculas cursivas e símbolos."""
        return cls("minusculas", [
            "abcdefg",
            "hijklmn",
            "opqrstu",
            "vwxyz#$",
            "%€£¥*+×",
            "÷=/\\-<>",
            "[]{}|~°",
        ])
