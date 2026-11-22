"""City grids with traffic delays and congestion updates.

make_instance(size) -> dict with:
    rows, cols     grid dimensions; intersection id = r * cols + c, coordinates in `pos`
    edges          {(u, v): delay_minutes}   (two-way roads stored in both directions)
    base           free-flow delay per edge (lower bound, useful for an admissible A* heuristic)
    queries        list of (source, target)
    updates        list of congestion batches: [{(u, v): new_delay, ...}, ...]
"""

from __future__ import annotations

import random

SIZES = {"small": 10, "medium": 50, "large": 200, "huge": 500}


def make_instance(size: str, seed: int = 0, n_queries: int = 20, n_updates: int = 5) -> dict:
    rng = random.Random(seed)
    side = SIZES[size]
    pos = {r * side + c: (r, c) for r in range(side) for c in range(side)}
    base, edges = {}, {}
    for r in range(side):
        for c in range(side):
            u = r * side + c
            for dr, dc in ((0, 1), (1, 0)):
                if r + dr < side and c + dc < side:
                    v = (r + dr) * side + (c + dc)
                    free_flow = 1.0                               # 1 minute per block at free flow
                    delay = free_flow * rng.uniform(1.0, 3.0)     # current traffic
                    for a, b in ((u, v), (v, u)):
                        base[(a, b)] = free_flow
                        edges[(a, b)] = delay
    nodes = list(pos)
    queries = [tuple(rng.sample(nodes, 2)) for _ in range(n_queries)]
    keys = list(edges)
    updates = [{k: base[k] * rng.uniform(1.0, 8.0) for k in rng.sample(keys, max(1, len(keys) // 20))}
               for _ in range(n_updates)]
    return {"rows": side, "cols": side, "pos": pos, "edges": edges, "base": base,
            "queries": queries, "updates": updates}
