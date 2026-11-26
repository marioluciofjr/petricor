"""Renderização de provas a partir dos contornos (sem precisar compilar a fonte)."""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from ..outline.glyph_factory import OutlineGlyph


class GlyphRasterizer:
    """Pinta contornos numa imagem. Cada cápsula é preenchida e somada (união)."""

    def __init__(self, glyphs: dict | None = None, color=(30, 30, 30)):
        self.glyphs = glyphs or {}
        self.color = color

    def draw(self, canvas: np.ndarray, glyph: OutlineGlyph, origin: tuple[float, float], scale: float):
        ox, oy = origin
        for contour in glyph.contours:
            pts = np.vstack([c.sample(16) for c in contour])
            px = np.column_stack([ox + pts[:, 0] * scale, oy - pts[:, 1] * scale])
            cv2.fillPoly(canvas, [np.round(px * 4).astype(np.int32)], self.color, cv2.LINE_AA, shift=2)
        for comp in glyph.components:  # compostos: desenha cada peça no seu deslocamento
            if comp.base in self.glyphs:
                self.draw(canvas, self.glyphs[comp.base], (ox + comp.dx * scale, oy - comp.dy * scale), scale)


class SimpleShaper:
    """Imita a regra 'calt' da fonte: depois de letra com saída alta, usa a variante .hi."""

    def __init__(self, cmap: dict[str, str], glyph_names: set[str], high_exit: set[str]):
        self.cmap = cmap
        self.names = glyph_names
        self.high_exit = high_exit

    def shape(self, text: str) -> list[str | None]:
        out, prev = [], None
        for ch in text:
            name = self.cmap.get(ch)
            if name and prev and prev in self.high_exit and f"{name}.hi" in self.names:
                name = f"{name}.hi"
            out.append(name)
            prev = name
        return out


class SpecimenRenderer:
    """Compõe linhas de texto com os glifos e salva em PNG."""

    def __init__(self, glyphs: dict[str, OutlineGlyph], cmap: dict[str, str], space: float = 260,
                 high_exit: set[str] | None = None):
        self.glyphs = glyphs
        self.space = space
        self.shaper = SimpleShaper(cmap, set(glyphs), high_exit or set())
        self.rasterizer = GlyphRasterizer(glyphs)

    def _advance(self, name: str | None) -> float:
        return self.glyphs[name].advance if name in self.glyphs else self.space

    def render(self, blocks: list[tuple[str, list[str], float]], width: int = 2400, margin: int = 60) -> np.ndarray:
        """blocks = [(título, [linhas], tamanho em px por 1000 unidades)]."""
        rows = []
        for title, lines, size in blocks:
            scale = size / 1000
            line_h = int(size * 1.35)
            img = np.full((int(size * 0.5) + line_h * len(lines) + 20, width, 3), 255, np.uint8)
            cv2.putText(img, title, (margin, int(size * 0.35)), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (120, 120, 120), 2, cv2.LINE_AA)
            for i, text in enumerate(lines):
                base = int(size * 0.5) + line_h * i + int(size * 1.0)
                cv2.line(img, (margin, base), (width - margin, base), (235, 220, 200), 1)
                x = margin
                for name in self.shaper.shape(text):
                    if name in self.glyphs:
                        self.rasterizer.draw(img, self.glyphs[name], (x, base), scale)
                    x += self._advance(name) * scale
            rows.append(img)
        return np.vstack(rows)

    @staticmethod
    def save(img: np.ndarray, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imencode(".png", img)[1].tofile(str(path))
        return path
