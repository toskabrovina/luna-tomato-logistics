"""Teste automatike per kufirin teorik te Luna Tomato Logistics."""

from itertools import combinations
import random

import pytest

from matching import Transfer, is_valid, total_weight
from upper_bound import upper_bound


def exact_optimum(transfers):
    """Kontrollon te gjitha kombinimet; perdoret vetem me shembuj te vegjel."""
    best = 0.0
    for size in range(len(transfers) + 1):
        for chosen in combinations(range(len(transfers)), size):
            if is_valid(transfers, list(chosen)):
                best = max(best, total_weight(transfers, list(chosen)))
    return best


def test_empty_input():
    assert upper_bound([]) == 0.0


def test_no_conflicts_exact_bound():
    transfers = [
        Transfer(1, 1, 1, 6.0),
        Transfer(2, 2, 2, 8.0),
        Transfer(3, 3, 3, 9.0),
    ]
    assert upper_bound(transfers) == pytest.approx(23.0)
    assert exact_optimum(transfers) == pytest.approx(23.0)


def test_conflicting_transfers_bound_is_not_below_optimum():
    transfers = [
        Transfer(1, 1, 1, 10.0),
        Transfer(1, 2, 2, 7.0),
        Transfer(2, 1, 3, 7.0),
    ]
    optimum = exact_optimum(transfers)
    assert optimum == pytest.approx(14.0)
    assert upper_bound(transfers) == pytest.approx(17.0)
    assert upper_bound(transfers) >= optimum


def test_negative_weights():
    transfers = [
        Transfer(1, 1, 1, -5.0),
        Transfer(2, 2, 2, 4.0),
    ]
    assert upper_bound(transfers) == pytest.approx(4.0)
    assert exact_optimum(transfers) == pytest.approx(4.0)


def test_small_random_cases_against_brute_force():
    rng = random.Random(42)
    for _ in range(20):
        transfers = [
            Transfer(
                rng.randint(1, 4),
                rng.randint(1, 4),
                rng.randint(1, 4),
                float(rng.randint(-5, 15)),
            )
            for _ in range(7)
        ]
        assert upper_bound(transfers) + 1e-9 >= exact_optimum(transfers)
