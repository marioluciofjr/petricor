"""Construtores que transformam as receitas em esqueletos (GlyphSkeleton)."""
from __future__ import annotations

import numpy as np

from ..model import GlyphSkeleton, Stroke
from ..skeleton.store import SkeletonStore
from . import recipes as R
from .skeleton_pen import Corner, HandJitter, SkeletonPen

ANGLE_LOW = np.radians(35)
TAN_LOW = (float(np.cos(ANGLE_LOW)), float(np.sin(ANGLE_LOW)))
TAN_HIGH = (1.0, 0.0)


class RecipeReader:
    """Converte um item de receita (lista de pontos ou dict) em Stroke."""

    @staticmethod
    def stroke(item) -> Stroke:
        if isinstance(item, dict):
            return SkeletonPen.spline(item["points"], closed=item.get("closed", False))
        if len(item) == 1:
            return SkeletonPen.dot(item[0])
        return SkeletonPen.spline(item)


class CursiveBuilder:
    """Minúsculas conectadas: entrada em (0, junção) e saída em (largura, junção).

    Variante 'hi': entra pela junção alta (depois de o, v, w, b).
    As âncoras 'entry' e 'exit' guardam os pontos de conexão; o Spacer
    usa 'exit' como largura de avanço, então a saída de uma letra cai
    exatamente sobre a entrada da próxima.
    """

    def __init__(self, jitter: HandJitter | None = None):
        self.jitter = jitter or HandJitter()

    def build(self, letter: str, high_entry: bool = False) -> GlyphSkeleton:
        rec = R.CURSIVE[letter]
        high_exit = rec.get("exit") == "high"
        j_in = R.JOIN_HIGH if high_entry else R.JOIN_LOW
        j_out = R.JOIN_HIGH if high_exit else R.JOIN_LOW
        pts = self._points(rec, j_in, j_out, high_entry)
        entry, exit_ = (0.0, j_in), (float(rec["main"][-1][1]), j_out)
        main = SkeletonPen.spline(pts, start_tangent=TAN_HIGH if high_entry else TAN_LOW,
                                  end_tangent=TAN_HIGH if high_exit else TAN_LOW)
        name = f"{letter}.hi" if high_entry else letter
        strokes = [self.jitter.apply(main, name, protect=[entry, exit_])]
        strokes += [self.jitter.apply(RecipeReader.stroke(e), name + "x") for e in rec.get("extra", [])]
        strokes += [SkeletonPen.dot(d) for d in rec.get("dots", [])]
        return GlyphSkeleton(name, [] if high_entry else [ord(letter)], strokes, advance=exit_[0],
                             anchors={"entry": entry, "exit": exit_})

    @staticmethod
    def _points(rec, j_in, j_out, high_entry):
        out = []
        lead = rec.get("lead", 0)
        if high_entry and "lead_hi" in rec:  # receita com conector alto próprio
            body = rec["main"][1 + lead:]
            rec = {**rec, "main": ["E", *rec["lead_hi"], *body], "lead": 0}
        for i, p in enumerate(rec["main"]):
            if p == "E":
                out.append((0.0, j_in))
            elif isinstance(p, tuple) and p and p[0] == "X":
                out.append((float(p[1]), j_out))
            elif high_entry and 1 <= i <= lead and SkeletonPen.xy(p)[1] < j_in - 100:
                continue  # conector baixo não faz sentido quando a entrada vem do alto
            else:
                out.append(p)
        return out


class PrintBuilder:
    """Minúsculas de forma: receitas próprias + maiúsculas reduzidas + letras do Mário."""

    def __init__(self, base: SkeletonStore, jitter: HandJitter | None = None):
        self.base = base
        self.jitter = jitter or HandJitter()

    @staticmethod
    def names() -> list[str]:
        return sorted(set(R.PRINT) | set(R.PRINT_FROM_CAPS) | set(R.PRINT_FROM_HAND))

    def build(self, letter: str) -> GlyphSkeleton:
        if letter in R.PRINT:
            strokes = [self._jit(RecipeReader.stroke(it), letter, i) for i, it in enumerate(R.PRINT[letter])]
        elif letter in R.PRINT_FROM_CAPS:
            cap, sx, sy = R.PRINT_FROM_CAPS[letter]
            src = self.base.load(cap)
            strokes = [s.transformed(lambda p: (p[0] * sx, p[1] * sy)) for s in src.strokes]
        else:
            strokes = list(self.base.load(letter).strokes)
        g = GlyphSkeleton(letter, [ord(letter)], strokes)
        b = g.bounds()
        g.advance = b[2] - b[0]
        return g

    def _jit(self, stroke: Stroke, letter: str, i: int) -> Stroke:
        is_dot = all(np.ptp(s.as_array(), axis=0).max() < 0.5 for s in stroke.segments)
        return stroke if is_dot else self.jitter.apply(stroke, f"{letter}{i}")


class RedrawBuilder:
    """Glifos refeitos a pedido do Mário (0, 9, @), com o mesmo tremor controlado."""

    def __init__(self, jitter: HandJitter | None = None):
        self.jitter = jitter or HandJitter(amplitude=3.0)

    def build(self, name: str, unicodes: list[int]) -> GlyphSkeleton:
        strokes = [self.jitter.apply(RecipeReader.stroke(it), name) for it in R.REDRAW[name]]
        g = GlyphSkeleton(name, unicodes, strokes)
        b = g.bounds()
        g.advance = b[2] - b[0]
        return g


class GlyphCorrections:
    """Ajustes pontuais pedidos pelo Mário depois das provas (reprodutíveis, em código)."""

    E_MIDDLE_RATIO = 0.72  # barra do meio do E: ~72% da largura (antes ~35%, parecia '[')

    def __init__(self, base: SkeletonStore, jitter: HandJitter | None = None):
        self.base = base
        self.jitter = jitter or HandJitter(amplitude=3.0)

    def all(self) -> list[GlyphSkeleton]:
        return [self.longer_e_middle()]

    def longer_e_middle(self) -> GlyphSkeleton:
        g = self.base.load("E")
        width = g.bounds()[2] - g.bounds()[0]

        def is_middle(s: Stroke) -> bool:
            p = s.sample(12)
            return 250 < p[:, 1].mean() < 500 and np.ptp(p[:, 1]) < 60

        strokes = []
        for s in g.strokes:
            if is_middle(s):
                x0, y0 = s.segments[0].p0
                x1 = g.bounds()[0] + self.E_MIDDLE_RATIO * width
                s = self.jitter.apply(SkeletonPen.spline([(x0, y0), (x0 + 0.4 * (x1 - x0), y0 + 8), (x1, y0 + 4)]),
                                      "Emid")
            strokes.append(s)
        return GlyphSkeleton("E", list(g.unicodes), strokes, g.advance)


class LayerStack:
    """Consulta várias camadas de esqueletos; a primeira que tiver o glifo vence."""

    def __init__(self, stores: list[SkeletonStore]):
        self.stores = stores

    def has(self, name: str) -> bool:
        return any(s.exists(name) for s in self.stores)

    def get(self, name: str) -> GlyphSkeleton:
        for s in self.stores:
            if s.exists(name):
                return s.load(name)
        raise KeyError(name)


class DeriveRun:
    """Gera as camadas derivadas: common/ (as duas famílias), print/ (Petricor), cursive/ (Caligrafia)."""

    REDRAW_UNICODES = {"zero": [0x30], "nine": [0x39], "at": [0x40]}

    def __init__(self, base_dir, common_dir, print_dir, cursive_dir):
        self.base = SkeletonStore(base_dir)
        self.common = SkeletonStore(common_dir)
        self.print = SkeletonStore(print_dir)
        self.cursive = SkeletonStore(cursive_dir)
        self.count: dict[str, int] = {}

    def _save(self, store: SkeletonStore, g: GlyphSkeleton) -> None:
        if store.exists(g.name) and store.load(g.name).locked:
            return  # editado à mão: preserva
        store.save(g)
        key = store.folder.name
        self.count[key] = self.count.get(key, 0) + 1

    def run(self) -> dict:
        self._letters()
        self._accents_and_extras()
        return dict(self.count)

    def _letters(self) -> None:
        for g in GlyphCorrections(self.base).all():
            self._save(self.common, g)
        redraw = RedrawBuilder()
        for name, uni in self.REDRAW_UNICODES.items():
            self._save(self.common, redraw.build(name, uni))
        printer = PrintBuilder(self.base)
        for letter in printer.names():
            self._save(self.print, printer.build(letter))
        cursive = CursiveBuilder()
        for letter in R.CURSIVE:
            self._save(self.cursive, cursive.build(letter))
            self._save(self.cursive, cursive.build(letter, high_entry=True))

    def _accents_and_extras(self) -> None:
        import glyphsets

        from .accents import MARKS, SPACING_MARKS, AccentCatalog, MarkBuilder, SpacingMarkBuilder
        from .extras import ExtraBuilder

        marks = MarkBuilder(self.base)
        for spec in MARKS:
            self._save(self.common, marks.build(spec))
        for u in SPACING_MARKS:
            self._save(self.common, SpacingMarkBuilder.build(u))
        common_stack = LayerStack([self.common, self.base])
        for g in ExtraBuilder(common_stack.get).common():
            self._save(self.common, g)
        print_stack = LayerStack([self.print, self.common, self.base])
        for layer, cursive in ((self.print, False), (self.cursive, True)):
            stack = LayerStack([layer, self.common, self.base])
            for g in ExtraBuilder(stack.get).family(cursive, stack.has, print_stack.get):
                self._save(layer, g)
        catalog = AccentCatalog()
        composites = catalog.composites(sorted(glyphsets.unicodes_per_glyphset("GF_Latin_Core")))
        for g in composites:
            self._save(self.common, g)
        cursive_stack = LayerStack([self.cursive, self.common, self.base])
        for g in catalog.high_variants(composites, cursive_stack.has):
            self._save(self.cursive, g)
