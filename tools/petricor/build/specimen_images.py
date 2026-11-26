"""Imagens de espécime para o README e a pasta documentation/ (a partir das fontes finais)."""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from .vf_proof import LineSpec, VariableFontProof


class SpecimenImages:
    """Gera um cartaz por família: nome grande, pesos e uma frase em português."""

    def __init__(self, fonts_dir: Path, out_dir: Path):
        self.fonts_dir = Path(fonts_dir)
        self.out_dir = Path(out_dir)

    def family(self, stem: str, title: str, max_w: int, sentence: str) -> Path:
        proof = VariableFontProof(self.fonts_dir / "variable" / f"{stem}[wght].ttf")
        rows = [proof.line(LineSpec(title, 500, 200), width=2000)]
        for w in range(100, max_w + 1, 100):
            rows.append(proof.line(LineSpec(f"{w}  {sentence}", w, 64), width=2000))
        rows.append(proof.line(LineSpec("ABCDEFGHIJKLMNOPQRSTUVWXYZ", 400, 80), width=2000))
        rows.append(proof.line(LineSpec("abcdefghijklmnopqrstuvwxyz 0123456789", 400, 80), width=2000))
        img = np.vstack(rows)
        out = self.out_dir / f"{stem}-specimen.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        cv2.imencode(".png", img)[1].tofile(str(out))
        return out

    def all(self) -> list[Path]:
        return [
            self.family("Petricor", "Petricor", 900, "O cheiro da terra molhada depois da chuva."),
            self.family("PetricorCaligrafia", "Petricor Caligrafia", 600, "O cheiro da terra molhada depois da chuva."),
        ]
