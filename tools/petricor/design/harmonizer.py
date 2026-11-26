"""Harmonização LEVE: alinha alturas e proporções sem apagar a mão do Mário.

Para cada glifo escolhemos uma REGRA conforme a sua classe:
- ZoneFit: estica/encolhe na vertical até as linhas-alvo (ex.: base e
  altura-x). A largura acompanha só metade da correção individual, para
  a letra não ficar 'espremida' nem 'esticada' demais.
- Shift: só desloca na vertical (pontuação), mantendo o tamanho original.
Os pingos (i, j) não entram na medição, mas acompanham a transformação.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np

from ..model import GlyphSkeleton, Stroke
from .metrics import DEFAULT_METRICS, Metrics


@dataclass(frozen=True)
class Extent:
    lo: float
    hi: float
    xmin: float

    @classmethod
    def of(cls, strokes: list[Stroke]) -> "Extent":
        pts = np.vstack([s.sample(24) for s in strokes])
        return cls(float(pts[:, 1].min()), float(pts[:, 1].max()), float(pts[:, 0].min()))


class Rule(ABC):
    """Estratégia de harmonização de uma classe de glifos."""

    @abstractmethod
    def mapping(self, ext: Extent, class_scale: float) -> tuple[float, float, float, float]:
        """Devolve (sx, sy, y_from, y_to): y' = y_to + (y − y_from)·sy; x' = (x − xmin)·sx."""


@dataclass(frozen=True)
class ZoneFit(Rule):
    lo: float
    hi: float

    def mapping(self, ext, class_scale):
        sy = (self.hi - self.lo) / max(ext.hi - ext.lo, 1e-6)
        # largura: escala da classe inteira + metade da correção individual
        sx = class_scale * (sy / class_scale) ** 0.5
        return sx, sy, ext.lo, self.lo


@dataclass(frozen=True)
class Shift(Rule):
    """Mantém o tamanho e alinha um ponto de referência ('bottom', 'top' ou 'center')."""

    anchor: str
    y: float

    def mapping(self, ext, class_scale):
        ref = {"bottom": ext.lo, "top": ext.hi, "center": (ext.lo + ext.hi) / 2}[self.anchor]
        return class_scale, class_scale, ref, self.y


class GlyphClassifier:
    """Decide a regra de cada glifo a partir das métricas-alvo."""

    def __init__(self, m: Metrics = DEFAULT_METRICS):
        o = m.overshoot
        cap, rnd = ZoneFit(0, m.cap_height), ZoneFit(-o, m.cap_height + o)
        xh, asc = ZoneFit(0, m.x_height), ZoneFit(0, m.ascender)
        desc = ZoneFit(m.descender, m.x_height)
        self.rules: dict[str, Rule] = {}
        self.rules.update({c: cap for c in "ABDEFHIJKLMNPRTUVWXYZ"})
        self.rules.update({c: rnd for c in "CGOQS"})
        self.rules.update({c: xh for c in "acemnorsuvwxzi"})
        self.rules.update({c: asc for c in "bdhkl"})
        self.rules.update({c: desc for c in "gpqyj"})
        self.rules["f"] = ZoneFit(m.descender, m.ascender)
        self.rules["t"] = ZoneFit(0, m.t_height)
        digits = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
        self.rules.update({d: ZoneFit(0, m.digit_height) for d in digits})
        self.rules.update({n: ZoneFit(0, m.cap_height) for n in
                           ["ampersand", "Euro", "sterling", "yen", "numbersign", "percent"]})
        self.rules["dollar"] = ZoneFit(-80, m.cap_height + 80)
        self.rules["at"] = ZoneFit(-110, m.cap_height - 60)
        for n in ["parenleft", "parenright", "bracketleft", "bracketright", "braceleft", "braceright", "bar"]:
            self.rules[n] = ZoneFit(m.paren_bottom, m.paren_top)
        for n in ["plus", "multiply", "divide", "equal", "less", "greater", "asciitilde"]:
            self.rules[n] = Shift("center", m.math_axis)
        self.rules["hyphen"] = Shift("center", m.hyphen_axis)
        self.rules["underscore"] = Shift("center", m.underscore_axis)
        for n in ["quotesingle", "quotedbl", "degree", "asterisk"]:
            self.rules[n] = Shift("top", m.cap_height)
        for n in ["period", "exclam", "question", "colon", "slash", "backslash"]:
            self.rules[n] = Shift("bottom", 0)
        for n in ["comma", "semicolon"]:
            self.rules[n] = None  # tratados por deslocamento fixo (ver Harmonizer)
        self.metrics = m

    def rule_for(self, name: str) -> Rule | None:
        return self.rules.get(self.base_name(name))

    @staticmethod
    def base_name(name: str) -> str:
        """'a.hi' → 'a' (variantes usam as regras da letra-base)."""
        return name.split(".")[0]

    def sitting_offset(self) -> float:
        return self.metrics.sitting_offset

    def zones_for(self, name: str) -> list[tuple[float, int]]:
        """Linhas de referência do glifo: (y visual, sentido).

        sentido +1 = linha de BAIXO (a linha central sobe meia caneta);
        sentido −1 = linha de CIMA (a linha central desce meia caneta).
        Usado pelo WeightProfile para a borda cair na linha em todo peso.
        """
        m = self.metrics
        base, xh, asc, desc = m.baseline, m.x_height, m.ascender, m.descender
        special = {
            **{c: [(base, 1), (xh, -1)] for c in "acemnorsuvwxzi"},
            **{c: [(base, 1), (xh, -1), (asc, -1)] for c in "bdhkl"},
            **{c: [(desc, 1), (base, 1), (xh, -1)] for c in "gpqyj"},
            "f": [(desc, 1), (base, 1), (xh, -1), (asc, -1)],
            "t": [(base, 1), (xh, -1), (m.t_height, -1)],
        }
        name = self.base_name(name)
        if name in special:
            return special[name]
        rule = self.rule_for(name)
        if isinstance(rule, ZoneFit):
            return [(rule.lo, 1), (rule.hi, -1)]
        if isinstance(rule, Shift):
            return {"bottom": [(rule.y, 1)], "top": [(rule.y, -1)], "center": []}[rule.anchor]
        return [(base, 1)]  # vírgula e ponto e vírgula: pousam na base


class Harmonizer:
    # proporção média das classes: medida nas folhas (alvo ÷ medido)
    def __init__(self, classifier: GlyphClassifier | None = None):
        self.classifier = classifier or GlyphClassifier()

    @staticmethod
    def main_strokes(g: GlyphSkeleton) -> list[Stroke]:
        """Ignora pingos (traços minúsculos acima do resto) na medição."""
        if len(g.strokes) < 2:
            return g.strokes
        exts = [Extent.of([s]) for s in g.strokes]
        heights = [e.hi - e.lo for e in exts]
        tallest = max(heights)
        body_top = max(e.hi for e, h in zip(exts, heights) if h > 0.3 * tallest)
        keep = [s for s, e, h in zip(g.strokes, exts, heights) if not (h < 0.25 * tallest and e.lo > body_top - 10)]
        return keep or g.strokes

    def class_scales(self, glyphs: list[GlyphSkeleton]) -> dict[Rule, float]:
        """Escala típica de cada regra (mediana), para preservar proporções da classe."""
        per_rule: dict = {}
        for g in glyphs:
            rule = self.classifier.rule_for(g.name)
            if isinstance(rule, ZoneFit) and g.strokes:
                e = Extent.of(self.main_strokes(g))
                per_rule.setdefault(rule, []).append((rule.hi - rule.lo) / max(e.hi - e.lo, 1e-6))
        return {r: float(np.median(v)) for r, v in per_rule.items()}

    def harmonize(self, g: GlyphSkeleton, class_scales: dict) -> GlyphSkeleton:
        if not g.strokes:
            return g
        rule = self.classifier.rule_for(g.name)
        ext = Extent.of(self.main_strokes(g))
        sitting = self.classifier.sitting_offset()
        if rule is None:  # vírgula e ponto e vírgula: só descontam a 'flutuação' da escrita
            sx, sy, y_from, y_to = 1.0, 1.0, 0.0, -sitting
        else:
            sx, sy, y_from, y_to = rule.mapping(ext, class_scales.get(rule, 1.0))
        xmin = Extent.of(g.strokes).xmin

        def fn(p):
            return ((p[0] - xmin) * sx, y_to + (p[1] - y_from) * sy)

        out = g.transformed(fn)
        b = out.bounds()
        out.advance = b[2] - b[0]
        return out
