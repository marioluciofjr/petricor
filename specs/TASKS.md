# TASKS — o que fazer agora

Legenda: ✅ feito · 🔄 em andamento · ⏳ pendente · ⛳ requer aprovação do Mário

## Fase 1 — Fundação
- ✅ T01 `git init`, estrutura de pastas, folhas movidas para `sources/scans/`
- ✅ T02 venv Python 3.13 + `requirements.txt`
- ✅ T03 Verificar disponibilidade do nome "Petricor" (google/fonts e GitHub: livre)
- ✅ T04 Ler GF Guide atualizado (Fontspector, VF-only, issue + CLA)
- ✅ T05 Escrever as 12 specs
- ✅ T06 Esqueleto de `tests/` + `pytest` rodando + pacote `tools/petricor`

## Fase 2 — Digitalização
- ✅ T07 `SheetLayout` (mapa célula → caractere das duas folhas)
- ✅ T08 `SheetLoader` + ajuste de grade regular (substitui o `RegistrationAligner`: a grade ajustada já corrige a rotação)
- ✅ T09 `GridSlicer` + `InkExtractor` (tinta × guias ciano por matiz HSV; ponte sobre as guias; linha de base da célula)
- ✅ T10 `Skeletonizer` + `StrokeTracer` + `BezierFitter`
- ✅ T11 `SkeletonStore` (JSON) + comando `trace` (escala: maiúsculas 174 px = 700 un)
- ✅ T12 Prova 1 (original × vetorizado) → `proofs/prova1-vetorizacao.png`

## Fase 3 — Harmonização ⛳
- ✅ T13 `Metrics` + `Harmonizer` (alturas por classe, largura acompanha metade da correção; inclinação medida ≈ 0, não aplicada)
- ✅ T14 Correções glifo a glifo (vazamento da guia no `>`/`<`/`|`, pingos falsos, espora do `E`)
- ✅ T15 `StrokeExpander` + compensação por zonas · Prova 2 revisada pelo Mário ⛳ → pediu: harmonizar mais a cursiva, refazer 0/9/@, criar família não cursiva
- ✅ T15a Camadas de esqueleto por família (`print/`, `cursive/`, `redraw/` sobre a base) + `FamilySpec`
- ✅ T15b `SkeletonPen` + `HandJitter` + redesenho de `0`, `9`, `@`
- ✅ T15c `PrintBuilder`: minúsculas de forma (receitas + S/V/W reduzidas + x/y/z da mão do Mário)
- ✅ T15e Cursivas redesenhadas como traço contínuo com junção padrão (baixa 110 a 35°; alta 330) + variantes `.hi` (antecipa T16)
- ✅ T15d Prova 2b aprovada pelo Mário ("ficou muito boa") ⛳, com o pedido de acentos (Fase 5)

## Fase 4 — Cursiva conectada
- ✅ T16 Junção baixa/alta e variantes `.hi` (feito em T15e: `CursiveBuilder`)
- ⏳ T17 `FeatureWriter` (`calt`) + Prova 3

## Fase 5 — Glifos faltantes
- ✅ T18 `MarkBuilder`: 14 acentos combinantes + `caroncomb.alt` (ď ľ ť Ľ) + `commaturnedabovecomb` (ģ); til do `~`, anel do `°`, vírgula da `,` do Mário
- ✅ T19 `AccentCatalog` + `AnchorCalculator` + `Composer` + `MasterGlyphSet`: 145 acentuados + variantes `.hi` da Caligrafia; **GF Latin Core 100% nas duas famílias** (teste de contrato)
- ✅ T20 `ExtraBuilder`: 62 extras (aspas curvas, travessões, « », ¡ ¿, © ®, Æ Œ Ø Ð Þ Ħ Ł ẞ, æ œ ø ð þ ß ı ȷ ł ħ đ, ª º ¢ …) + algarismos tabulares `.tf` · Prova 4 `proofs/prova4-acentos.png`

## Fase 6 — Pesos ⛳
- ✅ T20a Pedidos do Mário: `o` cursivo refeito (não parece `a`); barra do meio do `E` em 72% da largura (não parece `[`)
- ✅ T21 Masters Thin/Regular/Black (`MasterBuilder`); divisão em cápsulas decidida no esqueleto original → masters compatíveis (teste de integração)
- ✅ T22 Designspace + VFs compiladas com fontmake · Prova 5 aprovada ⛳ (renderizada da VF via HarfBuzz)
- ✅ T22a `o` cursivo com laçadinha grande + `LoopInflation` (laço cresce com o peso); aprovado pelo Mário
- ✅ T22b Caligrafia limitada a 100–600 (Thin a SemiBold), Petricor 100–900 (`FamilySpec.max_wght`, contrato `test_weights.py`)

## Fase 7 — Build e QA
- ✅ T23 `Kerner` óptico automático com grupos (acentuados herdam) + `tnum`; espaço cresce com o peso; sinais matemáticos com largura igual
- ✅ T24 `sources/config.yaml` + gftools builder: VFs, 15 TTF com hinting, OTF, WOFF2 em `fonts/`
- ✅ T25 Fontbakery 1.1 (perfil googlefonts): **0 FAIL** nas duas famílias; WARNs justificados em TESTS.md
- ✅ T25a Pedidos do Mário: 5 alinhado aos demais algarismos (bug do "pingo" na harmonização); cifrão refeito

## Fase 8 — Documentação
- ✅ T26 OFL.txt (modelo GF), AUTHORS.txt, CONTRIBUTORS.txt, README raiz com espécimes (`documentation/`)
- ✅ T27 CI `.github/workflows/build.yaml` (build + testes + fontbakery + artefato)

## Fase 9 — Publicação ⛳
- 🔄 T28 Repositório público criado (github.com/marioluciofjr/petricor) ✅ · push bloqueado: o login do `gh` não tem o escopo `workflow` → Mário roda `gh auth refresh -h github.com -s workflow` ⛳
- ⏳ T29 Mário assina o CLA individual do Google (cla.developers.google.com) ⛳
- ⏳ T30 Abrir a issue "Add Petricor" no google/fonts (texto pronto, com declaração de uso de IA exigida pelo modelo) ⛳
- ✅ T30a Nome verificado: namecheck.fontdata.com e DaFont sem fontes "Petricor"/"Petricor Caligrafia"
