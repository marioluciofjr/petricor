"""Prova 5: a mesma frase nos 9 pesos, nas duas famílias."""
from __future__ import annotations

from pathlib import Path

import numpy as np

from ..outline.composer import MasterGlyphSet
from ..outline.family import FamilySpec
from .specimen import SpecimenRenderer

LINE = "Petricor: chuva no chão 2026"


class WeightsProof:
    def __init__(self, families: list[FamilySpec]):
        self.families = families
        self.glyphset = MasterGlyphSet()

    def render(self, out_path: Path) -> Path:
        parts = []
        for fam in self.families:
            skel = fam.glyphs()
            high = fam.high_exit_names(skel)
            for prof in fam.instances():
                outlines = self.glyphset.build(skel, prof)
                cmap = {chr(u): g.name for g in outlines.values() for u in g.unicodes}
                r = SpecimenRenderer(outlines, cmap, high_exit=high)
                parts.append(r.render([(f"{fam.name} {prof.name} ({prof.wght})", [LINE], 95)], width=2000))
        return SpecimenRenderer.save(np.vstack(parts), out_path)
