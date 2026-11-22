"""Report-ready charts from results/ (metrics.csv, history.csv, fronts.json) -> results/*.png.

    scaling_<metric>.png     cost metrics (time, memory, states) per instance, one line per algorithm
                             (log scale when values span orders of magnitude) -> "theory vs measured"
    quality_<metric>.png     quality metrics (fitness, cost, accuracy, ...) as grouped bars
    convergence_<inst>.png   best value over time, from meter.record() calls
    front_<inst>.png         Pareto fronts (two objectives), from score()["_front"]
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # no window needed, just save PNGs
import matplotlib.pyplot as plt

RESULTS = Path("results")
COST = {"seconds": "time (s)", "peak_mb": "peak memory (MB)", "evaluated": "states / solutions evaluated",
        "pruned": "states pruned", "pruned_pct": "search space pruned (%)"}


def _rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _style(ax, title: str, xlabel: str, ylabel: str) -> None:
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.3)
    if ax.get_legend_handles_labels()[0]:
        ax.legend()


def _save(fig, name: str) -> Path:
    out = RESULTS / name
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def numeric_metrics(csv_path: Path = RESULTS / "metrics.csv") -> list[str]:
    """Columns of metrics.csv that contain numbers in every row and are not all zero (nothing to chart)."""
    rows = _rows(csv_path)
    out = []
    for col in rows[0] if rows else []:
        if col in ("instance", "algorithm"):
            continue
        try:
            values = [float(r[col]) for r in rows]
            if any(values):
                out.append(col)
        except (TypeError, ValueError):
            pass
    return out


def _table(rows: list[dict], metric: str):
    instances = list(dict.fromkeys(r["instance"] for r in rows))
    algos = list(dict.fromkeys(r["algorithm"] for r in rows))
    value = {(r["instance"], r["algorithm"]): float(r[metric]) for r in rows}
    return instances, algos, value


def scaling(metric: str, csv_path: Path = RESULTS / "metrics.csv") -> Path:
    """Cost metric per instance (instances in run order, e.g. small -> large), one line per algorithm."""
    instances, algos, value = _table(_rows(csv_path), metric)
    fig, ax = plt.subplots(figsize=(7, 4))
    all_vals = []
    for algo in algos:
        ys = [value.get((inst, algo)) for inst in instances]
        ax.plot(instances, ys, marker="o", label=algo)
        all_vals += [y for y in ys if y]
    if all_vals and min(all_vals) > 0 and max(all_vals) / min(all_vals) > 100:
        ax.set_yscale("log")
    _style(ax, f"Scaling: {COST.get(metric, metric)}", "instance", COST.get(metric, metric))
    return _save(fig, f"scaling_{metric}.png")


def metric_bars(metric: str, csv_path: Path = RESULTS / "metrics.csv") -> Path:
    """Grouped bar chart of one quality metric per instance and algorithm."""
    instances, algos, value = _table(_rows(csv_path), metric)
    width = 0.8 / max(len(algos), 1)
    fig, ax = plt.subplots(figsize=(7, 4))
    for i, algo in enumerate(algos):
        ax.bar([x + i * width for x in range(len(instances))], [value.get((inst, algo), 0) for inst in instances],
               width, label=algo)
    ax.set_xticks([x + width * (len(algos) - 1) / 2 for x in range(len(instances))], instances)
    _style(ax, f"{metric} by instance and algorithm", "instance", metric)
    return _save(fig, f"quality_{metric}.png")


def convergence(csv_path: Path = RESULTS / "history.csv") -> list[Path]:
    """Best value over time, one chart per instance, one line per algorithm."""
    series = defaultdict(lambda: defaultdict(list))
    for r in _rows(csv_path):
        series[r["instance"]][r["algorithm"]].append((float(r["seconds"]), float(r["value"])))
    outs = []
    for inst, algos in series.items():
        fig, ax = plt.subplots(figsize=(7, 4))
        for algo, pts in algos.items():
            ax.step([p[0] for p in pts], [p[1] for p in pts], where="post", label=algo)
        _style(ax, f"Convergence — {inst}", "time (s)", "best value")
        outs.append(_save(fig, f"convergence_{inst}.png"))
    return outs


def pareto_fronts(json_path: Path = RESULTS / "fronts.json", x: str = "f1", y: str = "f2") -> list[Path]:
    """One plot per instance, one staircase per algorithm.

    results/fronts.json format: {"<instance>/<algorithm>": [{"f1": ..., "f2": ...}, ...], ...}
    (pass x/y to use other key names). Both objectives are shown as stored.
    """
    fronts = json.loads(json_path.read_text())
    by_instance = defaultdict(dict)
    for key, points in fronts.items():
        inst, algo = key.split("/", 1)
        by_instance[inst][algo] = points
    outs = []
    for inst, algos in by_instance.items():
        fig, ax = plt.subplots(figsize=(6, 4))
        for algo, pts in algos.items():
            pts = sorted(pts, key=lambda p: p[x])
            ax.step([p[x] for p in pts], [p[y] for p in pts], where="post", marker="o", label=algo)
        _style(ax, f"Pareto fronts — {inst}", x, y)
        outs.append(_save(fig, f"front_{inst}.png"))
    return outs


def main() -> list[Path]:
    """Draw every chart the results allow (old PNGs are removed first so the report never shows stale charts)."""
    csv_path = RESULTS / "metrics.csv"
    if not csv_path.exists():
        raise SystemExit("results/metrics.csv not found — run `python tasks.py run` first.")
    for old in RESULTS.glob("*.png"):
        old.unlink()
    outs = []
    for m in numeric_metrics(csv_path):
        outs.append(scaling(m, csv_path) if m in COST else metric_bars(m, csv_path))
    if (RESULTS / "history.csv").exists():
        outs += convergence()
    if (RESULTS / "fronts.json").exists():
        outs += pareto_fronts()
    for p in outs:
        print(p)
    return outs


if __name__ == "__main__":
    main()
