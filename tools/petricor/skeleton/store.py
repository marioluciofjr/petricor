"""Repositório dos esqueletos em JSON (um arquivo por glifo).

Formato pensado para edição à mão:
{
  "name": "a", "unicodes": [97], "advance": 520, "locked": false,
  "anchors": {"top": [260, 520]},
  "strokes": [{"closed": false, "nodes": [[x,y], [x,y], ...]}],   // 1 + 3n pontos
  "components": [{"base": "a", "dx": 0, "dy": 0}]
}
"""
from __future__ import annotations

import json
from pathlib import Path

from ..model import Component, GlyphSkeleton, Stroke


class SkeletonStore:
    def __init__(self, folder: Path | str):
        self.folder = Path(folder)

    def path_for(self, name: str) -> Path:
        # Windows não diferencia maiúsculas de minúsculas em nomes de arquivo:
        # "A.json" e "a.json" colidiriam. Convenção UFO: maiúscula ganha "_".
        safe = "".join(ch + "_" if ch.isupper() else ch for ch in name)
        return self.folder / f"{safe}.json"

    def save(self, glyph: GlyphSkeleton) -> Path:
        self.folder.mkdir(parents=True, exist_ok=True)
        path = self.path_for(glyph.name)
        path.write_text(json.dumps(self._to_dict(glyph), ensure_ascii=False, indent=1) + "\n",
                        encoding="utf-8", newline="\n")
        return path

    def load(self, name: str) -> GlyphSkeleton:
        return self._from_dict(json.loads(self.path_for(name).read_text(encoding="utf-8")))

    def exists(self, name: str) -> bool:
        return self.path_for(name).exists()

    def all(self) -> list[GlyphSkeleton]:
        return [self._from_dict(json.loads(p.read_text(encoding="utf-8")))
                for p in sorted(self.folder.glob("*.json"))]

    # --- conversão ----------------------------------------------------
    @staticmethod
    def _round(p):
        return [round(float(p[0]), 1), round(float(p[1]), 1)]

    def _to_dict(self, g: GlyphSkeleton) -> dict:
        return {
            "name": g.name,
            "unicodes": g.unicodes,
            "advance": round(g.advance, 1),
            "locked": g.locked,
            "anchors": {k: self._round(v) for k, v in g.anchors.items()},
            "strokes": [{"closed": s.closed, "nodes": [self._round(p) for p in s.nodes()]} for s in g.strokes],
            "components": [{"base": c.base, "dx": c.dx, "dy": c.dy} for c in g.components],
        }

    @staticmethod
    def _from_dict(d: dict) -> GlyphSkeleton:
        return GlyphSkeleton(
            name=d["name"],
            unicodes=list(d.get("unicodes", [])),
            strokes=[Stroke.from_nodes([tuple(p) for p in s["nodes"]], s.get("closed", False))
                     for s in d.get("strokes", [])],
            advance=float(d.get("advance", 0)),
            anchors={k: tuple(v) for k, v in d.get("anchors", {}).items()},
            components=[Component(c["base"], c.get("dx", 0), c.get("dy", 0)) for c in d.get("components", [])],
            locked=bool(d.get("locked", False)),
        )
