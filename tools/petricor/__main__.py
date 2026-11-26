"""Permite rodar `python -m petricor <etapa>` (com tools/ no PYTHONPATH)."""
from .cli import build_cli

build_cli().main()
