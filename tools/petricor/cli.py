"""Fachada de linha de comando: `python -m petricor <etapa>`.

Cada etapa é um objeto Command com o método run(). A CLI só conhece os
comandos; os comandos conhecem as etapas (baixo acoplamento). Os
caminhos chegam por injeção (objeto Paths), o que facilita testar.
"""
from __future__ import annotations

import argparse
import json
from abc import ABC, abstractmethod
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class Paths:
    """Endereços do repositório (um só lugar para mudar)."""

    def __init__(self, root: Path = ROOT):
        self.root = root
        self.scans = root / "sources" / "scans"
        self.raw = root / "sources" / "skeletons" / "raw"
        self.skeletons = root / "sources" / "skeletons"
        self.proofs = root / "proofs"
        self.build_dir = root / "build"
        self.report = self.build_dir / "trace-report.json"

    def write_report(self, data: dict) -> None:
        self.build_dir.mkdir(parents=True, exist_ok=True)
        self.report.write_text(json.dumps(data, indent=1), encoding="utf-8")

    def read_report(self) -> dict:
        return json.loads(self.report.read_text(encoding="utf-8"))


class Command(ABC):
    """Uma etapa do pipeline. Subclasses implementam run()."""

    name: str = ""
    help: str = ""

    def __init__(self, paths: Paths):
        self.paths = paths

    @abstractmethod
    def run(self) -> None: ...


class TraceCommand(Command):
    name, help = "trace", "Vetoriza as folhas digitalizadas → sources/skeletons/raw"

    def run(self) -> None:
        from .skeleton.sheet_tracer import SheetTracer
        report = SheetTracer(self.paths.scans, self.paths.raw).run()
        self.paths.write_report(report)
        print(f"{len(report['glyphs'])} glifos vetorizados · altura das maiúsculas = "
              f"{report['cap_height_px']:.0f} px · escala = {report['scale']:.3f} un/px")


class TraceProofCommand(Command):
    name, help = "proof-trace", "Prova 1: original × vetorizado (proofs/prova1-vetorizacao.png)"

    def run(self) -> None:
        from .build.trace_proof import TraceProof
        scale = self.paths.read_report()["scale"]
        out = TraceProof(self.paths.scans, self.paths.raw, scale).render(self.paths.proofs / "prova1-vetorizacao.png")
        print(f"Prova gerada: {out}")


class HarmonizeCommand(Command):
    name, help = "harmonize", "Harmoniza os esqueletos brutos → sources/skeletons (preserva os 'locked')"

    def run(self) -> None:
        from .design.harmonize_run import HarmonizeRun
        res = HarmonizeRun(self.paths.raw, self.paths.skeletons).run()
        print(f"{res['written']} glifos harmonizados · preservados (editados à mão): {res['locked'] or 'nenhum'}")


class HarmonizeProofCommand(Command):
    name, help = "proof-harmonize", "Prova 2: antes × depois da harmonização (Regular)"

    def run(self) -> None:
        from .build.harmonize_proof import HarmonizeProof
        out = HarmonizeProof(self.paths.raw, self.paths.skeletons).render(self.paths.proofs / "prova2-harmonizacao.png")
        print(f"Prova gerada: {out}")


class DeriveCommand(Command):
    name, help = "derive", "Gera camadas derivadas: common/ (acentos, extras), print/ (Petricor), cursive/ (Caligrafia)"

    def run(self) -> None:
        from .design.letter_builder import DeriveRun
        sk = self.paths.skeletons
        res = DeriveRun(sk, sk / "common", sk / "print", sk / "cursive").run()
        print(f"Derivados por camada: {res}")


class FamilyProofCommand(Command):
    name, help = "proof-families", "Prova 2b: Petricor × Petricor Caligrafia (Regular)"

    def run(self) -> None:
        from .build.family_proof import FamilyProof
        from .outline.family import Families
        out = FamilyProof(Families(self.paths.skeletons).all()).render(self.paths.proofs / "prova4-acentos.png",
                                                                        with_accents=True)
        print(f"Prova gerada: {out}")


class MastersCommand(Command):
    name, help = "masters", "Gera masters UFO (Thin/Regular/Black) + designspace das duas famílias"

    def run(self) -> None:
        from .outline.family import Families
        from .outline.master_builder import MasterBuilder
        builder = MasterBuilder(self.paths.root / "sources" / "masters")
        for fam in Families(self.paths.skeletons).all():
            print(f"{fam.name}: {builder.build(fam)}")


class WeightsProofCommand(Command):
    name, help = "proof-weights", "Prova 5: cascata dos 9 pesos nas duas famílias"

    def run(self) -> None:
        from .build.weights_proof import WeightsProof
        from .outline.family import Families
        out = WeightsProof(Families(self.paths.skeletons).all()).render(self.paths.proofs / "prova5-pesos.png")
        print(f"Prova gerada: {out}")


class PetricorCli:
    def __init__(self, commands: list[Command]):
        self.commands = {c.name: c for c in commands}

    def main(self, argv=None) -> None:
        parser = argparse.ArgumentParser(prog="petricor", description="Pipeline da fonte Petricor")
        sub = parser.add_subparsers(dest="cmd", required=True)
        for c in self.commands.values():
            sub.add_parser(c.name, help=c.help)
        args = parser.parse_args(argv)
        self.commands[args.cmd].run()


def build_cli(paths: Paths | None = None) -> PetricorCli:
    paths = paths or Paths()
    return PetricorCli([TraceCommand(paths), TraceProofCommand(paths),
                        HarmonizeCommand(paths), HarmonizeProofCommand(paths),
                        DeriveCommand(paths), FamilyProofCommand(paths),
                        MastersCommand(paths), WeightsProofCommand(paths)])
