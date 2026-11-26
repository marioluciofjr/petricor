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


class DeriveRun:
    """Gera as camadas derivadas: redraw/, print/ (Petricor) e cursive/ (Caligrafia)."""

    REDRAW_UNICODES = {"zero": [0x30], "nine": [0x39], "at": [0x40]}

    def __init__(self, base_dir, redraw_dir, print_dir, cursive_dir):
        self.base = SkeletonStore(base_dir)
        self.stores = {"redraw": SkeletonStore(redraw_dir), "print": SkeletonStore(print_dir),
                       "cursive": SkeletonStore(cursive_dir)}

    def _save(self, layer: str, g: GlyphSkeleton) -> None:
        store = self.stores[layer]
        if store.exists(g.name) and store.load(g.name).locked:
            return  # editado à mão: preserva
        store.save(g)

    def run(self) -> dict:
        redraw = RedrawBuilder()
        for name, uni in self.REDRAW_UNICODES.items():
            self._save("redraw", redraw.build(name, uni))
        printer = PrintBuilder(self.base)
        for letter in printer.names():
            self._save("print", printer.build(letter))
        cursive = CursiveBuilder()
        for letter in R.CURSIVE:
            self._save("cursive", cursive.build(letter))
            self._save("cursive", cursive.build(letter, high_entry=True))
        return {"redraw": len(self.REDRAW_UNICODES), "print": len(printer.names()), "cursive": 2 * len(R.CURSIVE)}
