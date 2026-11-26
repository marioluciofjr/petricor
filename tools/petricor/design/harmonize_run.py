"""Aplica a harmonização a todos os esqueletos brutos (respeitando os editados à mão)."""
from __future__ import annotations

from pathlib import Path

from ..skeleton.store import SkeletonStore
from .harmonizer import Harmonizer


class HarmonizeRun:
    def __init__(self, raw_dir: Path, out_dir: Path, harmonizer: Harmonizer | None = None):
        self.raw = SkeletonStore(raw_dir)
        self.out = SkeletonStore(out_dir)
        self.harmonizer = harmonizer or Harmonizer()

    def run(self) -> dict:
        glyphs = self.raw.all()
        scales = self.harmonizer.class_scales(glyphs)
        written, kept = [], []
        for g in glyphs:
            if self.out.exists(g.name) and self.out.load(g.name).locked:
                kept.append(g.name)  # editado à mão: não sobrescreve
                continue
            self.out.save(self.harmonizer.harmonize(g, scales))
            written.append(g.name)
        return {"written": len(written), "locked": kept}
