"""Do esqueleto em pixels para caminhos ordenados (traços de caneta).

O esqueleto é visto como um GRAFO:
- nós   = pontas (1 vizinho) e cruzamentos (3+ vizinhos);
- arestas = sequências de pixels entre dois nós.

Depois:
1. Podamos "galhos" curtos que o afinamento cria nas pontas e quinas.
2. Em cada cruzamento, ligamos os ramos que continuam mais em linha reta
   (no 'X', as duas diagonais; no 't', a barra atravessa a haste).
3. Percorremos as ligações para montar cada traço contínuo.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

import numpy as np

_OFFSETS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


@dataclass
class PixelPath:
    """Caminho em coordenadas de imagem (x, y), y para baixo."""

    points: np.ndarray
    closed: bool = False

    def length(self) -> float:
        d = np.diff(self.points, axis=0)
        return float(np.hypot(d[:, 0], d[:, 1]).sum())


@dataclass
class _Node:
    pixels: set
    center: np.ndarray
    ends: list = field(default_factory=list)  # (edge_id, lado 0/1)


@dataclass
class _Edge:
    a: int
    b: int
    pts: np.ndarray  # inclui o centro do nó 'a' no início e de 'b' no fim
    alive: bool = True

    def length(self) -> float:
        d = np.diff(self.pts, axis=0)
        return float(np.hypot(d[:, 0], d[:, 1]).sum()) if len(d) else 0.0


class SkeletonGraph:
    """Constrói o grafo (nós e arestas) a partir da máscara do esqueleto."""

    def __init__(self, skeleton: np.ndarray):
        self.pixels = {(int(r), int(c)) for r, c in zip(*np.nonzero(skeleton))}
        self.nodes: dict[int, _Node] = {}
        self.edges: dict[int, _Edge] = {}
        self.loops: list[np.ndarray] = []  # componentes que são anéis sem nós
        self._pix2node: dict = {}
        self._build()

    # --- construção ---------------------------------------------------
    def _neighbors(self, p):
        r, c = p
        return [(r + dr, c + dc) for dr, dc in _OFFSETS if (r + dr, c + dc) in self.pixels]

    def _build(self):
        node_px = {p for p in self.pixels if len(self._neighbors(p)) != 2}
        self._cluster_nodes(node_px)
        visited = set()
        direct = set()
        for nid, node in list(self.nodes.items()):
            for q in node.pixels:
                for s in self._neighbors(q):
                    if s in node.pixels:
                        continue
                    if s in self._pix2node:
                        key = tuple(sorted((nid, self._pix2node[s])))
                        if key not in direct:
                            direct.add(key)
                            self._add_edge(nid, self._pix2node[s], [])
                    elif s not in visited:
                        self._walk(nid, q, s, visited)
        self._collect_loops(visited)

    def _cluster_nodes(self, node_px):
        seen = set()
        for p in node_px:
            if p in seen:
                continue
            stack, group = [p], set()
            seen.add(p)
            while stack:
                cur = stack.pop()
                group.add(cur)
                for n in self._neighbors(cur):
                    if n in node_px and n not in seen:
                        seen.add(n)
                        stack.append(n)
            nid = len(self.nodes)
            arr = np.array(list(group), float)
            self.nodes[nid] = _Node(group, np.array([arr[:, 1].mean(), arr[:, 0].mean()]))
            for g in group:
                self._pix2node[g] = nid

    def _walk(self, start_node, prev, cur, visited):
        path = []
        while True:
            visited.add(cur)
            path.append(cur)
            nxt = [n for n in self._neighbors(cur) if n != prev and n not in visited]
            # prioriza vizinhos que já são nó (fecha a aresta) para não "pular" o nó
            nodes_ahead = [n for n in nxt if n in self._pix2node and not (len(path) == 1 and self._pix2node[n] == start_node and n == prev)]
            if nodes_ahead:
                end_node = self._pix2node[nodes_ahead[0]]
                self._add_edge(start_node, end_node, path)
                return
            if not nxt:  # não deveria ocorrer; encerra como ponta solta
                self._add_edge(start_node, start_node, path)
                return
            prev, cur = cur, nxt[0]

    def _add_edge(self, a, b, path_px):
        interior = [np.array([c, r], float) for r, c in path_px]
        pts = np.array([self.nodes[a].center, *interior, self.nodes[b].center])
        eid = len(self.edges)
        self.edges[eid] = _Edge(a, b, pts)
        self.nodes[a].ends.append((eid, 0))
        self.nodes[b].ends.append((eid, 1))

    def _collect_loops(self, visited):
        rest = self.pixels - visited - set(self._pix2node)
        while rest:
            start = next(iter(rest))
            path, prev, cur = [start], None, start
            rest.discard(start)
            while True:
                nxt = [n for n in self._neighbors(cur) if n != prev and n in rest]
                if not nxt:
                    break
                prev, cur = cur, nxt[0]
                rest.discard(cur)
                path.append(cur)
            self.loops.append(np.array([[c, r] for r, c in path], float))

    # --- consultas ----------------------------------------------------
    def degree(self, nid: int) -> int:
        return sum(1 for e, _ in self.nodes[nid].ends if self.edges[e].alive)

    def live_ends(self, nid: int):
        return [(e, s) for e, s in self.nodes[nid].ends if self.edges[e].alive]


class StrokeTracer:
    """Transforma o esqueleto em caminhos de traço, prontos para o ajuste Bézier."""

    def __init__(self, spur_factor: float = 1.6, join_angle_deg: float = 55.0,
                 probe_factor: float = 2.0, min_path_px: float = 3.0):
        self.spur_factor = spur_factor
        self.join_cos = -np.cos(np.radians(join_angle_deg))
        self.probe_factor = probe_factor
        self.min_path_px = min_path_px

    def trace(self, skeleton: np.ndarray, stroke_width: float) -> list[PixelPath]:
        g = SkeletonGraph(skeleton)
        self._prune_spurs(g, self.spur_factor * max(stroke_width, 2.0))
        links = self._pair_junctions(g, self.probe_factor * max(stroke_width, 2.0))
        paths = self._chain(g, links, trim=0.6 * stroke_width)
        paths += [PixelPath(loop, closed=True) for loop in g.loops if len(loop) > 8]
        paths = [p for p in paths if p.length() >= self.min_path_px]
        # pontos isolados (pingo do i, ponto final) viram um "traço" de 1 ponto
        paths += [PixelPath(n.center[None, :]) for nid, n in g.nodes.items() if g.degree(nid) == 0]
        return paths

    # ------------------------------------------------------------------
    @staticmethod
    def _prune_spurs(g: SkeletonGraph, spur_len: float):
        """Remove galhos curtos que saem de um cruzamento e terminam soltos."""
        changed = True
        while changed:
            changed = False
            for e in g.edges.values():
                if not e.alive or e.a == e.b:
                    continue
                da, db = g.degree(e.a), g.degree(e.b)
                tip_at_a, tip_at_b = da == 1 and db >= 3, db == 1 and da >= 3
                if (tip_at_a or tip_at_b) and e.length() < spur_len:
                    e.alive = False
                    changed = True

    @staticmethod
    def _direction(edge: _Edge, side: int, probe: float) -> np.ndarray:
        """Direção com que a aresta SAI do nó, medida a 'probe' pixels de distância."""
        pts = edge.pts if side == 0 else edge.pts[::-1]
        origin = pts[0]
        d = np.hypot(*(pts - origin).T)
        idx = int(np.searchsorted(d, probe)) if d[-1] > probe else len(pts) - 1
        v = pts[max(idx, 1)] - origin
        n = np.linalg.norm(v)
        return v / n if n else v

    def _pair_junctions(self, g: SkeletonGraph, probe: float) -> dict:
        """Em cada nó, liga as pontas de aresta que seguem mais 'em frente'."""
        links = {}
        for nid in g.nodes:
            ends = g.live_ends(nid)
            if len(ends) == 2:  # nó de passagem: sempre liga
                links[ends[0]], links[ends[1]] = ends[1], ends[0]
                continue
            if len(ends) < 3:
                continue
            dirs = {end: self._direction(g.edges[end[0]], end[1], probe) for end in ends}
            pairs = sorted(((float(dirs[i] @ dirs[j]), i, j)
                            for k, i in enumerate(ends) for j in ends[k + 1:]))
            used = set()
            for dot, i, j in pairs:
                if dot > self.join_cos:
                    break  # restantes fazem ângulo agudo demais para ser o mesmo traço
                if i in used or j in used:
                    continue
                links[i], links[j] = j, i
                used |= {i, j}
        return links

    @staticmethod
    def _edge_points(g, end, trim_start, trim_end, trim):
        """Pontos da aresta a partir da ponta 'end', aparando perto dos cruzamentos ligados."""
        eid, side = end
        pts = g.edges[eid].pts if side == 0 else g.edges[eid].pts[::-1]
        if trim > 0 and len(pts) > 4:
            d0 = np.hypot(*(pts - pts[0]).T)
            d1 = np.hypot(*(pts - pts[-1]).T)
            keep = np.ones(len(pts), bool)
            if trim_start:
                keep &= d0 >= trim
            if trim_end:
                keep &= d1 >= trim
            if keep.sum() >= 2:
                pts = pts[keep]
        return pts

    def _chain(self, g: SkeletonGraph, links: dict, trim: float) -> list[PixelPath]:
        used = set()
        paths = []

        def run(start_end):
            pieces, end, closed = [], start_end, False
            while True:
                eid, side = end
                used.add(eid)
                other = (eid, 1 - side)
                nxt = links.get(other)
                pieces.append(self._edge_points(g, end, end in links, nxt is not None, trim))
                if nxt is None:
                    break
                if nxt[0] in used:
                    closed = nxt == start_end
                    break
                end = nxt
            return PixelPath(np.vstack(pieces), closed)

        all_ends = [(eid, s) for eid, e in g.edges.items() if e.alive for s in (0, 1)]
        for end in all_ends:  # caminhos abertos começam numa ponta sem ligação
            if end[0] not in used and end not in links:
                paths.append(run(end))
        for end in all_ends:  # sobram ciclos fechados
            if end[0] not in used:
                paths.append(run(end))
        return paths
