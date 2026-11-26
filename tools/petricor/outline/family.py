"""Famílias: cada uma é uma pilha de camadas de esqueleto (a primeira vence).

    Petricor            = print/   + redraw/ + base (sources/skeletons)
    Petricor Caligrafia = cursive/ + redraw/ + base

A base guarda o que é compartilhado: maiúsculas, algarismos e símbolos.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..model import GlyphSkeleton
from ..skeleton.store import SkeletonStore


@dataclass(frozen=True)
class FamilySpec:
    name: str          # nome da família (ASCII, regra do Google Fonts)
    file_stem: str     # nome do arquivo, sem espaços
    layers: tuple      # pastas de esqueletos, da mais prioritária para a base

    def glyphs(self) -> dict[str, GlyphSkeleton]:
        merged: dict[str, GlyphSkeleton] = {}
        for folder in reversed(self.layers):  # base primeiro; camadas de cima sobrescrevem
            if Path(folder).exists():
                for g in SkeletonStore(folder).all():
                    merged[g.name] = g
        return merged


class Families:
    """Fábrica das duas famílias a partir da pasta sources/skeletons."""

    def __init__(self, skeletons: Path):
        self.root = Path(skeletons)

    def petricor(self) -> FamilySpec:
        return FamilySpec("Petricor", "Petricor", (self.root / "print", self.root / "redraw", self.root))

    def caligrafia(self) -> FamilySpec:
        return FamilySpec("Petricor Caligrafia", "PetricorCaligrafia",
                          (self.root / "cursive", self.root / "redraw", self.root))

    def all(self) -> list[FamilySpec]:
        return [self.petricor(), self.caligrafia()]
