# WORKFLOW — pipeline de trabalho e Implementation Plan

## Ciclo de cada tarefa
```
TASKS.md (escolher) → teste falhando → código → teste verde → prova visual (se mexe no desenho)
 → atualizar TASKS/TRACEABILITY/specs → git add + commit → próxima tarefa
```

## Pipeline técnico
```
sources/scans/*.jpeg
  └─ scan       → build/cells/<glifo>.png            (tinta isolada por célula)
  └─ trace      → sources/skeletons/<glifo>.json     (esqueleto bruto)
  └─ harmonize  → sources/skeletons/<glifo>.json     (métricas, suavização)
  └─ compose    → acentos, compostos, variantes .hi, âncoras
  └─ masters    → sources/masters/Petricor-{Thin,Regular,Black}.ufo + Petricor.designspace + features
  └─ build      → fonts/variable/Petricor[wght].ttf, fonts/ttf, fonts/webfonts
  └─ qa         → fonts/report/fontspector.md
  └─ proof      → proofs/*.png, proofs/index.html
```

## Implementation Plan (fases)
| Fase | Entrega | Aprovação |
|---|---|---|
| 1 Fundação | git, venv, specs, testes vazios, nome verificado | — |
| 2 Digitalização | esqueletos brutos de todos os caracteres; Prova 1 | — |
| 3 Harmonização | métricas e correções glifo a glifo; Prova 2 | ⛳ Mário |
| 4 Cursiva conectada | junções, `.hi`, `calt`; Prova 3 | — |
| 5 Glifos faltantes | acentos, sinais, GF Latin Core; Prova 4 | — |
| 6 Pesos | masters Thin/Regular/Black; Prova 5 | ⛳ Mário |
| 7 Build e QA | espaçamento, kerning, `tnum`, gftools, Fontspector sem FAIL | — |
| 8 Documentação | README raiz com imagem, AUTHORS, CONTRIBUTORS, OFL, CI | — |
| 9 Publicação | repo público → CI verde → issue "Add Petricor" | ⛳ Mário (cada ação) |

## Entrega no Google Fonts
1. Repositório público com a estrutura upstream (sources/, fonts/, documentation/, OFL.txt, AUTHORS.txt, CONTRIBUTORS.txt, README.md, requirements.txt).
2. O Mário assina o CLA do Google (cla.developers.google.com).
3. Issue em github.com/google/fonts com o template "Submit an OFL Font", título "Add Petricor" e link do repositório.
