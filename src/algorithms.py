"""Algoritmet per ESA Luna Tomato Logistics.

Random Search eshte zgjidhja baze e VSI-se.
Greedy dhe Local Search (2-swap) jane algoritmet tona per Matching I dhe II.
"""

from __future__ import annotations

import random
import time
from pathlib import Path

from matching import Transfer, is_valid, load_transfers
from vsi.pareto import pareto_filter


ROOT = Path(__file__).resolve().parent.parent
DATASETS = (
    ROOT / "data" / "spoc4" / "ltl" / "random_harder_5000.txt",  # Matching I
    ROOT / "data" / "spoc4" / "ltl" / "random_hard_10000.txt",    # Matching II
)


def random_vector(udp, rng):
    """Krijon nje kandidat rastesor (kodi baze i VSI-se)."""
    lower, upper = udp.get_bounds()
    n_int = udp.get_nix() if hasattr(udp, "get_nix") else 0
    n = len(lower)
    x = []
    for i in range(n):
        integer = i >= n - n_int or (
            isinstance(lower[i], int) and isinstance(upper[i], int)
        )
        if integer:
            x.append(rng.randint(int(lower[i]), int(upper[i])))
        else:
            x.append(rng.uniform(lower[i], upper[i]))
    return x


def n_objectives(udp) -> int:
    return udp.get_nobj() if hasattr(udp, "get_nobj") else 1


def random_search(udp, budget_seconds, meter, rng):
    """Baseline i VSI-se: kandidatet rastesisht brenda kohes se lejuar."""
    multi = n_objectives(udp) >= 2
    archive = []
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


def greedy_indices(transfers: list[Transfer]) -> list[int]:
    """Zgjedh transferet me peshen me te madhe, pa perseritur E, L apo D.

    Kompleksiteti: O(n log n) kohe per renditje dhe O(n) hapesire.
    Greedy nuk garanton zgjidhjen optimale.
    """
    used_earth = set()
    used_moon = set()
    used_destinations = set()
    selected = []

    # Sipas peshes, prej me te madhes tek me e vogla.
    ordered_indices = sorted(
        range(len(transfers)), key=lambda i: transfers[i].weight, reverse=True
    )

    for index in ordered_indices:
        t = transfers[index]
        if t.weight <= 0:
            break  # Nje transfer pa peshe pozitive nuk na ndihmon.
        if (t.earth in used_earth or
                t.moon in used_moon or
                t.destination in used_destinations):
            continue
        selected.append(index)
        used_earth.add(t.earth)
        used_moon.add(t.moon)
        used_destinations.add(t.destination)

    return selected


def greedy_by_weight(udp, budget_seconds, meter, rng):
    """Lidh Greedy me evaluatorin zyrtar ESA dhe VSI.

    Parametrat budget_seconds dhe rng nuk duhen per kete algoritem
    determinist, por ruhen per t'u pershtatur me nderfaqen e VSI-se.
    """
    dimension = len(udp.get_bounds()[0])

    # E dallojme Matching I nga Matching II sipas gjatesise se vektorit.
    for path in DATASETS:
        if not path.exists():
            continue
        transfers = load_transfers(path)
        if len(transfers) != dimension:
            continue

        indices = greedy_indices(transfers)
        assert is_valid(transfers, indices), "Greedy krijoi nje zgjidhje me konflikt!"

        # ESA kerkon nje 0/1 per CDO transfer, ne rendin origjinal.
        decision_vector = [0] * len(transfers)
        for index in indices:
            decision_vector[index] = 1

        # Kontrollojme rezultatin me funksionin ZYRTAR te ESA-s.
        official_score = float(udp.fitness(decision_vector)[0])
        meter.count()
        meter.record(official_score)
        return [decision_vector]

    # Trajectory-matching nuk zgjidhet nga ky Greedy.
    return []



def _compatible(a: Transfer, b: Transfer) -> bool:
    """A mund t'i zgjedhim keto dy transfere bashke?"""
    return (a.earth != b.earth and a.moon != b.moon
            and a.destination != b.destination)


def improve_two_swap(
    transfers: list[Transfer],
    initial_indices: list[int],
    deadline: float,
    meter=None,
) -> list[int]:
    """Local Search: zevendeso 1 transfer me 2 me peshe totale me te madhe.

    Dy transferet e rinj duhet te jene ne konflikt VETEM me transferin
    qe hiqet, dhe jo me njeri-tjetrin. Keshtu zgjidhja mbetet e vlefshme.
    Kufiri kohor na pengon me bere kerkime pa fund ne instancat e medha.
    """
    chosen = set(initial_indices)
    assert is_valid(transfers, list(chosen))
    limit_per_transfer = 35  # mban kerkimin te shpejte ne 92,103 transfere
    epsilon = 1e-9

    while time.perf_counter() < deadline:
        # Per secilen orbite/destinacion, ruaj transferin qe e ka zene.
        owner_e = {transfers[i].earth: i for i in chosen}
        owner_l = {transfers[i].moon: i for i in chosen}
        owner_d = {transfers[i].destination: i for i in chosen}

        # Kandidatet qe bllokohen nga SAKTESISHT nje transfer i zgjedhur.
        candidates: dict[int, list[int]] = {}
        for idx, transfer in enumerate(transfers):
            if idx in chosen:
                continue
            blockers = {
                owner for owner in (
                    owner_e.get(transfer.earth),
                    owner_l.get(transfer.moon),
                    owner_d.get(transfer.destination),
                ) if owner is not None
            }
            if len(blockers) == 1:
                blocked = next(iter(blockers))
                candidates.setdefault(blocked, []).append(idx)

        # Gjej nje zevendesim qe na e rrit peshen totale.
        replacement = None
        for old_idx, candidate_ids in candidates.items():
            if time.perf_counter() >= deadline:
                break
            if len(candidate_ids) < 2:
                continue
            candidate_ids.sort(key=lambda i: transfers[i].weight, reverse=True)
            shortlist = candidate_ids[:limit_per_transfer]
            old_weight = transfers[old_idx].weight
            for pos, a_idx in enumerate(shortlist):
                a = transfers[a_idx]
                # Lista eshte e renditur: me tutje peshat jane me te vogla.
                if pos + 1 >= len(shortlist) or (
                    a.weight + transfers[shortlist[pos + 1]].weight
                    <= old_weight + epsilon
                ):
                    break
                for b_idx in shortlist[pos + 1:]:
                    b = transfers[b_idx]
                    if a.weight + b.weight <= old_weight + epsilon:
                        break
                    if meter is not None:
                        meter.count()  # nje kombinim i shqyrtuar
                    if _compatible(a, b):
                        replacement = (old_idx, a_idx, b_idx)
                        break
                if replacement is not None:
                    break
            if replacement is not None:
                break

        if replacement is None:
            break
        old_idx, a_idx, b_idx = replacement
        chosen.remove(old_idx)
        chosen.add(a_idx)
        chosen.add(b_idx)

    # Pas zevendesimeve, ploteso me transfere pozitive pa konflikt.
    # Kjo e ben rezultatin te pakten aq te mire sa para ketij hapi.
    owner_e = {transfers[i].earth for i in chosen}
    owner_l = {transfers[i].moon for i in chosen}
    owner_d = {transfers[i].destination for i in chosen}
    for idx in sorted(range(len(transfers)),
                      key=lambda i: transfers[i].weight, reverse=True):
        t = transfers[idx]
        if t.weight <= 0:
            break
        if (t.earth not in owner_e and t.moon not in owner_l
                and t.destination not in owner_d):
            chosen.add(idx)
            owner_e.add(t.earth)
            owner_l.add(t.moon)
            owner_d.add(t.destination)

    result = sorted(chosen)
    assert is_valid(transfers, result), "Local Search prodhoi konflikt!"
    return result


def local_search(udp, budget_seconds, meter, rng):
    """Nis nga Greedy, pastaj ben 2-swap per sa kohe ka buxhet."""
    deadline = time.perf_counter() + max(0.0, budget_seconds)
    dimension = len(udp.get_bounds()[0])
    for path in DATASETS:
        if not path.exists():
            continue
        transfers = load_transfers(path)
        if len(transfers) != dimension:
            continue

        greedy = greedy_indices(transfers)
        selected = improve_two_swap(transfers, greedy, deadline, meter)
        vector = [0] * len(transfers)
        for idx in selected:
            vector[idx] = 1

        score = float(udp.fitness(vector)[0])  # ESA: kontrolli perfundimtar
        meter.count()
        meter.record(score)
        return [vector]

    return []  # Trajectory Matching ka model tjeter


ALGORITHMS = {
    "random_search": random_search,
    "greedy": greedy_by_weight,
    "local_search": local_search,
}


if __name__ == "__main__":
    # Test me nje rast ku Greedy NUK gjen zgjidhjen me te mire.
    example = [
        Transfer(1, 1, 1, 10.0),
        Transfer(1, 2, 2, 7.0),
        Transfer(2, 1, 3, 7.0),
    ]
    greedy = greedy_indices(example)
    improved = improve_two_swap(example, greedy, time.perf_counter() + 2.0)
    assert is_valid(example, improved)
    assert sum(example[i].weight for i in greedy) == 10.0
    assert sum(example[i].weight for i in improved) == 14.0
    print("OK: Greedy = 10, Local Search = 14 (pa konflikte).")
