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

## Verificação oficial
O Fontspector (binário Rust) foi bloqueado pelo controle de permissões local; usamos o **Fontbakery 1.1** (mesmo perfil `googlefonts`), num ambiente separado `.venv-qa` (conflita com o gftools). O CI do GitHub roda o mesmo.

Resultado (2026-11-25): **0 FAIL / 0 FATAL / 0 ERROR** nas duas famílias, rodando uma família por vez:
```powershell
.\.venv-qa\Scripts\fontbakery.exe check-googlefonts "fonts/variable/Petricor[wght].ttf" --ghmarkdown fonts/report/fontbakery-Petricor.md
```

FAILs corrigidos na Fase 7: regras `mark` só no script DFLT (faltava `languagesystem latn`); acentos soltos (´ ¨ …) marcados como marcas no GDEF; `winAscent` < 1000; métricas/eixos "inconsistentes" por checar as duas famílias juntas.
WARNs corrigidos: largura dos sinais matemáticos, texto do OFL, círculo pontilhado ◌, pingo do i/į com acentos (soft-dotted).

## WARNs aceitos (justificativa)
| WARN | Justificativa |
|---|---|
| `avar` ausente | A progressão do traço é linear por projeto (caneta 16 → 60 → 150); avar é recomendação, não requisito |
| Contornos sobrepostos | Fontes variáveis mantêm sobreposições (cápsulas da caneta); o gftools as remove nas estáticas |
| Imagens do ARTICLE | O ARTICLE é produzido pela equipe do Google Fonts na entrada da fonte |
| Subconjuntos do METADATA | O METADATA.pb é gerado pela equipe do Google Fonts |
| Shapes languages (TransLatin Arabic) | Só caracteres AUXILIARES fora do GF Latin Core (Ĕ Ĭ Ŀ…); escopo atual = Latin Core |
| Tabela `meta` | Opcional; pode ser adicionada numa versão futura |
| `achVendID` | Requer registro de um código de fabricante na Microsoft (opcional) |
