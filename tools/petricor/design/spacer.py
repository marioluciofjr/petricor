"""Espaçamento lateral (sidebearings): o 'ar' à esquerda e à direita de cada glifo.

Versão inicial por grupos; o ajuste fino (e o kerning) entra na Fase 7.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..model import Cubic


@dataclass(frozen=True)
class SpacingRule:
    left: float
    right: float


class Spacer:
    def __init__(self):
        caps, lower, digit, punct = SpacingRule(55, 55), SpacingRule(30, 30), SpacingRule(45, 45), SpacingRule(45, 45)
        self.rules = {}
        self.rules.update({c: caps for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"})
        self.rules.update({c: lower for c in "abcdefghijklmnopqrstuvwxyz"})
        for n in ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]:
            self.rules[n] = digit
        # o gancho do j de forma passa por baixo da letra anterior (lado esquerdo negativo)
        self.rules["j"] = SpacingRule(-45, 30)
        self.default = punct
        self.space_width = 260

    def rule_for(self, name: str) -> SpacingRule:
        return self.rules.get(name, self.default)

    def space(self, glyph, prof):
        """Desloca os contornos para lsb e define o avanço = lsb + largura + rsb."""
        b = glyph.bounds()
        if b is None:
            # espaço cresce com a caneta: letras mais gordas pedem mais ar entre palavras
            glyph.advance = self.space_width - 30 + 0.6 * prof.pen
            return glyph
        if any(k.startswith("_") for k in glyph.anchors):
            glyph.advance = 0.0  # acento combinante: largura zero, centrado na âncora
            return glyph
        if "exit" in glyph.anchors:
            # cursiva conectada: sem 'ar' lateral; a largura vai da entrada até a saída,
            # então a saída desta letra coincide com a entrada da próxima
            glyph.advance = glyph.anchors["exit"][0] - glyph.anchors.get("entry", (0, 0))[0]
            return glyph
        rule = self.rule_for(glyph.name)
        dx = rule.left - b[0]
        glyph.contours = [[Cubic(*[(p[0] + dx, p[1]) for p in (c.p0, c.p1, c.p2, c.p3)]) for c in cont]
                          for cont in glyph.contours]
        glyph.anchors = {k: (v[0] + dx, v[1]) for k, v in glyph.anchors.items()}
        glyph.advance = rule.left + (b[2] - b[0]) + rule.right
        return glyph
