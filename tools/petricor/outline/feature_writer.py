"""Regras OpenType escritas à mão (o kerning e o 'mark' o ufo2ft gera sozinho).

- calt (Caligrafia): depois de letra que sai pela junção alta, troca a
  próxima minúscula pela variante .hi.
- ccmp: i/j + acento de cima → i/j sem pingo.
- tnum: algarismos tabulares.
"""
from __future__ import annotations

from ..design.accents import TOP_MARKS, GlyphNamer
from .composer import DIGITS


class FeatureWriter:
    def __init__(self, glyph_names: set[str], high_exit: set[str]):
        self.names = glyph_names
        self.high_exit = sorted(n for n in high_exit if n in glyph_names)

    def write(self) -> str:
        return "\n\n".join(p for p in (self._classes(), self._ccmp(), self._calt(), self._tnum()) if p) + "\n"

    def _classes(self) -> str:
        top = sorted(GlyphNamer.name(u) for u in TOP_MARKS if GlyphNamer.name(u) in self.names)
        return f"@TopMarks = [{' '.join(top)}];"

    def _ccmp(self) -> str:
        pairs = [(s, d) for s, d in (("i", "idotless"), ("j", "jdotless"), ("i.hi", "idotless.hi"),
                                      ("j.hi", "jdotless.hi")) if s in self.names and d in self.names]
        if not pairs:
            return ""
        src = " ".join(s for s, _ in pairs)
        dst = " ".join(d for _, d in pairs)
        return f"feature ccmp {{\n  sub [{src}]' @TopMarks by [{dst}];\n}} ccmp;"

    def _calt(self) -> str:
        hi = sorted(n for n in self.names if n.endswith(".hi") and n[:-3] in self.names)
        if not hi or not self.high_exit:
            return ""
        base = " ".join(n[:-3] for n in hi)
        return ("@HighExit = [" + " ".join(self.high_exit) + "];\n"
                f"@LowEntry = [{base}];\n@HighEntry = [{' '.join(hi)}];\n"
                "feature calt {\n  sub @HighExit @LowEntry' by @HighEntry;\n} calt;")

    def _tnum(self) -> str:
        figs = [d for d in DIGITS if d in self.names and f"{d}.tf" in self.names]
        if not figs:
            return ""
        return (f"feature tnum {{\n  sub [{' '.join(figs)}] by [{' '.join(f + '.tf' for f in figs)}];\n}} tnum;")
