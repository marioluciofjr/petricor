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
- 🔄 T14 Correções glifo a glifo (feito: vazamento da guia no `>`/`<`/`|`, pingos falsos, espora do `E`; aguardando revisão do Mário)
- 🔄 T15 `StrokeExpander` + compensação por zonas ✅ · Prova 2 `proofs/prova2-harmonizacao.png` aguardando aprovação ⛳

## Fase 4 — Cursiva conectada
- ⏳ T16 `CursiveJoiner` (junção baixa/alta, variantes `.hi`)
- ⏳ T17 `FeatureWriter` (`calt`) + Prova 3

## Fase 5 — Glifos faltantes
- ⏳ T18 `AccentDesigner` (marcas combinantes no estilo)
- ⏳ T19 `Composer` (âncoras, compostos, GF Latin Core 100%)
- ⏳ T20 Sinais extras (aspas curvas, travessões, ^, `, … etc.) + Prova 4

## Fase 6 — Pesos ⛳
- ⏳ T21 Masters Thin/Regular/Black + checagem de autointerseção
- ⏳ T22 `DesignspaceWriter` (eixo, 9 instâncias, STAT) + Prova 5 ⛳

## Fase 7 — Build e QA
- ⏳ T23 `Spacer` + `Kerner` + figuras tabulares (`tnum`)
- ⏳ T24 `config.yaml` + `GfBuilder` (VF, estáticas, webfonts)
- ⏳ T25 `QaRunner` (Fontspector) até zerar FAIL/FATAL

## Fase 8 — Documentação
- ⏳ T26 OFL.txt, AUTHORS.txt, CONTRIBUTORS.txt, README raiz com imagem
- ⏳ T27 CI `.github/workflows/build.yaml` + `proofs/index.html`

## Fase 9 — Publicação ⛳
- ⏳ T28 Criar repositório público e dar push ⛳
- ⏳ T29 Mário assina o CLA do Google ⛳
- ⏳ T30 Abrir a issue "Add Petricor" no google/fonts ⛳
