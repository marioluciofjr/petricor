"""Prova a partir da fonte COMPILADA: HarfBuzz compõe o texto (como num navegador).

Valida de uma vez: interpolação dos pesos, regras OpenType (calt, ccmp,
mark, tnum) e acentos — exatamente como a pessoa usuária verá.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import uharfbuzz as hb
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont


class FlattenPen(BasePen):
    """Converte curvas em polígonos (para pintar com o OpenCV)."""

    def __init__(self, glyphset):
        super().__init__(glyphset)
        self.polys, self.cur = [], []

    def _moveTo(self, p):
        self.cur = [p]

    def _lineTo(self, p):
        self.cur.append(p)

    def _curveToOne(self, p1, p2, p3):
        p0 = self.cur[-1]
        for t in np.linspace(0, 1, 10)[1:]:
            mt = 1 - t
            self.cur.append(tuple(mt ** 3 * np.array(p0) + 3 * mt ** 2 * t * np.array(p1)
                                  + 3 * mt * t ** 2 * np.array(p2) + t ** 3 * np.array(p3)))

    def _qCurveToOne(self, p1, p2):
        p0 = self.cur[-1]
        for t in np.linspace(0, 1, 8)[1:]:
            mt = 1 - t
            self.cur.append(tuple(mt ** 2 * np.array(p0) + 2 * mt * t * np.array(p1) + t ** 2 * np.array(p2)))

    def _closePath(self):
        if len(self.cur) > 2:
            self.polys.append(np.array(self.cur))
        self.cur = []

    _endPath = _closePath


@dataclass(frozen=True)
class LineSpec:
    """Uma linha de prova: texto, peso (eixo wght), tamanho em px e recursos OpenType."""

    text: str
    wght: float
    size: int
    features: dict | None = None


class VariableFontProof:
    def __init__(self, font_path: Path):
        self.path = Path(font_path)
        self.tt = TTFont(str(self.path))
        self.blob = hb.Blob.from_file_path(str(self.path))
        self.order = self.tt.getGlyphOrder()

    def line(self, spec: LineSpec, width: int = 2200) -> np.ndarray:
        size = spec.size
        face = hb.Face(self.blob)
        font = hb.Font(face)
        font.set_variations({"wght": spec.wght})
        buf = hb.Buffer()
        buf.add_str(spec.text)
        buf.guess_segment_properties()
        hb.shape(font, buf, spec.features or {})
        gs = self.tt.getGlyphSet(location={"wght": spec.wght})
        scale = size / 1000
        img = np.full((int(size * 1.45), width, 3), 255, np.uint8)
        base_y, x = int(size * 1.05), 40.0
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            pen = FlattenPen(gs)
            gs[self.order[info.codepoint]].draw(pen)
            ox, oy = x + pos.x_offset * scale, base_y - pos.y_offset * scale
            for poly in pen.polys:
                px = np.column_stack([ox + poly[:, 0] * scale, oy - poly[:, 1] * scale])
                cv2.fillPoly(img, [np.round(px * 4).astype(np.int32)], (25, 25, 25), cv2.LINE_AA, shift=2)
            x += pos.x_advance * scale
        return img


class WeightsCascade:
    """Prova 5: a mesma frase nos 9 pesos, para cada fonte variável."""

    def __init__(self, fonts: list[tuple[str, Path, int]], text: str):
        self.fonts = fonts  # (rótulo, arquivo, peso máximo do eixo)
        self.text = text

    def render(self, out: Path, size: int = 90) -> Path:
        rows = []
        for label, path, max_w in self.fonts:
            proof = VariableFontProof(path)
            title = np.full((60, 2200, 3), 255, np.uint8)
            cv2.putText(title, label, (40, 45), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (110, 110, 110), 2, cv2.LINE_AA)
            rows.append(title)
            for w in range(100, max_w + 1, 100):
                rows.append(proof.line(LineSpec(self.text, w, size)))
        out.parent.mkdir(parents=True, exist_ok=True)
        cv2.imencode(".png", np.vstack(rows))[1].tofile(str(out))
        return out
