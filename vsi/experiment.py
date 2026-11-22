"""Run every algorithm on every instance, measure it, and save a metrics table.

Generic: `algorithms` maps name -> fn(instance, meter) -> result, and `score` turns a result into a
dict of quality numbers. Writes results/metrics.csv and returns the rows.

Extra outputs (used by `python tasks.py plots`):
- results/history.csv  every meter.record(value) call -> convergence charts
- results/fronts.json  when score() returns "_front": [[f1, f2], ...] -> Pareto front charts
Keys starting with "_" are not written to metrics.csv.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Callable

from .measure import Meter


def run_experiments(
    algorithms: dict[str, Callable],
    instances: dict[str, object],
    score: Callable[[str, object, object], dict],
    out_csv: str | Path = "results/metrics.csv",
) -> list[dict]:
    rows, history, fronts = [], [], {}
    for inst_name, instance in instances.items():
        for algo_name, algo in algorithms.items():
            with Meter() as meter:
                result = algo(instance, meter)
            quality = score(inst_name, instance, result)
            if quality.get("_front"):
                fronts[f"{inst_name}/{algo_name}"] = [{"f1": p[0], "f2": p[1]} for p in quality["_front"]]
            history += [{"instance": inst_name, "algorithm": algo_name, "seconds": t, "evaluated": e, "value": v}
                        for t, e, v in meter.history]
            row = {"instance": inst_name, "algorithm": algo_name, **meter.report(),
                   **{k: v for k, v in quality.items() if not k.startswith("_")}}
            rows.append(row)
            print(row)
    out = Path(out_csv)
    out.parent.mkdir(parents=True, exist_ok=True)
    for extra in ("history.csv", "fronts.json"):   # never mix with charts from an older run
        (out.parent / extra).unlink(missing_ok=True)
    if history:
        with (out.parent / "history.csv").open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(history[0]))
            writer.writeheader()
            writer.writerows(history)
    if fronts:
        (out.parent / "fronts.json").write_text(json.dumps(fronts))
    if rows:
        fields = list(dict.fromkeys(k for r in rows for k in r))
        with out.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    return rows
