"""Fast checks for the new mid-course shooting helper (no ESA physics needed)."""
from src.advanced_midcourse_refine import (
    build_three_burn_vector, target_position, refine_middle_impulse,
)


def test_target_side():
    assert target_position(1.0, 0.1, "near").tolist() == [0.9, 0.0, 0.0]
    assert target_position(1.0, 0.1, "far").tolist() == [1.1, 0.0, 0.0]


def test_pack_three_burns():
    # Stand-in builder: we only test ESA's first 21 values and vector shape.
    def fake_builder(e, l, d, t0, state, dv, duration):
        one = [float(e), float(l), float(d), t0,
               *state[0], *state[1], *dv,
               0., 0., 0., 0., 0., 0., duration, 0.]
        return one + ([-1.] + [0.] * 20) * 399

    result = build_three_burn_vector(
        fake_builder, 1, 2, 3, [[0., 0., 0.], [0., 0., 0.]],
        [0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9], 1.5, 2.5,
    )
    assert len(result) == 8400
    assert result[10:13] == [0.1, 0.2, 0.3]
    assert result[13:16] == [0.4, 0.5, 0.6]
    assert result[16:19] == [0.7, 0.8, 0.9]
    assert result[19:21] == [1.5, 2.5]
    assert result[21] == -1.


def test_refiner_reduces_error_on_linear_example():
    # A tiny fake propagator in which a mid-course impulse changes the endpoint.
    # This is not the ESA physics; it tests only the correction math.
    length = 3.7567696752e5  # makes V = 1 in the helper

    def propagate(state, t0, impulses, durations):
        mid = impulses[1]
        return [[0.1 + 0.001 * mid[0],
                 0.02 + 0.001 * mid[1],
                 -0.03 + 0.001 * mid[2]], [0., 0., 0.]]

    result = refine_middle_impulse(
        propagate, [[0., 0., 0.], [0., 0., 0.]],
        [0., 0., 0.], 1.0, 1.0,
        target_position(0., 0., "near"), length, max_iterations=3,
    )
    assert result["status"] == "evaluated"
    assert result["position_error_km"] < 0.01
