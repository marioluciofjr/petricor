"""Ajuste de curvas Bézier a um caminho de pixels.

1. Reamostra o caminho com passo de 1 px e suaviza (média gaussiana).
2. Detecta CANTOS (mudança brusca de direção, como no vértice do V).
3. Entre cantos, usa o algoritmo de Philip Schneider (Graphics Gems, 1990):
   ajusta uma cúbica por mínimos quadrados e, se o erro passar da
   tolerância, divide no ponto de maior erro e tenta de novo.
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import gaussian_filter1d

from ..model import Cubic, Stroke
from .tracer import PixelPath


def _unit(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


class CornerDetector:
    """Acha índices onde o caminho 'vira' mais que corner_angle graus."""

    def __init__(self, corner_angle_deg: float = 50.0, window: int = 6):
        self.cos_limit = np.cos(np.radians(corner_angle_deg))
        self.window = window

    def find(self, pts: np.ndarray, closed: bool) -> list[int]:
        n, w = len(pts), self.window
        if n < 2 * w + 3:
            return []
        score = np.full(n, 1.0)
        rng = range(n) if closed else range(w, n - w)
        for i in rng:
            a = _unit(pts[i] - pts[(i - w) % n])
            b = _unit(pts[(i + w) % n] - pts[i])
            score[i] = a @ b  # cosseno da virada: 1 = reto, < cos_limit = canto
        corners = []
        for i in rng:
            if score[i] < self.cos_limit and score[i] == score[max(0, i - w):i + w + 1].min():
                if not corners or i - corners[-1] > w:
                    corners.append(i)
        return corners


class SchneiderFitter:
    """Ajuste recursivo de cúbicas com tolerância de erro (em px)."""

    def __init__(self, tolerance: float = 1.5, max_iterations: int = 12):
        self.tolerance = tolerance
        self.max_iterations = max_iterations

    def fit(self, pts: np.ndarray, t1: np.ndarray | None = None, t2: np.ndarray | None = None) -> list[Cubic]:
        if len(pts) < 2:
            return []
        t1 = _unit(pts[min(2, len(pts) - 1)] - pts[0]) if t1 is None else t1
        t2 = _unit(pts[max(-3, -len(pts))] - pts[-1]) if t2 is None else t2
        return self._fit(pts, t1, t2, depth=0)

    def _fit(self, pts, t1, t2, depth):
        if len(pts) == 2 or depth > 12:
            d = np.linalg.norm(pts[-1] - pts[0]) / 3
            return [self._cubic([pts[0], pts[0] + t1 * d, pts[-1] + t2 * d, pts[-1]])]
        u = self._chord_params(pts)
        bez = self._generate(pts, u, t1, t2)
        err, split = self._max_error(pts, bez, u)
        if err < self.tolerance:
            return [self._cubic(bez)]
        if err < 4 * self.tolerance:
            for _ in range(self.max_iterations):
                u = self._reparameterize(pts, bez, u)
                bez = self._generate(pts, u, t1, t2)
                err, split = self._max_error(pts, bez, u)
                if err < self.tolerance:
                    return [self._cubic(bez)]
        split = min(max(split, 1), len(pts) - 2)
        tc = _unit(pts[split - 1] - pts[split + 1])
        return self._fit(pts[:split + 1], t1, tc, depth + 1) + self._fit(pts[split:], -tc, t2, depth + 1)

    @staticmethod
    def _cubic(b) -> Cubic:
        return Cubic(*[tuple(map(float, p)) for p in b])

    @staticmethod
    def _chord_params(pts):
        d = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
        return d / d[-1] if d[-1] > 0 else np.linspace(0, 1, len(pts))

    @staticmethod
    def _bezier(b, u):
        u = np.asarray(u)[:, None]
        mu = 1 - u
        return mu ** 3 * b[0] + 3 * mu ** 2 * u * b[1] + 3 * mu * u ** 2 * b[2] + u ** 3 * b[3]

    def _generate(self, pts, u, t1, t2):
        """Mínimos quadrados para o tamanho das alças (alpha1, alpha2)."""
        p0, p3 = pts[0], pts[-1]
        uu = u[:, None]
        b1 = 3 * uu * (1 - uu) ** 2
        b2 = 3 * uu ** 2 * (1 - uu)
        a1, a2 = b1 * t1, b2 * t2
        c00, c01, c11 = (a1 * a1).sum(), (a1 * a2).sum(), (a2 * a2).sum()
        tmp = pts - self._bezier(np.array([p0, p0, p3, p3]), u)
        x0, x1 = (a1 * tmp).sum(), (a2 * tmp).sum()
        det = c00 * c11 - c01 * c01
        seg = np.linalg.norm(p3 - p0)
        alpha1 = (x0 * c11 - x1 * c01) / det if abs(det) > 1e-12 else 0
        alpha2 = (c00 * x1 - c01 * x0) / det if abs(det) > 1e-12 else 0
        eps = 1e-6 * seg
        if alpha1 < eps or alpha2 < eps:  # solução degenerada: heurística de 1/3
            alpha1 = alpha2 = seg / 3
        return np.array([p0, p0 + t1 * alpha1, p3 + t2 * alpha2, p3])

    def _max_error(self, pts, bez, u):
        d = np.linalg.norm(self._bezier(bez, u) - pts, axis=1)
        i = int(np.argmax(d))
        return float(d[i]), i

    def _reparameterize(self, pts, bez, u):
        """Um passo de Newton-Raphson para achar o t mais próximo de cada ponto."""
        q = self._bezier(bez, u)
        d1 = np.array([3 * (bez[1] - bez[0]), 3 * (bez[2] - bez[1]), 3 * (bez[3] - bez[2])])
        d2 = np.array([2 * (d1[1] - d1[0]), 2 * (d1[2] - d1[1])])
        uu = u[:, None]
        q1 = (1 - uu) ** 2 * d1[0] + 2 * (1 - uu) * uu * d1[1] + uu ** 2 * d1[2]
        q2 = (1 - uu) * d2[0] + uu * d2[1]
        num = ((q - pts) * q1).sum(1)
        den = (q1 * q1).sum(1) + ((q - pts) * q2).sum(1)
        with np.errstate(divide="ignore", invalid="ignore"):
            nu = np.where(np.abs(den) > 1e-12, u - num / den, u)
        return np.clip(nu, 0, 1)


class BezierFitter:
    """Fachada: caminho de pixels → Stroke (segmentos cúbicos)."""

    def __init__(self, tolerance: float = 1.5, smooth_sigma: float = 2.0,
                 corners: CornerDetector | None = None):
        self.smooth_sigma = smooth_sigma
        self.corners = corners or CornerDetector()
        self.schneider = SchneiderFitter(tolerance)

    def fit(self, path: PixelPath) -> Stroke | None:
        if len(path.points) == 1 or path.length() < 2:
            # ponto: cúbica degenerada (os 4 pontos iguais) → vira um círculo na expansão
            p = tuple(map(float, path.points.mean(axis=0)))
            return Stroke([Cubic(p, p, p, p)])
        pts = self._resample(path.points, path.closed)
        if len(pts) < 2:
            return None
        pts = self._smooth(pts, path.closed)
        cut = self.corners.find(pts, path.closed)
        segments: list[Cubic] = []
        if path.closed:
            if cut:  # recomeça o anel num canto para não criar emenda falsa
                pts = np.roll(pts, -cut[0], axis=0)
                cut = [(c - cut[0]) % len(pts) for c in cut]
                pts = np.vstack([pts, pts[:1]])
                bounds = cut + [len(pts) - 1]
                for a, b in zip(bounds[:-1], bounds[1:]):
                    segments += self.schneider.fit(pts[a:b + 1])
            else:  # anel liso: mesma tangente no começo e no fim
                pts = np.vstack([pts, pts[:1]])
                t = _unit(pts[1] - pts[-2])
                segments = self.schneider.fit(pts, t, -t)
        else:
            bounds = [0] + cut + [len(pts) - 1]
            for a, b in zip(bounds[:-1], bounds[1:]):
                segments += self.schneider.fit(pts[a:b + 1])
        return Stroke(segments, path.closed) if segments else None

    @staticmethod
    def _resample(pts: np.ndarray, closed: bool, step: float = 1.0) -> np.ndarray:
        if len(pts) < 2:
            return pts
        if closed:
            pts = np.vstack([pts, pts[:1]])
        d = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
        if d[-1] < step:
            return pts[[0, -1]]
        s = np.arange(0, d[-1], step)
        out = np.column_stack([np.interp(s, d, pts[:, 0]), np.interp(s, d, pts[:, 1])])
        if not closed:
            out = np.vstack([out, pts[-1]])
        return out

    def _smooth(self, pts: np.ndarray, closed: bool) -> np.ndarray:
        if len(pts) < 5:
            return pts
        mode = "wrap" if closed else "nearest"
        sm = np.column_stack([gaussian_filter1d(pts[:, i], self.smooth_sigma, mode=mode) for i in (0, 1)])
        if not closed:  # pontas ficam onde a caneta começou/terminou
            sm[0], sm[-1] = pts[0], pts[-1]
        return sm
