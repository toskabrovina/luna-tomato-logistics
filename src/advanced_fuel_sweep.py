"""Search diverse ESA Earth-to-Moon seeds for a fuel-feasible, matching lunar orbit.

Run from the Luna Tomato project root in the luna-esa environment:
    python -m src.advanced_fuel_sweep

Reuses the student's earlier Lambert guesses and midcourse Newton corrector.
This is an experimental diagnostic: success requires OFFICIAL ESA fitness < 0.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "results" / "advanced_fuel_sweep.json"
MAX_SEEDS = 10
TIME_FRACTIONS = (0.5,)  # Fraction of flight spent before the mid-course burn.


def norm(values):
    return float(np.linalg.norm(np.asarray(values, dtype=float)))


def seed_variations(arrival_rows, phase_rows, max_seeds=MAX_SEEDS):
    """Choose different phases/durations rather than repeatedly using two seeds."""
    candidates = []
    for row in arrival_rows:
        candidates.append({
            "source": "arrival", "raan_deg": float(row["raan_deg"]),
            "anomaly_deg": float(row["anomaly_deg"]),
            "flight_days": float(row["flight_days"]), "side": row["side"],
        })
    for row in phase_rows:
        candidates.append({
            "source": "low-first-burn", "raan_deg": float(row["raan_deg"]),
            "anomaly_deg": float(row["true_anomaly_deg"]),
            "flight_days": float(row["flight_days"]), "side": row["target_side"],
        })
    unique, seen = [], set()
    for row in candidates:
        key = (row["raan_deg"], row["anomaly_deg"], row["flight_days"], row["side"])
        if key not in seen:
            unique.append(row)
            seen.add(key)
    # Interleave closest approach and cheapest first-burn candidates, making
    # the 10-seed budget cover both objectives (rather than all arrivals first).
    a = [row for row in unique if row["source"] == "arrival"]
    p = [row for row in unique if row["source"] == "low-first-burn"]
    selected = []
    for i in range(max(len(a), len(p))):
        if i < len(a):
            selected.append(a[i])
        if i < len(p):
            selected.append(p[i])
        if len(selected) >= max_seeds:
            break
    return selected[:max_seeds]


def inclined_circular_velocity(r_si, mu_moon, inclination):
    """Circular lunar velocity with target inclination when geometry permits.

    A circular orbit has e=0. This suffices ONLY if the ESA target's
    eccentricity differs from zero by less than its official tolerance.
    """
    r = np.asarray(r_si, dtype=float)
    radius = norm(r)
    rxy = math.hypot(float(r[0]), float(r[1]))
    if radius == 0.0 or rxy < 1.0:
        raise ValueError("Cannot construct lunar circular orbit at this position")
    i = float(inclination)
    if not 0 <= i <= math.pi:
        raise ValueError("Invalid inclination")
    s, c = math.sin(i), math.cos(i)
    # h is perpendicular to r and has inclination i. Its planar component
    # has length sin(i), and its z component is cos(i).
    radial_planar = -c * float(r[2]) / rxy
    if abs(radial_planar) > s + 1e-12:
        # An exact inclination-i plane cannot pass through this position.
        raise ValueError("Arrival too far from target inclination plane")
    transverse_planar = math.sqrt(max(0.0, s*s - radial_planar*radial_planar))
    xhat, yhat = float(r[0]) / rxy, float(r[1]) / rxy
    h = np.array([
        radial_planar*xhat - transverse_planar*yhat,
        radial_planar*yhat + transverse_planar*xhat,
        c,
    ])
    tangent = np.cross(h, r / radius)
    tangent /= norm(tangent)
    return math.sqrt(float(mu_moon) / radius) * tangent


def load_scan_seeds():
    arrival_path = ROOT / "results" / "advanced_arrival_scan.json"
    phase_path = ROOT / "results" / "advanced_phase_scan.json"
    if not arrival_path.exists() or not phase_path.exists():
        raise SystemExit(
            "Need both scan files. Run 'python -m src.advanced_arrival_scan' "
            "and 'python -m src.advanced_phase_scan' first."
        )
    arrival = json.loads(arrival_path.read_text(encoding="utf-8"))
    phase = json.loads(phase_path.read_text(encoding="utf-8"))
    return seed_variations(
        arrival.get("top_candidates", []),
        phase.get("best_first_burn_candidates", []),
    )


def main():
    import pykep as pk
    from src.advanced_capture_refine import initial_guess, lunar_state_si
    from src.advanced_departures import L, T, V, MU_MOON, MOON_RATIO
    from src.advanced_midcourse_refine import (
        build_three_burn_vector, refine_middle_impulse, target_position,
    )
    from src.advanced_probe import best_destination, build_vector
    from src.advanced_phase_scan import MAX_POSITIVE_DV
    from src.esa_problem import load_udp

    udp = load_udp("trajectory-matching")
    physics = udp._validate_transfer.__globals__
    propagate, state2moon = physics["propagate"], physics["state2moon"]
    earth_id = moon_id = 0
    destination_id, _ = best_destination(udp.ltl_dict, moon_id)
    moon_a, moon_e, moon_i = map(float, udp.moon_data[moon_id])
    if abs(moon_e) >= 1e-6:
        raise RuntimeError(
            "Moon orbit target is too eccentric for this circular-capture strategy"
        )
    seeds = load_scan_seeds()
    if not seeds:
        raise SystemExit("Scans contain no candidates")
    print(f"Testing {len(seeds)} varied seeds; max positive-mass ΔV {MAX_POSITIVE_DV:,.0f} m/s", flush=True)
    rows = []
    for index, seed in enumerate(seeds, 1):
        print(f"\nSeed {index}/{len(seeds)}: {seed}", flush=True)
        try:
            state, first_mps, days, side, _ = initial_guess(pk, udp, seed)
            first_nd = (np.asarray(first_mps, dtype=float) / V).tolist()
            total_duration_nd = days * 86400.0 / T
            goal = target_position(1.0 - MOON_RATIO, moon_a/L, side)
            for fraction in TIME_FRACTIONS:
                t1 = total_duration_nd * fraction
                t2 = total_duration_nd * (1 - fraction)
                refined = refine_middle_impulse(
                    propagate, state, first_nd, t1, t2, goal, L,
                    max_iterations=10,
                )
                result = {
                    "seed": seed, "fraction": fraction,
                    "status": refined["status"],
                    "first_burn_mps": norm(first_mps),
                    "propagations": refined["calls"],
                }
                if refined["status"] != "evaluated":
                    rows.append(result)
                    continue
                middle = np.asarray(refined["middle_mps"], dtype=float)
                final_before_capture = refined["final_state_before_capture"]
                r_si, v_si = lunar_state_si(final_before_capture)
                try:
                    wanted_velocity = inclined_circular_velocity(r_si, MU_MOON, moon_i)
                    final_nd = ((wanted_velocity - v_si) / V).tolist()
                    capture_mps = norm(wanted_velocity - v_si)
                    status = "candidate"
                except ValueError as exc:
                    # Do not treat off-plane arrival as a successful trajectory.
                    result.update(status="off_target_plane", message=str(exc),
                                  position_error_km=float(refined["position_error_km"]))
                    rows.append(result)
                    print("  Arrival not on target orbital plane; continuing.", flush=True)
                    continue
                total_dv = norm(first_mps) + norm(middle) + capture_mps
                vec = build_three_burn_vector(
                    build_vector, earth_id, moon_id, destination_id, state,
                    first_nd, (middle / V).tolist(), final_nd, t1, t2,
                )
                official_score = float(udp.fitness(vec)[0])
                completed = propagate(
                    state, 0.0, [first_nd, (middle / V).tolist(), final_nd], [t1, t2],
                )
                if completed:
                    lunar_elements = state2moon(completed)
                    errors = [abs(float(lunar_elements[0])-moon_a)/L,
                              abs(float(lunar_elements[1])-moon_e),
                              abs(float(lunar_elements[2])-moon_i)]
                else:
                    errors = [float("inf")]*3
                result.update({
                    "status": status,
                    "position_error_km": float(refined["position_error_km"]),
                    "middle_burn_mps": norm(middle),
                    "capture_burn_mps": capture_mps,
                    "total_delta_v_mps": total_dv,
                    "fuel_feasible": total_dv < MAX_POSITIVE_DV,
                    "orbit_errors_a_over_L_e_i": errors,
                    "official_ESA_fitness": official_score,
                    "valid_delivery": official_score < 0,
                })
                rows.append(result)
                print(f"  position error={result['position_error_km']:,.3f} km; "
                      f"total ΔV={total_dv:,.1f} m/s; "
                      f"orbit errors={errors}; ESA fitness={official_score}", flush=True)
                if official_score < 0:
                    from vsi.esa import write_submission
                    submission = ROOT / "results" / "submission_trajectory-matching_sweep.json"
                    write_submission("spoc-4-luna-tomato-logistics",
                                     "trajectory-matching", vec, str(submission))
                    print(f"VALID ESA delivery saved to {submission}", flush=True)
                    break
        except (ValueError, RuntimeError, OverflowError, FloatingPointError) as exc:
            print(f"  Seed failed: {exc}", flush=True)
            rows.append({"seed": seed, "status": "error", "reason": str(exc)})
        if rows and rows[-1].get("valid_delivery"):
            break

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps({
        "status": "official_positive_fitness_check_required",
        "seeds_tried": len(set((str(row['seed'])) for row in rows)),
        "target_moon_orbit": {"a_m": moon_a, "e": moon_e, "i_rad": moon_i},
        "candidates": rows,
    }, indent=2), encoding="utf-8")
    print(f"\nSaved {OUTPUT.relative_to(ROOT)}")
    if not any(row.get("valid_delivery") for row in rows):
        print("NO VALID DELIVERY YET. Do not tick Advanced.")


if __name__ == "__main__":
    main()
