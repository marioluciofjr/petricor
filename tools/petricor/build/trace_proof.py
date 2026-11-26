"""Prova 1: original × vetorizado, lado a lado, para o Mário conferir."""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from ..scan.grid import GridSlicer
from ..scan.layout import SheetLayout
from ..scan.loader import SheetLoader
from ..skeleton.store import SkeletonStore


class TraceProof:
    """Desenha cada célula original e, ao lado, o esqueleto vetorial em vermelho."""

    TILE = (170, 230)  # largura, altura de cada metade

    def __init__(self, scans_dir: Path, skeleton_dir: Path, scale: float):
        self.scans_dir = Path(scans_dir)
        self.store = SkeletonStore(skeleton_dir)
        self.scale = scale

    def render(self, out_path: Path) -> Path:
        sheets = {"maiusculas.jpeg": SheetLayout.uppercase_sheet(),
                  "minusculas.jpeg": SheetLayout.lowercase_sheet()}
        rows = []
        for f, layout in sheets.items():
            img = SheetLoader.load(self.scans_dir / f)
            cells = GridSlicer().slice(img)
            for r in range(7):
                tiles = [self._pair(img, cells[(r, c)], layout.cells[r * 7 + c]) for c in range(7)]
                rows.append(np.hstack(tiles))
        sheet = np.vstack(rows)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imencode(".png", sheet)[1].tofile(str(out_path))
        return out_path

    def _pair(self, img, cell, spec):
        crop = cell.crop(img).copy()
        vec = np.full_like(crop, 255)
        glyph = self.store.load(spec.glyph_name)
        for stroke in glyph.strokes:
            pts = stroke.sample(24)
            px = np.column_stack([pts[:, 0] / self.scale, cell.baseline - pts[:, 1] / self.scale])
            cv2.polylines(vec, [px.round().astype(np.int32)], stroke.closed, (40, 40, 220), 2, cv2.LINE_AA)
            for seg in stroke.segments:  # nós em azul: ajudam a ver onde editar
                x, y = seg.p0
                cv2.circle(vec, (int(x / self.scale), int(cell.baseline - y / self.scale)), 3, (200, 120, 0), -1)
        cv2.line(vec, (0, cell.baseline), (vec.shape[1], cell.baseline), (200, 200, 200), 1)
        both = np.hstack([cv2.resize(crop, self.TILE), cv2.resize(vec, self.TILE)])
        return cv2.copyMakeBorder(both, 2, 2, 2, 2, cv2.BORDER_CONSTANT, value=(180, 180, 180))
