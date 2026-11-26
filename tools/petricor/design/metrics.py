"""Métricas-alvo da Petricor (Value Object único para todo o projeto).

Todos os valores são VISUAIS: onde a borda do traço deve ficar.
O esqueleto harmonizado é guardado nessas coordenadas; em cada peso,
o WeightProfile empurra a linha central para dentro em meia espessura,
para que a borda caia exatamente nestas linhas em qualquer peso.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Metrics:
    upm: int = 1000
    baseline: float = 0
    x_height: float = 430
    cap_height: float = 700
    ascender: float = 720
    descender: float = -230
    t_height: float = 600
    digit_height: float = 680
    overshoot: float = 10
    math_axis: float = 300       # centro de + − × ÷ = < > ~
    hyphen_axis: float = 250
    paren_top: float = 760
    paren_bottom: float = -140
    underscore_axis: float = -120
    sitting_offset: float = 20   # a escrita "flutua" ~20 un acima da guia impressa

    # Métricas verticais da fonte (regras do GF: typo = hhea, lineGap 0,
    # maiúsculas centralizadas: ascender − capHeight = |descender|)
    @property
    def typo_ascender(self) -> int:
        return 1000

    @property
    def typo_descender(self) -> int:
        return -300


DEFAULT_METRICS = Metrics()
