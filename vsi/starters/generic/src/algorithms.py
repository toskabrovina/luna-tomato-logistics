"""Your algorithms. Each one: fn(instance, meter) -> result.

- Call meter.count() for every state / candidate solution you explore,
  and meter.prune() for every one you skip thanks to pruning.
- Call meter.record(best_cost_so_far) whenever the best solution improves -> convergence chart.
- Register every algorithm in ALGORITHMS so `python tasks.py run` measures it.
- `score(instance, result)` returns the quality numbers that go into results/metrics.csv.
"""

from __future__ import annotations


def baseline(instance, meter):
    """TODO: the simplest correct algorithm for this problem (the bar to beat)."""
    meter.count()
    return None


ALGORITHMS = {
    "baseline": baseline,
    # "my_algorithm": my_algorithm,
}


def score(instance, result) -> dict:
    """TODO: quality metrics of `result` (e.g. cost, energy, accuracy, valid=True/False)."""
    return {"solved": result is not None}
