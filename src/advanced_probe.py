"""One reproducible Earth-to-Moon trajectory *probe* for ESA Luna Tomato Logistics.

Run in the luna-esa Miniforge environment from the project root:
    python -m src.advanced_probe

This is a diagnostic starting guess, NOT a trajectory optimiser. In particular,
its ESA fitness will normally be zero until a Moon orbit is matched precisely.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SLOTS = 400
VALUES_PER_SLOT = 21


def build_vector(earth_id, moon_id, destination_id, t0, state, impulse, duration):
    """Pack exactly one active 21-value transfer, leaving 399 slots unused."""
    position, velocity = state
    one = [
        float(earth_id), float(moon_id), float(destination_id), float(t0),
        *[float(v) for v in position], *[float(v) for v in velocity],
        *[float(v) for v in impulse],
        0.0, 0.0, 0.0,     # no middle impulse
        0.0, 0.0, 0.0,     # no last impulse
        float(duration), 0.0,
    ]
    assert len(one) == VALUES_PER_SLOT
    unused = [-1.0] + [0.0] * (VALUES_PER_SLOT - 1)
    result = one + unused * (SLOTS - 1)
    assert len(result) == SLOTS * VALUES_PER_SLOT
    return result


def best_destination(ltl_dict, moon_id):
    """Pick a destination with the highest capacity for this Moon orbit."""
    rate, destination = max(
        (float(rate), int(destination))
        for (moon, destination), rate in ltl_dict.items()
        if int(moon) == int(moon_id)
    )
    return destination, rate


def main():
    # Imports are here so the functions above remain easy to unit-test without pykep.
    from src.advanced_departures import departure_state, L, T, V, MOON_RATIO
    from src.esa_problem import load_udp

    udp = load_udp("trajectory-matching")
    earth_id, moon_id = 0, 0
    destination_id, capacity = best_destination(udp.ltl_dict, moon_id)
    state, matches_earth = departure_state(*map(float, udp.earth_data[earth_id]))
    if not matches_earth:
        raise RuntimeError("Departure does not match ESA Earth orbit. Stop here.")

    # Initial guess: a prograde translunar injection, not an optimised transfer.
    injection_mps = 3150.0
    duration_days = 4.5
    time0 = 0.0
    (x, y, z), (vx, vy, vz) = state
    inertial_velocity = [vx - y, vy + x + MOON_RATIO, vz]
    norm = math.sqrt(sum(v * v for v in inertial_velocity))
    if norm == 0:
        raise RuntimeError("Initial orbital velocity is zero")
    impulse = [injection_mps / V * v / norm for v in inertial_velocity]
    duration = duration_days * 86400.0 / T

    # Reuse the EXACT official dynamics and scoring function downloaded by VSI.
    official_propagate = udp._validate_transfer.__globals__["propagate"]
    dv_list = [impulse, [0.0] * 3, [0.0] * 3]
    final_state = official_propagate(state, time0, dv_list, [duration, 0.0])
    if final_state:
        moon_x = 1.0 - MOON_RATIO
        moon_distance_km = math.sqrt(
            (final_state[0][0] - moon_x) ** 2
            + final_state[0][1] ** 2
            + final_state[0][2] ** 2
        ) * L / 1000.0
        outcome = f"Final distance to Moon centre: {moon_distance_km:,.1f} km"
    else:
        moon_distance_km = None
        outcome = "Impact with Earth/Moon detected by ESA propagator"

    candidate = build_vector(
        earth_id, moon_id, destination_id, time0, state, impulse, duration
    )
    fitness = float(udp.fitness(candidate)[0])

    result = {
        "description": "One unoptimised physical trajectory probe; not a valid ESA submission",
        "earth_id": earth_id,
        "moon_id": moon_id,
        "destination_id": destination_id,
        "destination_capacity_kg_per_day": capacity,
        "launch_impulse_m_per_s": injection_mps,
        "flight_days": duration_days,
        "distance_from_moon_center_km": moon_distance_km,
        "official_ESA_fitness": fitness,
        "positive_delivery_confirmed": fitness < 0,
    }
    output = ROOT / "results" / "advanced_probe.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("OK: one trajectory probe evaluated with ESA's real physics.")
    print(f"Earth orbit: {earth_id} | Moon orbit: {moon_id} | Destination: {destination_id}")
    print(f"Launch impulse: {injection_mps:.0f} m/s | Flight: {duration_days} days")
    print(outcome)
    print(f"Official ESA fitness: {fitness}")
    print("IMPORTANT: Fitness 0 means no valid delivered mass. This is only a probe.")
    print(f"Saved: {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
