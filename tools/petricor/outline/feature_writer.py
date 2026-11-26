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

    # Sem declarar 'latn', as regras geradas (mark, kern) ficariam só no script DFLT,
    # e o HarfBuzz/navegadores não as aplicariam a texto latino.
    LANGUAGE_SYSTEMS = "languagesystem DFLT dflt;\nlanguagesystem latn dflt;"

    def write(self) -> str:
        parts = (self.LANGUAGE_SYSTEMS, self._classes(), self._ccmp(), self._calt(), self._tnum())
        return "\n\n".join(p for p in parts if p) + "\n"

    BOTTOM_MARKS = ("commaaccentcomb", "cedillacomb", "ogonekcomb")

    def _classes(self) -> str:
        top = sorted(GlyphNamer.name(u) for u in TOP_MARKS if GlyphNamer.name(u) in self.names)
        bottom = [m for m in self.BOTTOM_MARKS if m in self.names]
        return f"@TopMarks = [{' '.join(top)}];\n@BottomMarks = [{' '.join(bottom)}];"

    def _ccmp(self) -> str:
        """Letras de pingo (i, j, į) perdem o pingo quando recebem acento em cima,
        mesmo que haja um acento embaixo no meio (ex.: lituano 'į́', 'i̦̇')."""
        candidates = (("i", "idotless"), ("j", "jdotless"), ("i.hi", "idotless.hi"), ("j.hi", "jdotless.hi"),
                      ("iogonek", "iogonek.dotless"), ("iogonek.hi", "iogonek.dotless.hi"))
        pairs = [(s, d) for s, d in candidates if s in self.names and d in self.names]
        if not pairs:
            return ""
        src = " ".join(s for s, _ in pairs)
        dst = " ".join(d for _, d in pairs)
        return (f"feature ccmp {{\n  sub [{src}]' @TopMarks by [{dst}];\n"
                f"  sub [{src}]' @BottomMarks @TopMarks by [{dst}];\n}} ccmp;")

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
