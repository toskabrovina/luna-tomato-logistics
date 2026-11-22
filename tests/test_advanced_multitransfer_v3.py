"""Pure structural checks; real trajectories are evaluated by ESA on the user's PC."""

import math

import numpy as np
import pytest

from src.advanced_multitransfer_v3 import (
    active_slots, combine_transfers, elliptical_capture_velocity,
    choose_destination, SLOT_COUNT, SLOT_SIZE,
)


def slot(e, m, d):
    return [float(e), float(m), float(d)] + [0.0] * (SLOT_SIZE - 3)


def baseline(e=0, m=0, d=257):
    return slot(e, m, d) + ([-1.0] + [0.0] * 20) * (SLOT_COUNT - 1)


def test_can_append_independent_transfer_without_mutating_baseline():
    original = baseline()
    combined = combine_transfers(original, slot(12, 3, 112))
    assert len(combined) == 8400
    assert len(active_slots(combined)) == 2
    assert [int(a) for a in combined[21:24]] == [12, 3, 112]
    assert original[21] == -1.0


@pytest.mark.parametrize("new", [slot(0, 3, 1), slot(1, 0, 1), slot(1, 2, 257)])
def test_rejects_conflicting_ids(new):
    with pytest.raises(ValueError):
        combine_transfers(baseline(), new)


def test_elliptical_apoapsis_vis_viva():
    a = 1_900_000.0
    e = 0.04
    mu = 4.902800118e12
    r = np.array([a * (1 + e), 0.0, 0.0])
    v = elliptical_capture_velocity(r, a, e, math.radians(10), mu)
    speed2 = float(v @ v)
    expected = mu * (2 / np.linalg.norm(r) - 1 / a)
    assert abs(speed2 - expected) / expected < 1e-12
    assert abs(float(np.dot(v, r))) / (np.linalg.norm(v) * np.linalg.norm(r)) < 1e-12


def test_destination_excludes_existing_assignment():
    class UDP:
        ltl_dict = {(3, 257): 20.0, (3, 99): 18.0, (3, 12): 0.0}
    assert choose_destination(UDP(), 3, {257}) == 99
