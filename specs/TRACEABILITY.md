# TRACEABILITY — requisito → tarefa → código → teste

Nada é commitado sem conferir esta matriz.

| Requisito | Tarefas | Código | Testes | Status |
|---|---|---|---|---|
| RF01 Extrair caracteres das folhas | T07–T09 | `scan/layout.py`, `scan/loader.py`, `scan/grid.py`, `scan/ink.py` | `unit/test_scan_layout.py`, `unit/test_scan_ink.py`, `integration/test_scan_grid.py` | ✅ |
| RF02 Esqueleto vetorial editável | T10–T11 | `model.py`, `skeleton/skeletonizer.py`, `skeleton/tracer.py`, `skeleton/fitter.py`, `skeleton/store.py`, `skeleton/glyph_tracer.py`, `skeleton/sheet_tracer.py`, `cli.py` | `unit/test_skeleton.py`, `integration/test_trace.py` | ✅ |
| RF03 Harmonização leve | T13–T14 | `design/harmonizer.py`, `design/metrics.py`, `design/harmonize_run.py` | `unit/test_harmonizer.py`, `regression/` | 🔄 |
| RF04 Contornos 100–900 | T15, T21 | `outline/stroke_expander.py`, `outline/weight_profile.py`, `outline/glyph_factory.py` | `unit/test_stroke_expander.py`, `integration/test_interpolation.py` | 🔄 |
| RF05 Cursiva conectada | T16–T17 | `design/cursive_joiner.py`, `outline/feature_writer.py` | `contract/test_features.py` | ⏳ |
| RF06 Acentos e sinais | T18–T20 | `design/accent_designer.py`, `design/composer.py` | `contract/test_glyphset.py` | ⏳ |
| RF07 Espaçamento e kerning | T23 | `design/spacer.py`, `design/kerner.py` | `unit/test_spacer.py` | ⏳ |
| RF08 Algarismos tabulares | T23 | `design/composer.py`, `outline/feature_writer.py` | `contract/test_features.py` | ⏳ |
| RF09 Build em um comando | T24 | `build/gf_builder.py`, `sources/config.yaml` | `e2e/test_build.py` | ⏳ |
| RF10 Provas visuais | T12, T15, T17, T20, T22 | `build/trace_proof.py` (prova 1), `build/proof_renderer.py` | `regression/test_snapshots.py` | ⏳ |
| RF11 Repositório upstream | T26–T28 | raiz, `.github/` | `contract/test_repo_structure.py` | ⏳ |
| RF12 Issue no google/fonts | T30 | — | checklist manual | ⏳ |
| RNF01 OFL sem RFN | T26 | `OFL.txt` | `contract/test_license.py` | ⏳ |
| RNF04 Métricas verticais GF | T22 | `outline/master_builder.py` | `contract/test_vertical_metrics.py` | ⏳ |
| RNF03 TDD | T06 | `tests/` | `pytest` | 🔄 |
