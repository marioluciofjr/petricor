# Specs da Petricor — porta de entrada

Esta pasta guarda os documentos que explicam o projeto. Leia nesta ordem:

| Pergunta | Documento |
|---|---|
| Por que o projeto existe? | [PRD.md](PRD.md) |
| Como funciona por dentro? | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Como a fonte deve parecer? | [DESIGN.md](DESIGN.md) |
| O que fazer agora? | [TASKS.md](TASKS.md) e [WORKFLOW.md](WORKFLOW.md) |
| Como validar? | [TESTS.md](TESTS.md) |
| O que significa cada termo? | [GLOSSARY.md](GLOSSARY.md) |
| Requisito → tarefa → código → teste | [TRACEABILITY.md](TRACEABILITY.md) |
| Regras para agentes de IA | [AGENTS.md](AGENTS.md) |
| Cuidados depois de pronto | [MAINTENANCE.md](MAINTENANCE.md) |
| Quem decide o quê | [GOVERNANCE.md](GOVERNANCE.md) |

## Começar em 4 passos (Windows)
```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest tests
.\.venv\Scripts\python.exe -m petricor all
```
O resultado aparece em `fonts/` e as provas visuais, em `proofs/`.

## Onde ficam as coisas
- `sources/scans/`: folhas originais escritas pelo Mário.
- `sources/skeletons/`: um JSON por letra; é aqui que se corrige o desenho.
- `tools/petricor/`: o código do pipeline.
- `fonts/`: as fontes geradas (não edite à mão).
