# ARCHITECTURE — Petricor

> **Como** o projeto é montado por dentro.

## 1. Visão geral: Pipes and Filters
```
[folhas JPEG] → scan → skeleton → design → outline → build → [Petricor[wght].ttf] → QA
                  │         │          │         │
                  └─────────┴──── sources/skeletons/*.json (fonte da verdade)
```
Cada etapa lê a saída da anterior e escreve um artefato em disco. Isso permite rodar, testar e corrigir uma etapa sem refazer as outras.

## 2. Pacotes (`tools/petricor/`)
| Pacote | Responsabilidade única | Classes principais |
|---|---|---|
| `scan` | Ler a folha, achar a grade (ajuste regular por mínimos quadrados, que absorve a rotação do scanner), recortar as células e isolar a tinta | `SheetLoader`, `GridSlicer`, `InkExtractor`, `InkThresholds`, `SheetLayout` |
| `skeleton` | Transformar a tinta em linhas centrais vetoriais | `Skeletonizer`, `StrokeTracer`, `BezierFitter`, `SkeletonStore` |
| `design` | Decisões tipográficas sobre o esqueleto | `Metrics`, `Harmonizer`, `AccentDesigner`, `Composer`, `Spacer`, `Kerner`, `CursiveJoiner` |
| `outline` | Esqueleto → contorno → UFO | `StrokeExpander` (`PieceSplitter`, `CubicOffsetter`, `CapBuilder`), `WeightProfile`, `ZoneCompensator`, `OutlineGlyphFactory`, `MasterBuilder`, `DesignspaceWriter`, `FeatureWriter` |
| `build` | Compilação, QA e provas | `TraceProof`, `HarmonizeProof`, `SpecimenRenderer`, `GlyphRasterizer`, `GfBuilder`, `QaRunner` |
| `cli.py` | Fachada de linha de comando | `PetricorCli` |

**Regra de dependência:** `scan → skeleton → design → outline → build`. Um pacote só importa pacotes à sua esquerda ou o módulo `model` (tipos compartilhados). O `cli` é o único que conhece todos.

## 3. Modelo de dados (`tools/petricor/model.py`)
- `Point(x, y)`: ponto em unidades de fonte (UPM 1000, y para cima).
- `Stroke`: lista de segmentos Bézier cúbicos contínuos (um traço de caneta).
- `GlyphSkeleton`: nome do glifo, unicode, lista de `Stroke`, largura de avanço, âncoras.
- Formato JSON em `sources/skeletons/<nome>.json` (legível e editável à mão).

## 4. Decisões técnicas (ADRs resumidos)
| ADR | Decisão | Motivo | Concessão |
|---|---|---|---|
| 01 | Esqueleto + expansão (e não contorno escaneado) | Traço de esferográfica é monolinear; 9 pesos saem de uma única fonte de verdade | Detalhes de pressão da caneta se perdem |
| 02 | Mesma estrutura de pontos em todos os masters | Requisito de interpolação da fonte variável | Contornos sobrepostos dentro do glifo |
| 03 | Contornos sobrepostos na VF | Remover sobreposições muda a estrutura por peso | Precisa da flag OVERLAP_SIMPLE (gftools aplica) |
| 04 | Masters Thin, Regular e Black | 3 masters controlam melhor a progressão do traço | Mais dados para manter |
| 05 | Fonte variável apenas para o Google Fonts | O GF gera as estáticas pela API | Estáticas ficam só no repo |
| 06 | Python 3.13 em venv | Wheels de skia-pathops/fontmake | Duas versões de Python na máquina |
| 07 | Conexão cursiva por altura de junção padrão + variantes `.hi` + `calt` | Funciona em qualquer app com suporte OpenType básico | Mais glifos alternativos |
| 08 | UFO como formato-fonte | Aceito pelo GF e gerado por código | Não editável no Glyphs sem conversão |

## 5. Fluxo de build
`python -m petricor all` = `scan` → `trace` → `harmonize` → `compose` → `masters` → `build` → `qa` → `proof`.
O `build` chama `gftools builder sources/config.yaml`, que usa fontmake e gera `fonts/variable/Petricor[wght].ttf`, `fonts/ttf/*.ttf` e `fonts/webfonts/*.woff2`.

## 6. Métricas verticais (alvo, confirmadas na Fase 2)
UPM 1000 · capHeight ≈ 700 · xHeight ≈ 450 · ascender 1000 · descender −300 · lineGap 0 · USE_TYPO_METRICS ligado · win = bounding box da família.
