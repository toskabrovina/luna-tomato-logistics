"""Upper Bound per Luna Tomato Logistics (Matching I dhe II).

Llogarit nje kufi TE SIGURTE mbi peshen optimale:
per cdo E, L, D marrim maksimumin e peshes dhe pastaj minimumin
nga tre shumat. Nuk perdor librari optimizimi.

Ekzekuto nga folderi kryesor:
    python src/upper_bound.py
"""

from __future__ import annotations

import csv
from itertools import combinations
from pathlib import Path

from matching import Transfer, is_valid, load_transfers, total_weight

ROOT = Path(__file__).resolve().parent.parent
DATASETS = {
    "matching-i": ROOT / "data" / "spoc4" / "ltl" / "random_harder_5000.txt",
    "matching-ii": ROOT / "data" / "spoc4" / "ltl" / "random_hard_10000.txt",
}


def upper_bound(transfers: list[Transfer]) -> float:
    """Kufi mbi optimumin, O(n) kohe dhe O(numrit te nyjeve) memorie."""
    best_e: dict[int, float] = {}
    best_l: dict[int, float] = {}
    best_d: dict[int, float] = {}

    for t in transfers:
        # Pesha negative nuk ndihmon; mund te mos zgjedhim asnje transfer.
        w = max(0.0, t.weight)
        best_e[t.earth] = max(best_e.get(t.earth, 0.0), w)
        best_l[t.moon] = max(best_l.get(t.moon, 0.0), w)
        best_d[t.destination] = max(best_d.get(t.destination, 0.0), w)

    return min(sum(best_e.values()), sum(best_l.values()), sum(best_d.values()))


def best_measured_score(problem_id: str) -> tuple[str, float] | None:
    """Lexon rezultatin ME TE MIRE te matur, pa hamendesuar piket."""
    metrics = ROOT / "results" / "metrics.csv"
    if not metrics.exists():
        return None
    best: tuple[str, float] | None = None
    with metrics.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("instance") != problem_id or not row.get("fitness"):
                continue
            # ESA minimizon te kunderten e peshes se transportuar.
            transported = -float(row["fitness"])
            if best is None or transported > best[1]:
                best = (row["algorithm"], transported)
    return best


def self_test() -> None:
    """Kontrollon Upper Bound kunder optimumit te sakte ne raste te vogla."""
    examples = [
        [],
        [Transfer(1, 1, 1, 10.0)],
        [Transfer(1, 1, 1, 10.0), Transfer(1, 2, 2, 7.0),
         Transfer(2, 1, 3, 7.0)],
        [Transfer(1, 1, 1, -5.0), Transfer(2, 2, 2, 4.0)],
    ]
    for transfers in examples:
        best_exact = 0.0
        for size in range(len(transfers) + 1):
            for selected in combinations(range(len(transfers)), size):
                if is_valid(transfers, list(selected)):
                    best_exact = max(best_exact, total_weight(transfers, list(selected)))
        assert upper_bound(transfers) + 1e-9 >= best_exact
    assert upper_bound(examples[2]) == 17.0


def main() -> None:
    self_test()
    print("OK: Upper Bound kaloi testet e vogla.")
    rows = []
    for problem_id, path in DATASETS.items():
        if not path.exists():
            print(f"MUNGON dataset-i {problem_id}: {path}")
            continue
        transfers = load_transfers(path)
        bound = upper_bound(transfers)
        measured = best_measured_score(problem_id)

        if measured is None:
            print(f"{problem_id}: Upper Bound = {bound:.3f} (pa rezultate te matura)")
            continue

        name, score = measured
        # Kjo eshte diferenca ndaj kufirit teorik, JO gabimi real nga optimumi.
        gap = 100.0 * max(0.0, bound - score) / bound if bound > 0 else 0.0
        print(f"{problem_id}: {name} = {score:.3f} | Upper Bound = {bound:.3f} | dallimi = {gap:.2f}%")
        rows.append({
            "instance": problem_id,
            "algorithm": name,
            "transported": f"{score:.3f}",
            "upper_bound": f"{bound:.3f}",
            "gap_to_bound_pct": f"{gap:.2f}",
        })

    if rows:
        result_path = ROOT / "results" / "upper_bounds.csv"
        result_path.parent.mkdir(parents=True, exist_ok=True)
        with result_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print("Rezultatet u ruajten ne results/upper_bounds.csv")


if __name__ == "__main__":
    main()
