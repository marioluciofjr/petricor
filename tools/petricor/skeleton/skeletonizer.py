"""Afinamento da tinta até uma linha de 1 pixel (o 'esqueleto').

Imagine a tinta derretendo pelas bordas até sobrar só o fio do meio:
é isso que o skeletonize faz. Junto, medimos a espessura original da
caneta com a transformada de distância (distância de cada pixel de
tinta até o papel mais próximo).
"""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np
from skimage.morphology import remove_small_holes, skeletonize


@dataclass(frozen=True)
class SkeletonResult:
    skeleton: np.ndarray   # máscara booleana de 1 px de largura
    stroke_width: float    # espessura típica do traço original (px)


class Skeletonizer:
    def __init__(self, smooth_sigma: float = 1.2, max_hole_area: int = 40):
        self.smooth_sigma = smooth_sigma
        self.max_hole_area = max_hole_area

    def run(self, mask: np.ndarray) -> SkeletonResult:
        clean = self._smooth(mask)
        skel = skeletonize(clean)
        return SkeletonResult(skel, self._stroke_width(clean, skel))

    def _smooth(self, mask: np.ndarray) -> np.ndarray:
        """Arredonda as bordas serrilhadas e tapa furinhos de tinta falhada.

        Furinhos viram laços falsos no esqueleto; contraformas de verdade
        (o 'olho' do e, por exemplo) são maiores que max_hole_area.
        """
        blurred = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), self.smooth_sigma)
        solid = blurred > 0.5
        return remove_small_holes(solid, max_size=self.max_hole_area)

    @staticmethod
    def _stroke_width(mask: np.ndarray, skel: np.ndarray) -> float:
        if not skel.any():
            return 0.0
        dist = cv2.distanceTransform(mask.astype(np.uint8), cv2.DIST_L2, 5)
        # no centro de um traço de largura L, a distância ao papel é (L + 1) / 2
        return float(2 * np.median(dist[skel]) - 1)
