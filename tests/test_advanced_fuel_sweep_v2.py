"""Unit checks for score selection. ESA propagation is tested on the user's machine."""

from src.advanced_fuel_sweep_v2 import better_than


def test_accept_only_strictly_better_negative_fitness():
    assert better_than(-200.0, -194.04892254026709)
    assert not better_than(-180.0, -194.04892254026709)
    assert not better_than(0.0, -194.04892254026709)
    assert not better_than(20.0, -194.04892254026709)
    assert not better_than(-194.04892254026709, -194.04892254026709)


def test_reject_invalid_score():
    assert not better_than(float("nan"), -194.0)
    assert not better_than(float("inf"), -194.0)
    assert not better_than(float("-inf"), -194.0)
