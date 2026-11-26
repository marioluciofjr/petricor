"""Prova focada em uma letra: palavras que testam suas conexões (ex.: o × a)."""
from __future__ import annotations

from pathlib import Path

from ..outline.composer import MasterGlyphSet
from ..outline.family import FamilySpec
from ..outline.weight_profile import profile
from .specimen import SpecimenRenderer


class LetterProof:
    def __init__(self, family: FamilySpec, weights=("Light", "Regular", "Bold")):
        self.family = family
        self.weights = weights

    def render(self, lines: list[str], out_path: Path) -> Path:
        import numpy as np
        skel = self.family.glyphs()
        parts = []
        for w in self.weights:
            outlines = MasterGlyphSet().build(skel, profile(w))
            cmap = {chr(u): g.name for g in outlines.values() for u in g.unicodes}
            r = SpecimenRenderer(outlines, cmap, high_exit=self.family.high_exit_names(skel))
            parts.append(r.render([(f"{self.family.name} - {w}", lines, 150)]))
        return SpecimenRenderer.save(np.vstack(parts), out_path)
