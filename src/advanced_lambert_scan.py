"""Lambert initial guesses for ESA Luna Tomato Logistics: Trajectory Matching.

This is a diagnostic / initialisation step, NOT a valid advanced submission.
Use in Miniforge Prompt from the Luna Tomato project root:
    python -m src.advanced_lambert_scan

Lambert uses a simplified Earth-only two-body model. Every candidate is then
propagated with the official ESA bi-circular model before being reported.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def euclidean_distance(a, b):
    return math.sqrt(sum((float(x) - float(y)) ** 2 for x, y in zip(a, b)))


def initial_earth_inertial(state, L, V, mu):
    """Undo the official Earth-centred rotating-frame conversion at t0=0."""
    (x, y, z), (vx, vy, vz) = state
    r0 = [(x + mu) * L, y * L, z * L]
    v0 = [(vx - y) * V, (vy + x + mu) * V, vz * V]
    return r0, v0


def lambert_departure_velocity(pk, r0, r1, tof_seconds, mu_earth):
    """Support both the older PyKEP 2 and the current PyKEP API."""
    arc = pk.lambert_problem(r0, r1, tof_seconds, mu_earth)
    if hasattr(arc, "get_v1"):
        return [float(x) for x in arc.get_v1()[0]]
    return [float(x) for x in arc.v0[0]]


def main():
    import pykep as pk
    from src.advanced_departures import (
        L, T, V, MU_EARTH, MOON_RATIO, departure_state,
    )
    from src.advanced_probe import build_vector, best_destination
    from src.esa_problem import load_udp

    udp = load_udp("trajectory-matching")
    earth_id, moon_id = 0, 0
    destination_id, _ = best_destination(udp.ltl_dict, moon_id)
    state, ok = departure_state(*[float(v) for v in udp.earth_data[earth_id]])
    if not ok:
        raise RuntimeError("Departure orbit does not match the ESA input")

    r0, v0 = initial_earth_inertial(state, L, V, MOON_RATIO)
    # This is a rough moon-centred target radius, not an exact lunar orbit.
    lunar_radius = abs(float(udp.moon_data[moon_id][0]))
    moon_center_rot = 1.0 - MOON_RATIO
    propagate = udp._validate_transfer.__globals__["propagate"]
    samples = []

    # Eight inexpensive *initial guesses*: 4 flight durations, 2 targets.
    for flight_days in (3.0, 4.5, 6.0, 7.0):
        tof = flight_days * 86400.0
        tau = tof / T
        c, s = math.cos(tau), math.sin(tau)
        for side, distance_from_earth in (
            ("near", L - lunar_radius),
            ("far", L + lunar_radius),
        ):
            try:
                # At arrival the Moon is moving in Earth's inertial frame.
                target = [distance_from_earth * c, distance_from_earth * s, 0.0]
                wanted_v0 = lambert_departure_velocity(pk, r0, target, tof, MU_EARTH)
                impulse_mps = [a - b for a, b in zip(wanted_v0, v0)]
                burn_mps = math.sqrt(sum(d * d for d in impulse_mps))
                impulse = [d / V for d in impulse_mps]
                duration = tof / T
                # Use the *exact* official BCP propagator to evaluate this guess.
                final_state = propagate(
                    state, 0.0,
                    [impulse, [0.0] * 3, [0.0] * 3],
                    [duration, 0.0],
                )
                if not final_state:
                    samples.append({
                        "flight_days": flight_days, "target_side": side,
                        "initial_impulse_mps": round(burn_mps, 2),
                        "status": "impact_or_invalid_propagation",
                    })
                    continue
                x, y, z = final_state[0]
                dist_km = math.sqrt(
                    (x - moon_center_rot) ** 2 + y ** 2 + z ** 2
                ) * L / 1000.0
                samples.append({
                    "flight_days": flight_days,
                    "target_side": side,
                    "initial_impulse_mps": round(burn_mps, 2),
                    "final_moon_distance_km": round(dist_km, 2),
                    "target_lunar_orbit_radius_km": round(lunar_radius / 1000, 2),
                    "distance_error_km": round(abs(dist_km - lunar_radius / 1000), 2),
                    "status": "propagated",
                    # Needed to re-evaluate *only the best* guess officially.
                    "_impulse": impulse,
                    "_duration": duration,
                })
                print(
                    f"{flight_days:>3g} days, {side:>4s}: "
                    f"Moon distance = {dist_km:,.0f} km | "
                    f"first burn = {burn_mps:,.0f} m/s",
                    flush=True,
                )
            except (ValueError, OverflowError, RuntimeError) as exc:
                samples.append({
                    "flight_days": flight_days, "target_side": side,
                    "status": "error", "detail": str(exc),
                })
                print(f"{flight_days:>3g} days, {side:>4s}: {exc}", flush=True)

    usable = [s for s in samples if s["status"] == "propagated"]
    if usable:
        best = min(usable, key=lambda s: s["distance_error_km"])
        vector = build_vector(
            earth_id, moon_id, destination_id, 0.0,
            state, best["_impulse"], best["_duration"],
        )
        score = float(udp.fitness(vector)[0])
        best_summary = {
            key: value for key, value in best.items() if not key.startswith("_")
        }
        best_summary["official_ESA_fitness"] = score
        print("\nBest Lambert starting guess:")
        print(
            f"  {best['flight_days']} days, {best['target_side']}: "
            f"final Moon distance {best['final_moon_distance_km']:,.1f} km"
        )
        print(f"  Official ESA fitness: {score}")
        if score == 0:
            print("  NOT A VALID DELIVERY YET: exact lunar-orbit matching is still needed.")
    else:
        best_summary = None
        print("\nNo candidate survived the official propagation; report is saved.")

    # Do not output a misleading submission; these are initial guesses only.
    output = ROOT / "results" / "advanced_lambert_scan.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    cleaned = [
        {k: v for k, v in s.items() if not k.startswith("_")}
        for s in samples
    ]
    output.write_text(json.dumps({
        "note": "Lambert two-body starting guesses, validated with ESA propagation. NOT a submission.",
        "candidates": cleaned,
        "best": best_summary,
    }, indent=2), encoding="utf-8")
    print(f"Saved: {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
