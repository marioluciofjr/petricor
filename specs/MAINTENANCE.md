# MAINTENANCE — cuidados depois de pronto

Distribuição do esforço: **50% evolutiva · 30% adaptativa · 20% preventiva**.

## Evolutiva (50%)
- Ampliar a cobertura: Latin Plus, vietnamita e símbolos extras.
- Criar alternativas estilísticas (pedidas como famílias irmãs, regra do GF).
- Refinar o kerning e as conexões com base no retorno das pessoas usuárias.
- Cada evolução segue o versionamento do GF: novos glifos = +0.010 (ex.: 1.010 → 1.020); novo conjunto de caracteres = +0.100.

## Adaptativa (30%)
- Atualizar gftools, fontmake e Fontspector quando o Google mudar os requisitos.
- Reler o GF Guide a cada versão e ajustar `tests/contract`.
- Manter compatibilidade com novas versões de Python (testar o venv novo antes de trocar).

## Preventiva (20%)
- CI do GitHub roda build + Fontspector a cada push.
- Testes de regressão visual bloqueiam mudanças não intencionais.
- **Nunca mudar métricas verticais** depois de publicado (o GF proíbe).
- Revisar dependências a cada 6 meses.

## Incidentes e fallback
| Situação | Ação |
|---|---|
| Build quebra após atualizar ferramenta | Fixar a versão anterior no `requirements.txt` e abrir tarefa |
| Glifo com falha relatado | Corrigir o JSON do esqueleto, adicionar teste de regressão e lançar patch (+0.001) |
| Google pede mudanças na revisão | Abrir tarefas no TASKS.md, responder na issue |
