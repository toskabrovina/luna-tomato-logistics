"""Search cheaper Lambert starting guesses for ESA Luna Tomato Logistics Advanced.

Run from project root with the luna-esa conda environment active:
    python -m src.advanced_phase_scan

This is a screening experiment, NOT a valid lunar-orbit transfer or submission.
It varies the orientation and position on Earth orbit 0, then propagates only
three promising candidates with ESA's official dynamics.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from src.advanced_departures import L, T, V, MU_EARTH, MOON_RATIO
from src.advanced_lambert_scan import (
    initial_earth_inertial, lambert_departure_velocity,
)
from src.advanced_probe import best_destination, build_vector
from src.esa_problem import load_udp

ROOT = Path(__file__).resolve().parent.parent
ISP = 311.0
G0 = 9.80665
WET_MASS = 5000.0
DRY_MASS = 500.0
# Positive payload requires TOTAL delta-v below this value.
MAX_POSITIVE_DV = ISP * G0 * math.log(WET_MASS / DRY_MASS)


def earth_state_with_angles(pk, a, e, inc, raan, true_anomaly):
    """Pick a different valid point and orientation on the same Earth orbit."""
    position, velocity = pk.par2ic(
        [float(a), float(e), float(inc), float(raan), 0.2, float(true_anomaly)],
        MU_EARTH,
    )
    r = [float(x) for x in position]
    v = [float(x) for x in velocity]
    x, y, z = r[0] / L - MOON_RATIO, r[1] / L, r[2] / L
    vx, vy, vz = v[0] / V + y, v[1] / V - x - MOON_RATIO, v[2] / V
    return [[x, y, z], [vx, vy, vz]]


def moon_distance_km(state):
    r = state[0]
    return math.sqrt(
        (r[0] - (1.0 - MOON_RATIO))**2 + r[1]**2 + r[2]**2
    ) * L / 1000.0


def main():
    import pykep as pk

    udp = load_udp("trajectory-matching")
    validate = udp._validate_transfer.__globals__["state2earth"]
    propagate = udp._validate_transfer.__globals__["propagate"]
    earth_id, moon_id = 0, 0
    destination_id, _ = best_destination(udp.ltl_dict, moon_id)
    a, e, inc = map(float, udp.earth_data[earth_id])
    moon_a = float(udp.moon_data[moon_id][0])
    durations = (3.0, 4.5, 6.0, 7.0)
    samples = []

    print(f"Positive-payload delta-v threshold: {MAX_POSITIVE_DV:,.1f} m/s", flush=True)
    print("Searching orbital phase/orientation using Lambert (Earth-only approximation)...", flush=True)

    for k in range(12):
        raan = 2.0 * math.pi * k / 12
        for j in range(4):
            anomaly = 2.0 * math.pi * j / 4
            state = earth_state_with_angles(pk, a, e, inc, raan, anomaly)
            a2, e2, i2 = validate(state)
            if not (abs(a2 - a) / L < 1e-6 and
                    abs(e2 - e) < 1e-6 and
                    abs(i2 - inc) < 1e-6):
                raise RuntimeError("Initial orbit does not match ESA Earth orbit 0")
            r0, v0 = initial_earth_inertial(state, L, V, MOON_RATIO)

            for days in durations:
                seconds = days * 86400.0
                angle = seconds / T
                for side, radius in (("near", L - moon_a), ("far", L + moon_a)):
                    target = [radius * math.cos(angle), radius * math.sin(angle), 0.0]
                    try:
                        wanted = lambert_departure_velocity(pk, r0, target,
                                                           seconds, MU_EARTH)
                    except (ValueError, RuntimeError, OverflowError):
                        continue
                    difference = [x - y for x, y in zip(wanted, v0)]
                    burn = math.sqrt(sum(x*x for x in difference))
                    if not math.isfinite(burn):
                        continue
                    samples.append({
                        "raan_deg": 30*k,
                        "true_anomaly_deg": 90*j,
                        "flight_days": days,
                        "target_side": side,
                        "first_burn_mps": round(burn, 2),
                        "payload_upper_bound_kg": round(
                            WET_MASS*math.exp(-burn/(ISP*G0)) - DRY_MASS, 2
                        ),
                        "_state": state,
                        "_impulse": [x / V for x in difference],
                        "_duration": seconds / T,
                    })
        print(f"  Examined phase group {k + 1}/12", flush=True)

    if not samples:
        raise RuntimeError("No Lambert candidates found. Check input data.")

    samples.sort(key=lambda c: c["first_burn_mps"])
    feasible = [c for c in samples if c["first_burn_mps"] < MAX_POSITIVE_DV]
    print(f"\nCandidates evaluated: {len(samples)}")
    print(f"Candidates with potentially positive payload: {len(feasible)}")
    print("Best first-burn candidates (these are NOT validated Moon arrivals):")
    for c in samples[:5]:
        print(f"  RAAN={c['raan_deg']:3d}°, anomaly={c['true_anomaly_deg']:3d}°, "
              f"{c['flight_days']:g} days, {c['target_side']}: "
              f"{c['first_burn_mps']:,.0f} m/s | "
              f"payload upper bound={c['payload_upper_bound_kg']:,.1f} kg")

    # Avoid expensive propagations for fuel-infeasible candidates.
    # The first-burn filter is necessary, but not sufficient: capture needs fuel too.
    inspected = []
    for c in feasible[:3]:
        arrival = propagate(c["_state"], 0.0,
                            [c["_impulse"], [0.0]*3, [0.0]*3],
                            [c["_duration"], 0.0])
        vec = build_vector(earth_id, moon_id, destination_id, 0.0,
                           c["_state"], c["_impulse"], c["_duration"])
        score = float(udp.fitness(vec)[0])
        inspected.append({
            "raan_deg": c["raan_deg"],
            "true_anomaly_deg": c["true_anomaly_deg"],
            "flight_days": c["flight_days"],
            "first_burn_mps": c["first_burn_mps"],
            "moon_distance_km": round(moon_distance_km(arrival), 2) if arrival else None,
            "official_esa_fitness": score,
        })
        print(f"Official propagation: Moon distance = "
              f"{inspected[-1]['moon_distance_km']} km | fitness = {score}",
              flush=True)

    if not feasible:
        print("No candidates pass the FIRST-BURN fuel filter; change orbit or search space next.")
    else:
        print("Reminder: low burn alone does NOT prove the target Moon orbit is reached.")

    output = ROOT / "results" / "advanced_phase_scan.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({
        "status": "diagnostic_not_a_valid_submission",
        "max_positive_payload_delta_v_mps": round(MAX_POSITIVE_DV, 2),
        "candidates_evaluated": len(samples),
        "candidates_below_first_burn_threshold": len(feasible),
        "best_first_burn_candidates": [
            {k: v for k, v in c.items() if not k.startswith("_")}
            for c in samples[:10]
        ],
        "officially_propagated_candidates": inspected,
    }, indent=2), encoding="utf-8")
    print("Saved: results\\advanced_phase_scan.json")


if __name__ == "__main__":
    main()
