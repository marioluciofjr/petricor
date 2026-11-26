"""Glifos extras do GF Latin Core, construídos a partir dos traços do Mário.

Cada receita recebe uma função `get(nome)` que devolve o esqueleto já
disponível na família (camadas mescladas) e devolve um novo esqueleto.
Tudo é 'decomposto' (traços copiados), sem componentes escalados, porque
o Google Fonts reprova componentes com escala ou rotação.
"""
from __future__ import annotations

from typing import Callable

import numpy as np

from ..model import Component, GlyphSkeleton, Stroke
from .accents import GlyphNamer, is_dot_stroke
from .skeleton_pen import Corner as K
from .skeleton_pen import HandJitter, SkeletonPen

Getter = Callable[[str], GlyphSkeleton]


class StrokeOps:
    """Operações geométricas sobre listas de traços."""

    @staticmethod
    def bounds(strokes: list[Stroke]):
        pts = np.vstack([s.sample(16) for s in strokes])
        return pts[:, 0].min(), pts[:, 1].min(), pts[:, 0].max(), pts[:, 1].max()

    @staticmethod
    def move(strokes, dx=0.0, dy=0.0):
        return [s.transformed(lambda p: (p[0] + dx, p[1] + dy)) for s in strokes]

    @staticmethod
    def scale(strokes, sx, sy=None, origin=(0.0, 0.0)):
        sy = sx if sy is None else sy
        ox, oy = origin
        return [s.transformed(lambda p: (ox + (p[0] - ox) * sx, oy + (p[1] - oy) * sy)) for s in strokes]

    @staticmethod
    def rotate180(strokes, cx, cy):
        return [s.transformed(lambda p: (2 * cx - p[0], 2 * cy - p[1])) for s in strokes]

    @staticmethod
    def points_between(strokes, y0, y1):
        pts = np.vstack([s.sample(24) for s in strokes])
        return pts[(pts[:, 1] >= y0) & (pts[:, 1] <= y1)]


class ExtraBuilder:
    """Fábrica dos extras. `common()` = maiúsculas/símbolos; `family()` = dependem das minúsculas."""

    def __init__(self, get: Getter, jitter: HandJitter | None = None):
        self.get = get
        self.jitter = jitter or HandJitter(amplitude=3.0)
        self.ops = StrokeOps()

    # --- utilidades -----------------------------------------------------
    def _s(self, name):
        return list(self.get(name).strokes)

    def _line(self, a, b, seed):
        return self.jitter.apply(SkeletonPen.spline([a, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), b]), seed)

    def _spline(self, pts, seed, closed=False):
        return self.jitter.apply(SkeletonPen.spline(pts, closed=closed), seed)

    @staticmethod
    def _glyph(u, strokes, advance=0.0, anchors=None, name=None):
        g = GlyphSkeleton(name or GlyphNamer.name(u), [u] if u else [], strokes, advance, dict(anchors or {}))
        if strokes and not advance:
            b = StrokeOps.bounds(strokes)
            g.advance = b[2] - b[0]
        return g

    # --- maiúsculas e símbolos (iguais nas duas famílias) ---------------
    def common(self) -> list[GlyphSkeleton]:
        out = [self._glyph(0x0020, [], advance=260), self._glyph(0x00A0, [], advance=260)]
        return out + self._cap_letters() + self._symbols() + self._punctuation() + self._quotes()

    def _cap_letters(self) -> list[GlyphSkeleton]:
        o = self.ops
        out = []
        E, D, O, H, L = (self._s(n) for n in "EDOHL")
        eb = o.bounds(E)
        out.append(self._glyph(0x00C6, o.move(E, 300 - eb[0]) + [self._line((0, 0), (305, 700), "AE1"),
                                                                    self._line((150, 300), (305, 300), "AE2")]))
        ob = o.bounds(O)
        O2 = o.scale(O, 0.78, 1.0, (ob[0], 0))
        o2b = o.bounds(O2)
        out.append(self._glyph(0x0152, O2 + o.move(E, o2b[2] - eb[0] - 25)))
        bar = self._line((-40, 350), (170, 350), "Dbar")
        out.append(self._glyph(0x00D0, D + [bar]))
        out.append(self._glyph(0x0110, D + [bar]))
        out.append(self._glyph(0x00D8, O + [self._line((ob[0] - 30, -40), (ob[2] + 30, 740), "Oslash")]))
        out.append(self._glyph(0x00DE, [self._line((0, 700), (0, 0), "Th1"),
                                        self._spline([(5, 555), (180, 560), (300, 480), (300, 320), (190, 170),
                                                      (5, 165)], "Th2")]))
        hb = o.bounds(H)
        out.append(self._glyph(0x0126, H + [self._line((hb[0] - 50, 560), (hb[2] + 50, 560), "Hbar")]))
        lx = o.points_between(L, 200, 500)[:, 0].mean()
        out.append(self._glyph(0x0141, L + [self._line((lx - 70, 250), (lx + 110, 420), "Lsl")]))
        out.append(self._glyph(0x1E9E, [self._spline([(0, 0), (0, 500), (40, 640), (150, 705), (290, 680),
                                                     K(330, 640), (180, 430), K(180, 420), (320, 350), (350, 190),
                                                     (280, 40), (160, 0), (90, 15)], "Germ")]))
        return out

    def _symbols(self) -> list[GlyphSkeleton]:
        o = self.ops
        out = []
        for u, src in ((0x00A1, "exclam"), (0x00BF, "question")):
            s = self._s(src)
            b = o.bounds(s)
            out.append(self._glyph(u, o.move(o.rotate180(s, (b[0] + b[2]) / 2, (b[1] + b[3]) / 2), 0, -230 + 0)))
        out.append(self._glyph(0x00A7, [
            self._spline([(250, 650), (160, 705), (60, 660), (70, 560), (240, 470), (290, 370), (220, 280)], "sec1"),
            self._spline([(90, 430), (20, 340), (80, 250), (250, 170), (260, 60), (150, -5), (40, 40)], "sec2")]))
        circle = self._spline([(340, 700), (100, 600), (0, 350), (100, 100), (340, 0), (580, 100), (680, 350),
                               (580, 600)], "circ", closed=True)
        for u, src in ((0x00A9, "C"), (0x00AE, "R")):
            s = self._s(src)
            b = o.bounds(s)
            k = 0.42
            inner = o.move(o.scale(s, k), 340 - (b[0] + b[2]) / 2 * k, 350 - (b[1] + b[3]) / 2 * k)
            out.append(self._glyph(u, [circle] + inner))
        for u, src, n in ((0x00AB, "less", 2), (0x00BB, "greater", 2), (0x2039, "less", 1), (0x203A, "greater", 1)):
            s = self._s(src)
            b = o.bounds(s)
            k = 0.55
            one = o.move(o.scale(s, k), -b[0] * k, 230 - (b[1] + b[3]) / 2 * k)
            out.append(self._glyph(u, one + (o.move(one, 150) if n == 2 else [])))
        out.append(self._glyph(0x00B6, [self._spline([(250, 700), (110, 700), (20, 620), (20, 500), (110, 420),
                                                      (250, 420)], "pil1"),
                                        self._line((250, 700), (250, -100), "pil2"),
                                        self._line((360, 700), (360, -100), "pil3"),
                                        self._line((250, 700), (360, 700), "pil4")]))
        return out

    def _punctuation(self) -> list[GlyphSkeleton]:
        o = self.ops
        out = []
        period = self._s("period")
        pb = o.bounds(period)
        out.append(self._glyph(0x00B7, o.move(period, -pb[0], 280 - (pb[1] + pb[3]) / 2)))
        out.append(self._glyph(0x2022, [SkeletonPen.spline([(0, 310), (-30, 280), (0, 250), (30, 280)], closed=True),
                                        SkeletonPen.dot((0, 280))]))
        out.append(self._glyph(0x2026, period + o.move(period, 230) + o.move(period, 460)))
        out.append(self._dotted_circle())
        hy = self._s("hyphen")
        hyb = o.bounds(hy)
        for u, w in ((0x2013, 480), (0x2014, 960)):
            out.append(self._glyph(u, o.scale(hy, w / max(hyb[2] - hyb[0], 1), 1, (hyb[0], 0))))
        plus = self._s("plus")
        flat = min(plus, key=lambda s: np.ptp(s.sample(8)[:, 1]))
        out.append(self._glyph(0x2212, [flat]))
        T, M = self._s("T"), self._s("M")
        k = 0.36
        tb, mb = o.bounds(T), o.bounds(M)
        tm = o.move(o.scale(T, k), -tb[0] * k, 700 - 700 * k) + \
            o.move(o.scale(M, k), (tb[2] - tb[0]) * k + 40 - mb[0] * k, 700 - 700 * k)
        out.append(self._glyph(0x2122, tm))
        return out

    def _dotted_circle(self) -> GlyphSkeleton:
        """◌ (U+25CC): base técnica onde os sistemas mostram acentos soltos.
        Tem âncoras próprias para os acentos encaixarem nele."""
        cx, cy, r = 230.0, 230.0, 190.0
        dots = [SkeletonPen.dot((cx + r * np.cos(a), cy + r * np.sin(a))) for a in np.linspace(0, 2 * np.pi, 12, endpoint=False)]
        anchors = {"top": (cx, 495.0), "bottom": (cx, 0.0), "ogonek": (cx + 120, 0.0), "caron": (cx + 160, 560.0)}
        return self._glyph(0x25CC, dots, anchors=anchors)

    def _quotes(self) -> list[GlyphSkeleton]:
        """Aspas curvas: a vírgula do Mário é reta (girada fica igual), então o gesto ganha curva.

        ’ (fecha) desce curvando para a esquerda; ‘ (abre) é o mesmo gesto girado 180°.
        """
        o = self.ops
        hook = self._spline([(40, 140), (52, 95), (38, 40), (0, 0)], "quote")
        up = o.move([hook], 0, 700 - 140)
        turned = o.rotate180(up, 26, 630)
        comma = self._s("comma")
        cb = o.bounds(comma)
        base = o.move(comma, -cb[0])
        gap = 120
        return [self._glyph(0x2019, up), self._glyph(0x2018, turned), self._glyph(0x201A, base),
                self._glyph(0x201D, up + o.move(up, gap)), self._glyph(0x201C, turned + o.move(turned, gap)),
                self._glyph(0x201E, base + o.move(base, gap))]

    # --- dependem das minúsculas (gerados para cada família) -------------
    def family(self, cursive: bool, has: Callable[[str], bool], get_print: Getter) -> list[GlyphSkeleton]:
        out = self._dotless(has) + self._ligatures_and_slashes(cursive, has)
        return out + self._stroked(has) + self._ordinals_and_cent(get_print)

    def _dotless(self, has) -> list[GlyphSkeleton]:
        out = []
        for u, src in ((0x0131, "i"), (0x0237, "j")):
            for suffix in ("", ".hi"):
                if not has(src + suffix):
                    continue
                g = self.get(src + suffix)
                strokes = [s for s in g.strokes if not is_dot_stroke(s)]
                out.append(self._glyph(u if not suffix else None, strokes, g.advance, g.anchors,
                                       name=GlyphNamer.name(u) + suffix))
        return out

    def _ligatures_and_slashes(self, cursive, has) -> list[GlyphSkeleton]:
        o = self.ops
        out = []
        og = self.get("o")
        body = o.points_between(og.strokes, 20, 420)
        bx0, bx1 = body[:, 0].min(), (body[:, 0].max() if not cursive else min(body[:, 0].max(), 300))
        out.append(self._glyph(0x00F8, list(og.strokes) + [self._line((bx0 - 20, -40), (bx1 + 20, 470), "osl")],
                               og.advance, og.anchors))
        e_after_o = "e.hi" if cursive and has("e.hi") else "e"
        overlap = 0.0 if cursive else 95.0  # de forma: o 'e' invade o 'o'/'a' (ligadura de verdade)
        out.append(GlyphSkeleton("ae", [0xE6], components=[Component("a"), Component("e", overlap, 0, "after")]))
        out.append(GlyphSkeleton("oe", [0x153], components=[Component("o"), Component(e_after_o, overlap, 0, "after")]))
        out.append(self._glyph(0x00F0, [self._spline([(150, 432), (45, 380), (5, 215), (45, 45), (145, 0), (250, 40),
                                                      (295, 215), (262, 375)], "eth1", closed=True),
                                        self._spline([(262, 375), (280, 560), (200, 690), (110, 735)], "eth2"),
                                        self._line((90, 560), (270, 660), "eth3")]))
        out.append(self._glyph(0x00FE, [self._line((10, 720), (5, -230), "th1"),
                                        self._spline([(10, 300), (90, 410), (180, 432), (275, 370), (305, 215),
                                                      (270, 50), (170, 0), (80, 15), (10, 60)], "th2")]))
        out.append(self._glyph(0x00DF, [self._spline([(10, 0), (10, 560), (50, 680), (150, 725), (250, 690),
                                                     (270, 600), (210, 520), K(150, 490), (260, 440), (300, 300),
                                                     (260, 120), (170, 10), (80, 15)], "sz")]))
        return out

    def _stroked(self, has) -> list[GlyphSkeleton]:
        o = self.ops
        out = []
        for u, src, y, dx0, dx1 in ((0x0142, "l", (290, 470), -70, 80), (0x0127, "h", (600, 600), -60, 110),
                                     (0x0111, "d", (620, 620), -90, 70)):
            g = self.get(src)
            stem = o.points_between(g.strokes, 450 if src != "l" else 250, 650 if src != "l" else 550)
            xs = float(np.median(stem[:, 0])) if src != "d" else float(stem[:, 0].max())
            out.append(self._glyph(u, list(g.strokes) + [self._line((xs + dx0, y[0]), (xs + dx1, y[1]), src + "bar")],
                                   g.advance, g.anchors))
        return out

    def _ordinals_and_cent(self, get_print: Getter) -> list[GlyphSkeleton]:
        """ª º ¢ usam sempre as minúsculas DE FORMA (sem conectores), nas duas famílias."""
        o = self.ops
        out = []
        for u, src in ((0x00AA, "a"), (0x00BA, "o")):
            s = list(get_print(src).strokes)
            b = o.bounds(s)
            k = 0.58
            small = o.move(o.scale(s, k), -b[0] * k, 330)
            sb = o.bounds(small)
            out.append(self._glyph(u, small + [self._line((sb[0], 280), (sb[2], 280), src + "ord")]))
        c = list(get_print("c").strokes)
        cb = o.bounds(c)
        cx = (cb[0] + cb[2]) / 2
        out.append(self._glyph(0x00A2, c + [self._line((cx, -70), (cx + 10, 500), "cent")]))
        return out
