"""Rank fuel-feasible Lambert guesses by TRUE ESA lunar approach.

Diagnostic only. No success is claimed unless the official evaluator confirms it.
Run from Luna Tomato root, inside the luna-esa Miniforge environment:
    python -m src.advanced_arrival_scan

This reuses the student's existing phase-scan implementation, but compares
candidate arrivals using ESA's bi-circular propagator, not Lambert guesses alone.
"""
from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path

from src.advanced_departures import L, T, V, MU_EARTH, MOON_RATIO
from src.advanced_lambert_scan import (
    initial_earth_inertial, lambert_departure_velocity,
)
from src.advanced_phase_scan import (
    MAX_POSITIVE_DV, earth_state_with_angles, moon_distance_km,
)
from src.advanced_probe import best_destination, build_vector
from src.esa_problem import load_udp

ROOT = Path(__file__).resolve().parent.parent
DAYS = (3.0, 4.5, 6.0, 7.0)
SIDES = ("near", "far")
SAMPLES_PER_GROUP = 6  # 4 flight durations x 2 sides x 6 = up to 48


def choose_spread(candidates, count):
    """Include both cheap and higher-energy candidates, avoiding phase repeats."""
    by_phase = {}
    for c in sorted(candidates, key=lambda item: item["burn_mps"]):
        phase = (c["raan_deg"] + c["anomaly_deg"]) % 360
        by_phase.setdefault(phase, c)
    pool = sorted(by_phase.values(), key=lambda item: item["burn_mps"])
    if len(pool) <= count:
        return pool
    indices = {round(i * (len(pool) - 1) / (count - 1)) for i in range(count)}
    return [pool[i] for i in sorted(indices)]


def main():
    import pykep as pk

    udp = load_udp("trajectory-matching")
    propagate = udp._validate_transfer.__globals__["propagate"]
    state2moon = udp._validate_transfer.__globals__["state2moon"]
    earth_id, moon_id = 0, 0
    dest_id, _ = best_destination(udp.ltl_dict, moon_id)
    a, e, inc = map(float, udp.earth_data[earth_id])
    target_a, target_e, target_i = map(float, udp.moon_data[moon_id])
    print("Official Moon orbit target (id=0):", flush=True)
    print(f"  semi-major axis: {target_a / 1000:,.3f} km; "
          f"eccentricity: {target_e:.9f}; inclination: {target_i:.9f} rad", flush=True)
    print(f"First-burn fuel threshold (capture burn still needed): "
          f"{MAX_POSITIVE_DV:,.1f} m/s", flush=True)

    groups = defaultdict(list)
    for k in range(12):
        raan = 2 * math.pi * k / 12
        for j in range(4):
            anomaly = 2 * math.pi * j / 4
            state = earth_state_with_angles(pk, a, e, inc, raan, anomaly)
            r0, v0 = initial_earth_inertial(state, L, V, MOON_RATIO)
            for days in DAYS:
                tof = days * 86400.0
                angle = tof / T
                for side in SIDES:
                    radius = L + (-target_a if side == "near" else target_a)
                    target = [radius * math.cos(angle), radius * math.sin(angle), 0.0]
                    try:
                        departure_v = lambert_departure_velocity(
                            pk, r0, target, tof, MU_EARTH)
                        delta_v = [v - vinit for v, vinit in zip(departure_v, v0)]
                        burn = math.sqrt(sum(x*x for x in delta_v))
                        if not math.isfinite(burn) or burn >= MAX_POSITIVE_DV:
                            continue
                    except (ValueError, RuntimeError, OverflowError):
                        continue
                    groups[(days, side)].append({
                        "raan_deg": 30*k,
                        "anomaly_deg": 90*j,
                        "flight_days": days,
                        "side": side,
                        "burn_mps": burn,
                        "_state": state,
                        "_impulse": [x / V for x in delta_v],
                        "_duration": tof / T,
                    })

    chosen = []
    for days in DAYS:
        for side in SIDES:
            chosen.extend(choose_spread(groups[(days, side)], SAMPLES_PER_GROUP))
    if not chosen:
        raise RuntimeError("No candidates under the fuel threshold")
    print(f"\nOfficially propagating {len(chosen)} diverse candidates...", flush=True)

    arrivals = []
    for idx, c in enumerate(chosen, 1):
        try:
            final_state = propagate(c["_state"], 0.0,
                                    [c["_impulse"], [0.0]*3, [0.0]*3],
                                    [c["_duration"], 0.0])
            if not final_state:
                continue  # Earth or Moon impact
            moon_km = moon_distance_km(final_state)
            radius_gap_km = abs(moon_km - target_a/1000)
            row = {
                "raan_deg": c["raan_deg"],
                "anomaly_deg": c["anomaly_deg"],
                "flight_days": c["flight_days"],
                "side": c["side"],
                "first_burn_mps": round(c["burn_mps"], 1),
                "moon_distance_km": round(moon_km, 1),
                "radius_gap_km": round(radius_gap_km, 1),
                "_state": c["_state"],
                "_impulse": c["_impulse"],
                "_duration": c["_duration"],
            }
            try:
                lunar_elements = state2moon(final_state)
                row["final_lunar_a_km"] = round(float(lunar_elements[0])/1000, 3)
                row["final_lunar_e"] = round(float(lunar_elements[1]), 8)
                row["final_lunar_i_rad"] = round(float(lunar_elements[2]), 8)
            except (ValueError, RuntimeError, OverflowError):
                pass
            arrivals.append(row)
        except (ValueError, RuntimeError, OverflowError) as exc:
            print(f"  Skipping failed propagation #{idx}: {exc}", flush=True)
        if idx % 8 == 0:
            print(f"  {idx}/{len(chosen)} examined", flush=True)

    arrivals.sort(key=lambda x: (x["radius_gap_km"], x["first_burn_mps"]))
    print(f"\nPropagated without impact: {len(arrivals)}/{len(chosen)}")
    print("Closest results to the TARGET lunar-orbit radius (still NOT valid orbits):")
    for c in arrivals[:5]:
        print(f"  {c['flight_days']:g} days, RAAN {c['raan_deg']:3d}°, "
              f"anomaly {c['anomaly_deg']:3d}°: "
              f"Moon {c['moon_distance_km']:,.1f} km; "
              f"radius gap {c['radius_gap_km']:,.1f} km; "
              f"burn {c['first_burn_mps']:,.0f} m/s")

    official_scores = []
    for c in arrivals[:3]:
        vec = build_vector(earth_id, moon_id, dest_id, 0.0,
                           c["_state"], c["_impulse"], c["_duration"])
        score = float(udp.fitness(vec)[0])
        official_scores.append(score)
        print(f"  Official ESA score for candidate: {score}")

    report = ROOT / "results" / "advanced_arrival_scan.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps({
        "status": "diagnostic_not_a_valid_submission",
        "target_moon_orbit": {"a_km": target_a/1000,
                              "e": target_e, "inclination_rad": target_i},
        "num_propagated": len(chosen),
        "num_surviving": len(arrivals),
        "top_candidates": [{key: val for key, val in c.items()
                            if not key.startswith("_")} for c in arrivals[:10]],
        "official_scores_top_3": official_scores,
    }, indent=2), encoding="utf-8")
    print("Saved: results\\advanced_arrival_scan.json")
    print("IMPORTANT: Radius alone is insufficient: lunar a, e and i must match ESA tolerances.")


if __name__ == "__main__":
    main()
