"""Vetoriza as duas folhas inteiras e grava os esqueletos brutos em JSON."""
from __future__ import annotations

from pathlib import Path

import numpy as np

from ..scan.grid import GridSlicer
from ..scan.layout import SheetLayout
from ..scan.loader import SheetLoader
from .glyph_tracer import GlyphTracer, PixelToUnits
from .store import SkeletonStore

CAP_HEIGHT_UNITS = 700
FLAT_TOP_CAPS = "EFHIKLMNTZ"  # maiúsculas de topo reto: medida confiável da altura


class CapHeightProbe:
    """Mede a altura das maiúsculas (px) para definir a escala px → unidades."""

    def __init__(self, tracer: GlyphTracer):
        self.tracer = tracer

    def measure(self, image, cells, layout: SheetLayout) -> float:
        heights = []
        for spec in layout.cells:
            if spec.char in FLAT_TOP_CAPS:
                cell = cells[(spec.row, spec.col)]
                rows = np.nonzero(self.tracer.ink_mask(cell.crop(image)).any(axis=1))[0]
                heights.append(cell.baseline - rows.min())
        return float(np.median(heights))


class SheetTracer:
    def __init__(self, scans_dir: Path, out_dir: Path, tracer: GlyphTracer | None = None):
        self.scans_dir = Path(scans_dir)
        self.store = SkeletonStore(out_dir)
        self.tracer = tracer or GlyphTracer()
        self.sheets = {"maiusculas.jpeg": SheetLayout.uppercase_sheet(),
                       "minusculas.jpeg": SheetLayout.lowercase_sheet()}

    def run(self) -> dict:
        loaded = {f: SheetLoader.load(self.scans_dir / f) for f in self.sheets}
        grids = {f: GridSlicer().slice(img) for f, img in loaded.items()}
        cap_px = CapHeightProbe(self.tracer).measure(loaded["maiusculas.jpeg"], grids["maiusculas.jpeg"],
                                                     self.sheets["maiusculas.jpeg"])
        scale = CAP_HEIGHT_UNITS / cap_px  # a mesma escala vale para as duas folhas
        report = {"cap_height_px": cap_px, "scale": scale, "glyphs": {}}
        for f, layout in self.sheets.items():
            for spec in layout.cells:
                cell = grids[f][(spec.row, spec.col)]
                to_units = PixelToUnits(scale, 0.0, cell.baseline)
                glyph, width_px = self.tracer.trace(cell.crop(loaded[f]), to_units,
                                                    spec.glyph_name, [ord(spec.char)])
                self.store.save(glyph)
                report["glyphs"][spec.glyph_name] = {"strokes": len(glyph.strokes),
                                                     "pen_units": round(width_px * scale, 1)}
        return report
