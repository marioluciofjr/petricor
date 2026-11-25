# TESTS — como a Petricor é validada (TDD)

## Ciclo
**Vermelho → Verde → Refatorar.** Primeiro um teste que falha descrevendo o comportamento, depois o código mínimo para passar e, por fim, a limpeza.

## Suítes
| Pasta | O que garante | Exemplos |
|---|---|---|
| `tests/unit` | Cada classe isolada | alinhamento por marcas de registro; recorte da grade; separação tinta × guia; tracer; erro máximo do ajuste Bézier; expansão com nº de pontos igual entre pesos |
| `tests/integration` | Etapas encadeadas | folha → esqueleto de "A"; esqueletos → UFO; designspace interpolável (`fontTools.varLib`) |
| `tests/contract` | Requisitos do Google Fonts | GF Latin Core 100%; eixo `wght` 100–900; 9 instâncias; copyright/OFL; `calt`, `kern` e `tnum` presentes; métricas verticais; fsType 0 |
| `tests/e2e` | Pipeline inteiro | `petricor all` gera a VF e o Fontspector não aponta FAIL/FATAL |
| `tests/regression` | Nada piora sem querer | snapshot PNG por glifo/peso (tolerância de pixels); hash dos esqueletos aprovados |

## Como rodar
```powershell
.\.venv\Scripts\python.exe -m pytest tests -q              # tudo
.\.venv\Scripts\python.exe -m pytest tests/unit -q         # rápido
.\.venv\Scripts\python.exe -m pytest tests/e2e -q -m slow  # build completo
```

## Portão de publicação
1. Todas as suítes verdes.
2. `fontspector --profile googlefonts fonts/variable/Petricor[wght].ttf` sem FAIL/FATAL.
3. WARNs revisados e justificados abaixo.
4. Provas 2 e 5 aprovadas pelo Mário.

## WARNs aceitos (justificativa)
_(preenchido na Fase 7)_
