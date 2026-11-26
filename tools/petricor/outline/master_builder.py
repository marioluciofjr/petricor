"""Escreve os masters UFO e o designspace de cada família."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import ufoLib2
from fontTools.designspaceLib import AxisDescriptor, DesignSpaceDocument, InstanceDescriptor, SourceDescriptor

from .composer import MasterGlyphSet
from .family import FamilySpec
from .feature_writer import FeatureWriter
from .font_info import FontInfo
from .glyph_factory import OutlineGlyph
from .weight_profile import WeightProfile

UFO_ANCHORS = {"top", "bottom", "ogonek", "caron", "_top", "_bottom", "_ogonek", "_caron"}


class UfoGlyphWriter:
    """Converte um OutlineGlyph em glifo UFO (contornos, componentes, âncoras)."""

    @staticmethod
    def write(ufo, g: OutlineGlyph) -> None:
        glyph = ufo.newGlyph(g.name)
        glyph.unicodes = list(g.unicodes)
        glyph.width = UfoGlyphWriter._int(g.advance)
        pen = glyph.getPen()
        for contour in g.contours:
            pen.moveTo(UfoGlyphWriter._r(contour[0].p0))
            for c in contour:
                pen.curveTo(UfoGlyphWriter._r(c.p1), UfoGlyphWriter._r(c.p2), UfoGlyphWriter._r(c.p3))
            pen.closePath()
        for comp in g.components:
            pen.addComponent(comp.base, (1, 0, 0, 1, UfoGlyphWriter._int(comp.dx), UfoGlyphWriter._int(comp.dy)))
        # só âncoras de acento: 'entry'/'exit' gerariam uma regra 'curs' indesejada
        for name, (x, y) in sorted(g.anchors.items()):
            if name in UFO_ANCHORS:
                glyph.appendAnchor({"name": name, "x": UfoGlyphWriter._int(x), "y": UfoGlyphWriter._int(y)})

    @staticmethod
    def _int(v) -> int:
        return int(round(float(v)))

    @staticmethod
    def _r(p):
        """Converte para float do Python (o numpy vazaria 'np.float64(...)' no XML do UFO)."""
        return (round(float(p[0]), 2), round(float(p[1]), 2))


@dataclass(frozen=True)
class MasterContext:
    """O que é igual para os 3 masters de uma família (agrupado num objeto)."""

    family: FamilySpec
    info: FontInfo
    win: tuple[int, int]
    features: str


class MasterBuilder:
    """Gera os 3 masters (Thin, Regular, Black) de uma família + designspace."""

    def __init__(self, out_dir: Path, glyphset: MasterGlyphSet | None = None):
        self.out_dir = Path(out_dir)
        self.glyphset = glyphset or MasterGlyphSet()

    def build(self, family: FamilySpec) -> Path:
        skeletons = family.glyphs()
        masters = {p.name: self.glyphset.build(skeletons, p) for p in family.masters()}
        names = set(next(iter(masters.values())))
        ctx = MasterContext(family, FontInfo(family.name), self._win_metrics(masters),
                            FeatureWriter(names, family.high_exit_names(skeletons)).write())
        paths = {p.name: self._write_ufo(ctx, p, masters[p.name]) for p in family.masters()}
        return self._write_designspace(family, paths)

    @staticmethod
    def _win_metrics(masters) -> tuple[int, int]:
        """winAscent/winDescent = caixa que envolve TODOS os glifos da família (regra do GF)."""
        ymin, ymax = 0.0, 0.0
        for glyphs in masters.values():
            boxes = {n: g.bounds() for n, g in glyphs.items()}
            for n, g in glyphs.items():
                b = boxes[n]
                if b:
                    ymin, ymax = min(ymin, b[1]), max(ymax, b[3])
                for c in g.components:  # compostos: caixa da peça deslocada
                    cb = boxes.get(c.base)
                    if cb:
                        ymin, ymax = min(ymin, cb[1] + c.dy), max(ymax, cb[3] + c.dy)
        return int(np.ceil(ymax)) + 10, int(np.ceil(-ymin)) + 10

    def _write_ufo(self, ctx: MasterContext, prof: WeightProfile, glyphs) -> Path:
        ufo = ufoLib2.Font()
        ctx.info.apply(ufo, prof.name, prof.wght, ctx.win)
        order = sorted(glyphs, key=self._order_key)
        for name in order:
            UfoGlyphWriter.write(ufo, glyphs[name])
        ufo.glyphOrder = order
        ufo.features.text = ctx.features
        path = self.out_dir / f"{ctx.family.file_stem}-{prof.name}.ufo"
        path.parent.mkdir(parents=True, exist_ok=True)
        ufo.save(path, overwrite=True)
        return path

    @staticmethod
    def _order_key(name: str):
        """Ordem amigável: espaço, maiúsculas, minúsculas, algarismos, resto, variantes."""
        base = name.split(".")[0]
        group = 0 if name == "space" else 1 if base[:1].isupper() else 2 if base[:1].islower() else 3
        return (("." in name), group, name)

    def _write_designspace(self, family: FamilySpec, paths: dict) -> Path:
        doc = DesignSpaceDocument()
        axis = AxisDescriptor()
        axis.name, axis.tag = "Weight", "wght"
        axis.minimum, axis.default, axis.maximum = 100, 400, family.max_wght
        doc.addAxis(axis)
        for prof in family.masters():
            src = SourceDescriptor()
            src.path = str(paths[prof.name])
            src.filename = paths[prof.name].name
            src.familyName, src.styleName = family.name, prof.name
            src.location = {"Weight": prof.wght}
            doc.addSource(src)
        for prof in family.instances():
            inst = InstanceDescriptor()
            inst.familyName, inst.styleName = family.name, prof.name
            inst.location = {"Weight": prof.wght}
            inst.filename = f"instances/{family.file_stem}-{prof.name}.ufo"
            doc.addInstance(inst)
        out = self.out_dir / f"{family.file_stem}.designspace"
        doc.write(out)
        return out
