"""Random timelines: a forward causal DAG plus time-travel edges that point back in time.

make_instance(size) -> dict with:
    events        list of {id, timestamp, entities, remove_cost, modify_cost, delay_cost}
    dependencies  forward causal edges (u, v) with timestamp[u] < timestamp[v]
    time_travel   backward edges (u, v) with timestamp[u] > timestamp[v]  (each may create paradoxes)
    max_timelines limit on alternative timelines to explore
"""

from __future__ import annotations

import random

# events, extra forward edges per event, time-travel edges
SIZES = {"small": (10, 1, 2), "medium": (100, 2, 8), "large": (1_000, 3, 40), "huge": (10_000, 3, 200)}


def make_instance(size: str, seed: int = 0) -> dict:
    rng = random.Random(seed)
    n, extra, n_travel = SIZES[size]
    years = sorted(rng.sample(range(1000, 1000 + 50 * n), n))
    events = [{"id": i, "timestamp": years[i], "entities": rng.sample(range(max(5, n // 5)), 2),
               "remove_cost": rng.randint(1, 20), "modify_cost": rng.randint(1, 15), "delay_cost": rng.randint(1, 10)}
              for i in range(n)]
    deps = {(i, i + 1) for i in range(n - 1)}                  # chain of history
    for u in range(n - 1):
        for _ in range(extra):
            deps.add((u, rng.randrange(u + 1, n)))
    travel = set()
    while len(travel) < n_travel:
        u = rng.randrange(1, n)
        travel.add((u, rng.randrange(0, u)))                  # back to an earlier event
    return {"events": events, "dependencies": sorted(deps), "time_travel": sorted(travel),
            "max_timelines": 1000}
