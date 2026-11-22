"""Luna Tomato Logistics: refine the mid-course burn of two ESA transfer seeds.

Run from the project root in Miniforge Prompt (luna-esa):
    python -m src.advanced_midcourse_refine

This is an experiment, NOT a guaranteed valid trajectory. It uses the
OFFICIAL ESA bicircular propagator and ESA fitness for final verification.
A candidate is saved as a submission ONLY when the official score is < 0.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / "advanced_midcourse_refine.json"


def norm(vector):
    return float(np.linalg.norm(np.asarray(vector, dtype=float)))


def target_position(moon_center_x, target_radius_nd, side):
    """A simple near/far-side point on the target equatorial lunar orbit."""
    if side not in ("near", "far"):
        raise ValueError("side must be near or far")
    sign = -1.0 if side == "near" else 1.0
    return np.array([moon_center_x + sign * target_radius_nd, 0.0, 0.0])


def prepare_seeds():
    """Use one closest-arrival and one lowest-burn seed from existing scans."""
    seeds = []
    arrival = ROOT / "results" / "advanced_arrival_scan.json"
    if arrival.exists():
        rows = json.loads(arrival.read_text(encoding="utf-8")).get("top_candidates", [])
        if rows:
            row = rows[0]
            seeds.append({
                "source": "closest-arrival",
                "raan_deg": row["raan_deg"],
                "anomaly_deg": row["anomaly_deg"],
                "flight_days": row["flight_days"],
                "side": row["side"],
            })
    phase = ROOT / "results" / "advanced_phase_scan.json"
    if phase.exists():
        rows = json.loads(phase.read_text(encoding="utf-8")).get("best_first_burn_candidates", [])
        if rows:
            row = rows[0]
            seeds.append({
                "source": "lowest-first-burn",
                "raan_deg": row["raan_deg"],
                "anomaly_deg": row["true_anomaly_deg"],
                "flight_days": row["flight_days"],
                "side": row["target_side"],
            })
    if not seeds:
        raise SystemExit("First run: python -m src.advanced_arrival_scan AND python -m src.advanced_phase_scan")
    return seeds


def build_three_burn_vector(build_vector, earth_id, moon_id, destination_id,
                            state, first_burn_nd, middle_burn_nd,
                            final_burn_nd, t1_nd, t2_nd):
    """Use the existing builder and fill ESA slots for all 3 impulses and 2 arcs."""
    vector = build_vector(earth_id, moon_id, destination_id, 0.0,
                          state, first_burn_nd, t1_nd)
    vector[13:16] = [float(v) for v in middle_burn_nd]
    vector[16:19] = [float(v) for v in final_burn_nd]
    vector[19] = float(t1_nd)
    vector[20] = float(t2_nd)
    assert len(vector) == 8400
    return vector


def refine_middle_impulse(propagate, state, first_burn_nd, t1_nd, t2_nd,
                          goal, length_m, max_iterations=8):
    """Finite-difference correction of the middle burn (3 unknowns, 3 position errors).

    All three impulse components are expressed in m/s during optimisation.
    A capped Newton step and backtracking protect against unstable jumps.
    """
    middle_mps = np.zeros(3, dtype=float)
    calls = 0

    def evaluate(mid):
        nonlocal calls
        calls += 1
        try:
            final = propagate(state, 0.0,
                              [list(first_burn_nd), list(np.asarray(mid) / (length_m / 3.7567696752e5)),
                               [0.0, 0.0, 0.0]],
                              [t1_nd, t2_nd])
            if not final:
                return None, None
            error_km = (np.asarray(final[0], dtype=float) - goal) * length_m / 1000.0
            if not np.all(np.isfinite(error_km)):
                return None, None
            return error_km, final
        except (ValueError, RuntimeError, OverflowError, FloatingPointError):
            return None, None

    error, final = evaluate(middle_mps)
    if error is None:
        return {"status": "seed_impact_or_invalid", "calls": calls}
    best_error = norm(error)
    print(f"  Initial arrival error: {best_error:,.1f} km", flush=True)

    for iteration in range(max_iterations):
        if best_error < 0.001:  # 1 m, aiming tighter than ESA's orbit tolerances
            break
        # Numerical sensitivity of lunar-arrival position to mid-course delta-v.
        jacobian = np.zeros((3, 3))
        for axis in range(3):
            trial = middle_mps.copy()
            trial[axis] += 1.0  # 1 m/s finite difference
            other_error, _ = evaluate(trial)
            if other_error is None:
                trial[axis] = middle_mps[axis] - 1.0
                other_error, _ = evaluate(trial)
                if other_error is None:
                    jacobian[:, axis] = 0.0
                    continue
                jacobian[:, axis] = error - other_error
            else:
                jacobian[:, axis] = other_error - error

        if not np.all(np.isfinite(jacobian)) or norm(jacobian) < 1e-10:
            print("  No usable arrival sensitivity; stopping this seed.", flush=True)
            break

        # Damped least squares. Restrict the correction to 250 m/s per iteration.
        normal = jacobian.T @ jacobian
        gradient = jacobian.T @ error
        accepted = False
        for damping in (1e-6, 1e-3, 1e-1, 10.0):
            try:
                change = np.linalg.solve(normal + damping * np.eye(3), -gradient)
            except np.linalg.LinAlgError:
                continue
            change_length = norm(change)
            if change_length > 250.0:
                change *= 250.0 / change_length
            for multiplier in (1.0, 0.5, 0.25, 0.125):
                candidate = middle_mps + multiplier * change
                new_error, new_final = evaluate(candidate)
                if new_error is not None and norm(new_error) + 1e-7 < best_error:
                    middle_mps, error, final = candidate, new_error, new_final
                    best_error = norm(error)
                    accepted = True
                    break
            if accepted:
                break
        print(f"  iteration {iteration + 1}: error={best_error:,.3f} km; "
              f"mid-course={norm(middle_mps):,.1f} m/s; accepted={accepted}", flush=True)
        if not accepted:
            break

    return {"status": "evaluated", "middle_mps": middle_mps,
            "final_state_before_capture": final,
            "position_error_km": best_error, "calls": calls}


def main():
    import pykep as pk

    from src.advanced_capture_refine import (
        initial_guess, circular_capture_burn, lunar_state_si,
    )
    from src.advanced_departures import L, T, V, MOON_RATIO
    from src.advanced_probe import best_destination, build_vector
    from src.esa_problem import load_udp
    from src.advanced_phase_scan import MAX_POSITIVE_DV

    udp = load_udp("trajectory-matching")
    propagate = udp._validate_transfer.__globals__["propagate"]
    earth_id, moon_id = 0, 0
    destination_id, _ = best_destination(udp.ltl_dict, moon_id)
    target_a_m = float(udp.moon_data[moon_id][0])
    goal_radius_nd = target_a_m / L
    rows = []

    for seed in prepare_seeds():
        print(f"\nTrying {seed['source']} seed: {seed}", flush=True)
        try:
            state, first_mps, days, side, _ = initial_guess(pk, udp, seed)
            first_nd = (np.asarray(first_mps, dtype=float) / V).tolist()
            full_duration_nd = days * 86400.0 / T
            half_time = full_duration_nd / 2.0
            goal = target_position(1.0 - MOON_RATIO, goal_radius_nd, side)
            refined = refine_middle_impulse(propagate, state, first_nd,
                                           half_time, half_time, goal, L)
            row = {"seed": seed, "status": refined["status"],
                   "first_burn_mps": norm(first_mps),
                   "propagations": refined["calls"]}
            if refined["status"] != "evaluated":
                rows.append(row)
                continue

            mid_mps = np.asarray(refined["middle_mps"], dtype=float)
            state_before_capture = refined["final_state_before_capture"]
            final_nd, last_burn_mps = circular_capture_burn(state_before_capture)
            total_dv = norm(first_mps) + norm(mid_mps) + last_burn_mps
            vector = build_three_burn_vector(
                build_vector, earth_id, moon_id, destination_id, state,
                first_nd, (mid_mps / V).tolist(), final_nd,
                half_time, half_time,
            )
            official_fitness = float(udp.fitness(vector)[0])
            end_state = propagate(
                state, 0.0, [first_nd, (mid_mps / V).tolist(), final_nd],
                [half_time, half_time],
            )
            if end_state:
                elements = udp._validate_transfer.__globals__["state2moon"](end_state)
                a_error = abs(float(elements[0]) - target_a_m) / L
                e_error = abs(float(elements[1]) - float(udp.moon_data[moon_id][1]))
                i_error = abs(float(elements[2]) - float(udp.moon_data[moon_id][2]))
            else:
                a_error = e_error = i_error = float("inf")
            row.update({
                "position_error_km": refined["position_error_km"],
                "middle_burn_mps": norm(mid_mps),
                "capture_burn_mps": last_burn_mps,
                "total_delta_v_mps": total_dv,
                "fuel_feasible": total_dv < MAX_POSITIVE_DV,
                "normalized_orbital_errors": {"a": a_error, "e": e_error, "i": i_error},
                "official_ESA_fitness": official_fitness,
                "valid_delivery": official_fitness < 0,
            })
            print(f"  Total delta-v: {total_dv:,.0f} m/s "
                  f"(positive-payload limit {MAX_POSITIVE_DV:,.0f})")
            print(f"  Orbit errors (a/L,e,i): {a_error:.3g}, {e_error:.3g}, {i_error:.3g}")
            print(f"  OFFICIAL ESA FITNESS: {official_fitness}", flush=True)
            if official_fitness < 0:
                from vsi.esa import write_submission
                out = ROOT / "results" / "submission_trajectory-matching_midcourse.json"
                write_submission("spoc-4-luna-tomato-logistics",
                                 "trajectory-matching", vector, str(out))
                print(f"  VALID DELIVERY! Submission saved to {out}", flush=True)
            rows.append(row)
        except (ValueError, RuntimeError, OverflowError, FloatingPointError) as exc:
            rows.append({"seed": seed, "status": "error", "reason": str(exc)})
            print(f"  Could not refine this seed: {exc}", flush=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"description": "2-arc ESA diagnostic (not a valid delivery unless score < 0)",
                               "candidates": rows}, indent=2), encoding="utf-8")
    print(f"\nSaved: {OUT.relative_to(ROOT)}")
    if not any(row.get("valid_delivery") for row in rows):
        print("No valid ESA delivery found. Do NOT mark Advanced as complete.")


if __name__ == "__main__":
    main()
