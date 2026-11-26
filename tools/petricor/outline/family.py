"""Famílias: cada uma é uma pilha de camadas de esqueleto (a primeira vence).

    Petricor            = print/   + common/ + base (sources/skeletons)
    Petricor Caligrafia = cursive/ + common/ + base

- base    : o que veio das folhas, harmonizado (maiúsculas, algarismos, símbolos)
- common  : derivados iguais nas duas famílias (0 9 @ refeitos, acentos,
            compostos, aspas, travessões, Æ, Ø...)
- print   : minúsculas de forma (Petricor)
- cursive : minúsculas conectadas + variantes .hi (Caligrafia)
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..design.recipes import HIGH_EXIT
from ..model import GlyphSkeleton
from ..skeleton.store import SkeletonStore
from .weight_profile import INSTANCES, WeightProfile


@dataclass(frozen=True)
class FamilySpec:
    name: str          # nome da família (ASCII, regra do Google Fonts)
    file_stem: str     # nome do arquivo, sem espaços
    layers: tuple      # pastas de esqueletos, da mais prioritária para a base
    max_wght: int = 900  # peso máximo do eixo (Caligrafia para no SemiBold: decisão do Mário)

    def instances(self) -> list[WeightProfile]:
        return [p for p in INSTANCES if p.wght <= self.max_wght]

    def masters(self) -> list[WeightProfile]:
        """Thin, Regular e o peso mais pesado da família."""
        inst = self.instances()
        return [inst[0], next(p for p in inst if p.wght == 400), inst[-1]]

    def glyphs(self) -> dict[str, GlyphSkeleton]:
        merged: dict[str, GlyphSkeleton] = {}
        for folder in reversed(self.layers):  # base primeiro; camadas de cima sobrescrevem
            if Path(folder).exists():
                for g in SkeletonStore(folder).all():
                    merged[g.name] = g
        return merged

    @staticmethod
    def high_exit_names(glyphs: dict[str, GlyphSkeleton]) -> set[str]:
        """Glifos que terminam pela junção alta: o, v, w, b e seus acentuados (ó, õ, ŵ...)."""
        out = set()
        for name, g in glyphs.items():
            first = g.components[0].base if g.components else name
            if first.split(".")[0] in HIGH_EXIT and not name.endswith(".tf"):
                out.add(name)
        return out


class Families:
    """Fábrica das duas famílias a partir da pasta sources/skeletons."""

    def __init__(self, skeletons: Path):
        self.root = Path(skeletons)

    def layer(self, name: str) -> Path:
        return self.root / name

    def petricor(self) -> FamilySpec:
        return FamilySpec("Petricor", "Petricor", (self.layer("print"), self.layer("common"), self.root))

    def caligrafia(self) -> FamilySpec:
        # Bold e Black ficariam ilegíveis na cursiva (laços fechados): eixo vai até 600
        return FamilySpec("Petricor Caligrafia", "PetricorCaligrafia",
                          (self.layer("cursive"), self.layer("common"), self.root), max_wght=600)

    def all(self) -> list[FamilySpec]:
        return [self.petricor(), self.caligrafia()]
