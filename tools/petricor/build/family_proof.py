"""Provas das famílias: alfabeto, texto em português e pangramas com acentos."""
from __future__ import annotations

from pathlib import Path

import numpy as np

from ..outline.composer import MasterGlyphSet
from ..outline.family import FamilySpec
from ..outline.weight_profile import profile
from .specimen import SpecimenRenderer

ALPHABET = ["ABCDEFGHIJKLM", "NOPQRSTUVWXYZ", "abcdefghijklm", "nopqrstuvwxyz", "0123456789 @&"]
TEXT = ["O cheiro da terra molhada", "chama-se petricor. Ele vem", "da chuva que bate no chão",
        "quando o sol vai embora."]
WORDS = ["Harmonia nova vovó", "bom ovo, uva, wow"]
PANGRAMS = [
    "Pão de açúcar, maçã, ônibus",
    "Àquela época, você já sabia?",
    "¿Qué pasó? ¡Señor! «Ça va»",
    "Größe, Øre, œuvre, Łódź, ß",
    "“Aspas” — travessão… © ® ™ § ¶",
    "ÁÉÍÓÚ ÂÊÔ ÃÕ Ç ÀÜ Ñ Ž Š Č Ř",
]


class FamilyProof:
    def __init__(self, families: list[FamilySpec], weight: str = "Regular"):
        self.families = families
        self.prof = profile(weight)
        self.glyphset = MasterGlyphSet()

    def _renderer(self, fam: FamilySpec) -> SpecimenRenderer:
        skeletons = fam.glyphs()
        outlines = self.glyphset.build(skeletons, self.prof)
        cmap = {chr(u): g.name for g in outlines.values() for u in g.unicodes}
        return SpecimenRenderer(outlines, cmap, high_exit=fam.high_exit_names(skeletons))

    def render(self, out_path: Path, with_accents: bool = False) -> Path:
        parts = []
        for fam in self.families:
            r = self._renderer(fam)
            blocks = [(f"{fam.name} - {self.prof.name}", ALPHABET, 110), ("Texto", TEXT, 120),
                      ("Conexoes (o, v, w, b saem pelo alto)", WORDS, 120)]
            if with_accents:
                blocks.append(("Acentos e sinais", PANGRAMS, 110))
            parts.append(r.render(blocks))
        return SpecimenRenderer.save(np.vstack(parts), out_path)
