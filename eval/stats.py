from __future__ import annotations

import math
from typing import Dict, List, Sequence


def mean(xs: Sequence[float]) -> float:
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0


def std(xs: Sequence[float], ddof: int = 1) -> float:
    xs = list(xs)
    n = len(xs)
    if n - ddof <= 0:
        return 0.0
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (n - ddof))


def mean_std(xs: Sequence[float]) -> Dict[str, float]:
    xs = list(xs)
    return {"mean": round(mean(xs), 4), "std": round(std(xs), 4), "n": len(xs)}


def cohen_kappa(a: Sequence, b: Sequence) -> float:
    a, b = list(a), list(b)
    if len(a) != len(b):
        raise ValueError(f"label lengths differ: {len(a)} vs {len(b)}")
    n = len(a)
    if n == 0:
        return 0.0
    cats = sorted(set(a) | set(b), key=lambda x: str(x))
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pa = {c: a.count(c) / n for c in cats}
    pb = {c: b.count(c) / n for c in cats}
    pe = sum(pa[c] * pb[c] for c in cats)
    if abs(1.0 - pe) < 1e-12:
        return 1.0 if po == 1.0 else 0.0
    return (po - pe) / (1.0 - pe)


def _rankdata(values: Sequence[float]) -> List[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def wilcoxon_signed_rank(
    x: Sequence[float], y: Sequence[float]
) -> Dict[str, float]:
    x, y = list(x), list(y)
    if len(x) != len(y):
        raise ValueError(f"paired arrays differ in length: {len(x)} vs {len(y)}")
    diffs = [a - b for a, b in zip(x, y)]
    nonzero = [d for d in diffs if d != 0]
    n = len(nonzero)
    med = _median(diffs)
    if n == 0:
        return {"W": 0.0, "p_value": 1.0, "n_effective": 0, "median_diff": med,
                "method": "degenerate", "n_pairs": len(x)}

    try:
        from scipy.stats import wilcoxon

        stat, p = wilcoxon(x, y, zero_method="wilcox", alternative="two-sided")
        return {"W": float(stat), "p_value": float(p), "n_effective": n,
                "median_diff": med, "method": "scipy", "n_pairs": len(x)}
    except Exception:
        pass

    abs_ranks = _rankdata([abs(d) for d in nonzero])
    w_plus = sum(r for d, r in zip(nonzero, abs_ranks) if d > 0)
    w_minus = sum(r for d, r in zip(nonzero, abs_ranks) if d < 0)
    W = min(w_plus, w_minus)
    mean_w = n * (n + 1) / 4.0
    from collections import Counter

    tie_term = sum(t ** 3 - t for t in Counter(abs(d) for d in nonzero).values())
    var_w = (n * (n + 1) * (2 * n + 1) - tie_term / 2.0) / 24.0
    if var_w <= 0:
        return {"W": W, "p_value": 1.0, "n_effective": n, "median_diff": med,
                "method": "normal-approx", "n_pairs": len(x)}
    z = (W - mean_w + 0.5 * (1 if W < mean_w else -1)) / math.sqrt(var_w)
    p = 2.0 * _norm_sf(abs(z))
    return {"W": float(W), "p_value": float(min(1.0, p)), "n_effective": n,
            "median_diff": med, "z": round(z, 4), "method": "normal-approx",
            "n_pairs": len(x)}


def _median(xs: Sequence[float]) -> float:
    xs = sorted(xs)
    n = len(xs)
    if n == 0:
        return 0.0
    mid = n // 2
    return xs[mid] if n % 2 else (xs[mid - 1] + xs[mid]) / 2.0


def _norm_sf(z: float) -> float:
    return 0.5 * math.erfc(z / math.sqrt(2.0))


def cliffs_delta(x: Sequence[float], y: Sequence[float]) -> float:
    x, y = list(x), list(y)
    if not x or not y:
        return 0.0
    gt = lt = 0
    for a in x:
        for b in y:
            if a > b:
                gt += 1
            elif a < b:
                lt += 1
    return (gt - lt) / (len(x) * len(y))
