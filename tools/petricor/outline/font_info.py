"""Metadados da fonte (nomes, licença, métricas verticais) — regras do GF Guide."""
from __future__ import annotations

from dataclasses import dataclass

from ..design.metrics import DEFAULT_METRICS, Metrics

REPO_URL = "https://github.com/marioluciofjr/petricor"
YEAR = 2026


@dataclass(frozen=True)
class FontInfo:
    family: str
    metrics: Metrics = DEFAULT_METRICS
    version: tuple[int, int] = (1, 0)
    designer: str = "Mario Lucio"
    designer_url: str = "https://github.com/marioluciofjr"

    @property
    def copyright(self) -> str:
        # formato exigido: "Copyright {ano} The {família} Project Authors ({url do git})"
        return f"Copyright {YEAR} The Petricor Project Authors ({REPO_URL})"

    LICENSE = ("This Font Software is licensed under the SIL Open Font License, Version 1.1. "
               "This license is available with a FAQ at: https://openfontlicense.org")
    LICENSE_URL = "https://openfontlicense.org"

    def apply(self, ufo, style: str, weight: int, win: tuple[int, int]) -> None:
        """Preenche o fontinfo do UFO."""
        m, i = self.metrics, ufo.info
        i.familyName, i.styleName = self.family, style
        i.versionMajor, i.versionMinor = self.version
        i.unitsPerEm = m.upm
        i.capHeight, i.xHeight = m.cap_height, m.x_height
        i.ascender, i.descender = m.typo_ascender, m.typo_descender
        i.openTypeOS2TypoAscender, i.openTypeOS2TypoDescender, i.openTypeOS2TypoLineGap = \
            m.typo_ascender, m.typo_descender, 0
        i.openTypeHheaAscender, i.openTypeHheaDescender, i.openTypeHheaLineGap = \
            m.typo_ascender, m.typo_descender, 0
        i.openTypeOS2WinAscent, i.openTypeOS2WinDescent = win
        i.openTypeOS2Selection = [7]  # USE_TYPO_METRICS
        i.openTypeOS2WeightClass = weight
        i.openTypeOS2Type = []  # fsType 0: instalável
        i.copyright = self.copyright
        i.openTypeNameLicense, i.openTypeNameLicenseURL = self.LICENSE, self.LICENSE_URL
        i.openTypeNameDesigner, i.openTypeNameDesignerURL = self.designer, self.designer_url
        i.openTypeNameManufacturerURL = REPO_URL
