"""Prova 2: alfabeto antes × depois da harmonização, no peso Regular."""
from __future__ import annotations

from pathlib import Path

from ..outline.glyph_factory import OutlineGlyphFactory
from ..outline.weight_profile import profile
from ..skeleton.store import SkeletonStore
from .specimen import SpecimenRenderer

LINES = [
    "ABCDEFGHIJKLM",
    "NOPQRSTUVWXYZ",
    "abcdefghijklm",
    "nopqrstuvwxyz",
    "0123456789 &@",
    "!?.,;:'\"()[]{}",
    "#$%€£¥*+×÷=<>",
    "/\\|-_~°",
]
WORDS = ["Petricor chegou", "Harmonia da letra", "Sabor de chuva 2026"]


class HarmonizeProof:
    def __init__(self, raw_dir: Path, skeleton_dir: Path, weight: str = "Regular"):
        self.raw = SkeletonStore(raw_dir)
        self.harmonized = SkeletonStore(skeleton_dir)
        self.factory = OutlineGlyphFactory()
        self.prof = profile(weight)

    def _outlines(self, store: SkeletonStore):
        glyphs = {g.name: self.factory.build(g, self.prof) for g in store.all()}
        cmap = {chr(u): g.name for g in glyphs.values() for u in g.unicodes}
        return glyphs, cmap

    def render(self, out_path: Path) -> Path:
        raw, cmap = self._outlines(self.raw)
        harm, _ = self._outlines(self.harmonized)
        before = SpecimenRenderer(raw, cmap).render([("ANTES (vetorizado, sem harmonizar)", LINES[:5], 120)])
        after = SpecimenRenderer(harm, cmap).render([
            (f"DEPOIS (harmonizado) - {self.prof.name}", LINES, 120),
            ("Palavras", WORDS, 150),
        ])
        import numpy as np
        return SpecimenRenderer.save(np.vstack([before, after]), out_path)
