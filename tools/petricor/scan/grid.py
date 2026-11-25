"""Localização das 49 células da folha e da linha de base de cada uma.

Estratégia em 3 passos:
1. Achar as bordas ciano arredondadas das células (componentes conexos
   com o tamanho típico de uma célula).
2. Ajustar uma GRADE REGULAR a essas bordas por mínimos quadrados:
   x = x0 + col·px + lin·sx  e  y = y0 + lin·py + col·sy.
   Os termos sx/sy absorvem uma leve rotação do scanner, e as células
   com borda falhada são deduzidas pela grade.
3. Em cada célula, a linha de base é a guia ciano CONTÍNUA (a mais
   comprida); as outras guias são tracejadas.
"""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .layout import COLS, ROWS


@dataclass(frozen=True)
class Cell:
    """Retângulo da célula na folha (pixels) e linha de base relativa."""

    row: int
    col: int
    x: int
    y: int
    w: int
    h: int
    baseline: int  # y da linha de base, relativo ao topo da célula

    def crop(self, image: np.ndarray) -> np.ndarray:
        return image[self.y:self.y + self.h, self.x:self.x + self.w]


class GridSlicer:
    def __init__(self, cell_w_range=(200, 320), cell_h_range=(300, 390), inset=10):
        self.cell_w_range = cell_w_range
        self.cell_h_range = cell_h_range
        self.inset = inset  # margem para não confundir a borda com guias

    # ------------------------------------------------------------------
    def slice(self, image: np.ndarray) -> dict[tuple[int, int], Cell]:
        guides = self._guide_mask(image)
        boxes = self._find_cell_boxes(guides)
        model, size = self._fit_lattice(boxes)
        cells = {}
        for r in range(ROWS):
            for c in range(COLS):
                x, y = self._predict(model, r, c)
                w, h = size
                base = self._find_baseline(guides[y:y + h, x:x + w])
                cells[(r, c)] = Cell(r, c, x, y, w, h, base)
        return cells

    # ------------------------------------------------------------------
    @staticmethod
    def _guide_mask(image: np.ndarray) -> np.ndarray:
        """Máscara das guias ciano (matiz ≈ 85–102)."""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        return ((h >= 82) & (h <= 102) & (s >= 35) & (v >= 150)).astype(np.uint8)

    def _find_cell_boxes(self, guides: np.ndarray) -> list[tuple[int, int, int, int]]:
        n, _, stats, _ = cv2.connectedComponentsWithStats(guides, connectivity=8)
        boxes = []
        for x, y, w, h, _area in stats[1:]:
            if self.cell_w_range[0] < w < self.cell_w_range[1] and self.cell_h_range[0] < h < self.cell_h_range[1]:
                boxes.append((int(x), int(y), int(w), int(h)))
        if len(boxes) < 20:
            raise RuntimeError(f"Poucas células detectadas ({len(boxes)}); confira a digitalização")
        return boxes

    @staticmethod
    def _fit_lattice(boxes):
        """Atribui (linha, coluna) a cada borda e ajusta a grade regular."""
        arr = np.array(boxes, float)
        x0, y0 = arr[:, 0].min(), arr[:, 1].min()
        w_med, h_med = np.median(arr[:, 2]), np.median(arr[:, 3])
        # passo aproximado: célula + vão (~45 px a 300 dpi)
        px_guess, py_guess = w_med + 45, h_med + 12
        cols = np.round((arr[:, 0] - x0) / px_guess).astype(int)
        rows = np.round((arr[:, 1] - y0) / py_guess).astype(int)
        ok = (cols >= 0) & (cols < COLS) & (rows >= 0) & (rows < ROWS)
        A = np.column_stack([np.ones(ok.sum()), cols[ok], rows[ok]])
        coef_x, *_ = np.linalg.lstsq(A, arr[ok, 0], rcond=None)
        coef_y, *_ = np.linalg.lstsq(A, arr[ok, 1], rcond=None)
        return (coef_x, coef_y), (int(round(w_med)), int(round(h_med)))

    @staticmethod
    def _predict(model, r: int, c: int) -> tuple[int, int]:
        coef_x, coef_y = model
        x = coef_x[0] + coef_x[1] * c + coef_x[2] * r
        y = coef_y[0] + coef_y[1] * c + coef_y[2] * r
        return int(round(x)), int(round(y))

    def _find_baseline(self, cell_guides: np.ndarray) -> int:
        """A linha contínua tem mais pixels ciano por linha que as tracejadas."""
        i = self.inset
        inner = cell_guides[i:-i, i:-i]
        counts = inner.sum(axis=1)
        # suaviza 3 linhas (a guia tem 2–4 px de espessura)
        counts = np.convolve(counts, np.ones(3), mode="same")
        h = cell_guides.shape[0]
        lo, hi = int(0.5 * h) - i, int(0.92 * h) - i  # a base fica na metade de baixo
        return int(np.argmax(counts[lo:hi]) + lo + i)
