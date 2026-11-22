"""Krahason llogaritjen tone te peshes me vleresuesin zyrtar ESA.

Vendose kete file ne tests/test_official_fitness.py.
Run: python tasks.py test
"""

from pathlib import Path

import pytest

from esa_problem import load_udp
from matching import is_valid, load_transfers, total_weight


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "spoc4" / "ltl"


@pytest.mark.parametrize(
    "problem_id, filename",
    [
        ("matching-i", "random_harder_5000.txt"),
        ("matching-ii", "random_hard_10000.txt"),
    ],
)
def test_fitness_yne_perputhet_me_esa(problem_id, filename):
    """Provon rastin bosh, nje cift te vlefshem dhe konfliktin."""
    transfers = load_transfers(DATA_DIR / filename)
    udp = load_udp(problem_id)
    assert len(transfers) == len(udp.get_bounds()[0])

    def score_esa(indices):
        vector = [0] * len(transfers)
        for index in indices:
            vector[index] = 1
        return float(udp.fitness(vector)[0])

    # 1) Asnje transfer: rezultati yne = 0, rezultati ESA = 0.
    assert total_weight(transfers, []) == 0.0
    assert score_esa([]) == pytest.approx(0.0)

    # 2) Dy transfere pa konflikt: rezultati i ESA-s eshte
    #    NEGATIVI i peshes totale qe llogarisim ne.
    first = transfers[0]
    valid_second = next(
        i for i, t in enumerate(transfers[1:], start=1)
        if t.earth != first.earth
        and t.moon != first.moon
        and t.destination != first.destination
    )
    valid_indices = [0, valid_second]
    assert is_valid(transfers, valid_indices)
    assert score_esa(valid_indices) == pytest.approx(
        -total_weight(transfers, valid_indices), abs=1e-6
    )

    # 3) Dy transfere me konflikt: te dy vleresimet duhet te japin zero.
    conflicting_second = next(
        i for i, t in enumerate(transfers[1:], start=1)
        if t.earth == first.earth
        or t.moon == first.moon
        or t.destination == first.destination
    )
    invalid_indices = [0, conflicting_second]
    assert not is_valid(transfers, invalid_indices)
    assert total_weight(transfers, invalid_indices) == 0.0
    assert score_esa(invalid_indices) == pytest.approx(0.0)
