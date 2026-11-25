# AGENTS — instruções para agentes de IA

## Contexto
Repositório da fonte **Petricor**, feita a partir da caligrafia do Mário e destinada ao Google Fonts. Comunicação com o Mário em português do Brasil, de forma objetiva e didática.

## Comandos
| Ação | Comando |
|---|---|
| Python do projeto | `.\.venv\Scripts\python.exe` (Python 3.13; nunca use o 3.14 global) |
| Testes | `.\.venv\Scripts\python.exe -m pytest tests -q` |
| Pipeline completo | `.\.venv\Scripts\python.exe -m petricor all` |
| Uma etapa | `... -m petricor <scan\|trace\|harmonize\|compose\|masters\|build\|qa\|proof>` |

## Regras
1. **TDD**: escreva ou ajuste o teste antes do código.
2. **OOP** com alta coesão e baixo acoplamento; respeite a regra de dependência do ARCHITECTURE.md.
3. Comentários didáticos em PT-BR no código.
4. **Fonte da verdade = `sources/skeletons/*.json`.** Nunca edite `sources/masters/*.ufo` nem `fonts/` à mão: eles são gerados.
5. Antes de cada commit: testes verdes, `TASKS.md` e `TRACEABILITY.md` atualizados e specs afetadas revisadas.
6. Mensagens de commit em português, no imperativo.
7. **Nunca** publique (push, criar repositório, abrir issue) sem confirmação explícita do Mário.
8. Não altere as métricas verticais depois da primeira publicação.
9. Os nomes de glifos seguem as convenções do AGL/Glyphs (ex.: `aacute`, `quotedblleft`, `a.hi`).

## Limites
- Não reescreva a forma das letras além da harmonização **leve** sem aprovação do Mário.
- Mudanças de desenho grandes passam por prova visual em `proofs/`.
