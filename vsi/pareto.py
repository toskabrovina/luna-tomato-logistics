"""Pareto front utilities for two objectives that are BOTH minimised.

Points are (f1, f2) tuples. If an objective should be maximised, pass its negative
(or an equivalent minimised quantity).
"""

from __future__ import annotations

from typing import Sequence

Point = tuple[float, float]


def dominates(a: Point, b: Point) -> bool:
    """a dominates b if it is no worse in both objectives and better in at least one."""
    return a[0] <= b[0] and a[1] <= b[1] and a != b


def pareto_filter(items: Sequence[tuple[Point, object]]) -> list[tuple[Point, object]]:
    """Keep only non-dominated (point, payload) items. O(k log k) for k items."""
    best: list[tuple[Point, object]] = []
    for point, payload in sorted(items, key=lambda it: it[0]):
        if not best or point[1] < best[-1][0][1]:
            best.append((point, payload))
    return best


def hypervolume(points: Sequence[Point], ref: Point) -> float:
    """2-D hypervolume dominated by `points` w.r.t. reference point `ref` (bigger is better)."""
    front = [p for p, _ in pareto_filter([(p, None) for p in points]) if p[0] < ref[0] and p[1] < ref[1]]
    area = 0.0
    prev = ref[1]
    for f1, f2 in front:
        area += (ref[0] - f1) * (prev - f2)
        prev = f2
    return area


def select_best(items: Sequence[tuple[Point, object]], k: int, ref: Point) -> list[tuple[Point, object]]:
    """Choose at most k items maximising hypervolume (greedy: add the biggest gain each time)."""
    candidates = pareto_filter(items)
    if len(candidates) <= k:
        return candidates
    chosen: list[tuple[Point, object]] = []
    while len(chosen) < k:
        base = hypervolume([p for p, _ in chosen], ref)
        _, best = max(
            ((hypervolume([p for p, _ in chosen] + [c[0]], ref) - base, i) for i, c in enumerate(candidates)
             if candidates[i] not in chosen),
            key=lambda g: g[0],
        )
        chosen.append(candidates[best])
    return sorted(chosen, key=lambda it: it[0])
