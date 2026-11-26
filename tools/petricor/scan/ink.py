"""Separação da tinta da caneta e das guias impressas do modelo.

Como funciona: convertemos a imagem para HSV (Matiz, Saturação, Valor).
No HSV, a cor "pura" fica no canal H, então dá para separar a caneta
azul-arroxeada (H ≈ 104–130) das guias ciano (H ≈ 88–100) mesmo quando
as duas têm brilho parecido.
"""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class InkThresholds:
    """Limiares medidos nas folhas reais (agrupados num Value Object)."""

    # 106: abaixo disso aparecem pixels claros da guia de base (matiz 103–105)
    hue_range: tuple[int, int] = (106, 140)
    min_saturation: int = 40
    max_value: int = 228
    min_area: int = 25   # componentes menores que isso são sujeira
    close_px: int = 5    # tamanho do "pincel" que reconecta traços


class InkExtractor:
    """Transforma um recorte colorido em máscara binária só com a tinta."""

    def __init__(self, thresholds: InkThresholds | None = None):
        self.t = thresholds or InkThresholds()

    def extract(self, bgr: np.ndarray) -> np.ndarray:
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        lo, hi = self.t.hue_range
        mask = (h >= lo) & (h <= hi) & (s >= self.t.min_saturation) & (v <= self.t.max_value)
        guide = (h >= 82) & (h < lo) & (s >= 35)
        mask = self._bridge_guides(mask.astype(np.uint8), guide)
        mask = self._close_gaps(mask)
        return self._drop_specks(mask).astype(bool)

    @staticmethod
    def _bridge_guides(mask: np.ndarray, guide: np.ndarray, span: int = 11) -> np.ndarray:
        """Reconstrói a tinta 'escondida' sob as guias horizontais.

        Um fechamento só na vertical liga tinta acima e abaixo da guia;
        aceitamos o resultado apenas nos pixels que são guia, para não
        grudar traços vizinhos em outras partes da letra.
        """
        k = cv2.getStructuringElement(cv2.MORPH_RECT, (1, span))
        bridged = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k)
        return (mask | (bridged & guide.astype(np.uint8))).astype(np.uint8)

    def _close_gaps(self, mask: np.ndarray) -> np.ndarray:
        """Fechamento morfológico: reconecta o traço onde a guia o 'cortou'."""
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (self.t.close_px, self.t.close_px))
        return cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k)

    def _drop_specks(self, mask: np.ndarray) -> np.ndarray:
        """Remove sujeiras: componentes com área menor que min_area."""
        n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
        keep = np.zeros(n, bool)
        keep[1:] = stats[1:, cv2.CC_STAT_AREA] >= self.t.min_area
        return keep[labels]
