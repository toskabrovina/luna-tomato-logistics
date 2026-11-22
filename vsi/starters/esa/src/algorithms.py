"""Your optimisers for the ESA problem. Each one: fn(udp, budget_seconds, meter, rng) -> list of decision vectors.

The baseline samples random vectors inside the UDP bounds. Replace / extend with your own methods
(greedy construction, local search, simulated annealing, genetic algorithm, …) and register them.

- meter.count() for every fitness evaluation, meter.record(best) when the best value improves
  (-> convergence chart).
- Multi-objective problems (udp.get_nobj() >= 2): return the non-dominated vectors (-> Pareto front chart).
"""

from __future__ import annotations

import time

from vsi.pareto import pareto_filter


def random_vector(udp, rng):
    lower, upper = udp.get_bounds()
    n_int = udp.get_nix() if hasattr(udp, "get_nix") else 0
    n = len(lower)
    x = []
    for i in range(n):
        integer = i >= n - n_int or (isinstance(lower[i], int) and isinstance(upper[i], int))
        if integer:          # pygmo convention: last get_nix() entries; or bounds given as Python ints
            x.append(rng.randint(int(lower[i]), int(upper[i])))
        else:
            x.append(rng.uniform(lower[i], upper[i]))
    return x


def n_objectives(udp) -> int:
    return udp.get_nobj() if hasattr(udp, "get_nobj") else 1


def random_search(udp, budget_seconds, meter, rng):
    multi = n_objectives(udp) >= 2
    archive = []                      # multi-objective: ((f1, f2), x) of non-dominated solutions
    best_x, best_f = None, None
    deadline = time.perf_counter() + budget_seconds
    while time.perf_counter() < deadline:
        x = random_vector(udp, rng)
        f = list(udp.fitness(x))
        meter.count()
        if multi:
            archive = pareto_filter(archive + [((f[0], f[1]), x)])
        elif best_f is None or f < best_f:
            best_x, best_f = x, f
            meter.record(f[0])
    if multi:
        return [x for _, x in archive]
    return [best_x] if best_x is not None else []


ALGORITHMS = {
    "random_search": random_search,
}
