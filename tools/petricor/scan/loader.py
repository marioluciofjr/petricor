"""Leitura da folha digitalizada do disco."""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


class SheetLoader:
    """Carrega a imagem em BGR (o formato nativo do OpenCV)."""

    @staticmethod
    def load(path: Path | str) -> np.ndarray:
        # cv2.imread não lê caminhos com acento no Windows; imdecode lê.
        data = np.fromfile(str(path), dtype=np.uint8)
        image = cv2.imdecode(data, cv2.IMREAD_COLOR)
        if image is None:
            raise FileNotFoundError(f"Não foi possível ler a folha: {path}")
        return image
