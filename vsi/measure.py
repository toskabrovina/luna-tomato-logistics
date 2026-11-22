"""Measure runtime, peak memory and number of explored states/solutions.

Usage:
    with Meter() as meter:
        result = my_algorithm(data, meter=meter)   # call meter.count() for each state explored
    print(meter.report())   # {'seconds': ..., 'peak_mb': ..., 'evaluated': ...}

Convergence: call meter.record(best_value_so_far) whenever your algorithm improves; `run_experiments`
saves it to results/history.csv and `python tasks.py plots` draws a convergence chart (value over time).
"""

from __future__ import annotations

import time
import tracemalloc


class Meter:
    def __init__(self) -> None:
        self.evaluated = 0
        self.pruned = 0
        self.seconds = 0.0
        self.peak_mb = 0.0
        self.history: list[tuple[float, int, float]] = []   # (seconds, evaluated, value)
        self._t0 = time.perf_counter()

    def count(self, k: int = 1) -> None:
        """Record k explored states / evaluated solutions."""
        self.evaluated += k

    def prune(self, k: int = 1) -> None:
        """Record k states skipped thanks to pruning (for the 'search space eliminated' metric)."""
        self.pruned += k

    def record(self, value: float) -> None:
        """Record the current best objective value (for the convergence chart)."""
        self.history.append((round(time.perf_counter() - self._t0, 6), self.evaluated, float(value)))

    def __enter__(self) -> "Meter":
        tracemalloc.start()
        self._t0 = time.perf_counter()
        return self

    def __exit__(self, *exc) -> None:
        self.seconds = time.perf_counter() - self._t0
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        self.peak_mb = peak / 2**20

    def report(self) -> dict:
        total = self.evaluated + self.pruned
        return {
            "seconds": round(self.seconds, 4),
            "peak_mb": round(self.peak_mb, 3),
            "evaluated": self.evaluated,
            "pruned": self.pruned,
            "pruned_pct": round(100 * self.pruned / total, 2) if total else 0.0,
        }
