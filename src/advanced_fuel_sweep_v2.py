"""ESA Luna Tomato Logistics: extend fuel sweep without losing the verified best.

Run (luna-esa) from project root:
    python -m src.advanced_fuel_sweep_v2

Checks multiple midcourse fractions for all 10 precomputed seeds. Every trial
uses official ESA dynamics and fitness. The known good solution is never
changed; improvements go to a separate submission file.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from src.advanced_fuel_sweep import (
    inclined_circular_velocity, load_scan_seeds, norm, ROOT,
)

BASELINE = ROOT / "results" / "best_trajectory-matching.json"
REPORT = ROOT / "results" / "advanced_fuel_sweep_v2.json"
IMPROVED_SUBMISSION = ROOT / "results" / "submission_trajectory-matching_v2.json"
TIME_FRACTIONS = (0.35, 0.50, 0.65)


def better_than(score: float, incumbent: float) -> bool:
    """Official ESA fitness is minimized; valid deliveries have negative fitness."""
    return (math.isfinite(score) and score < 0.0
            and score < incumbent - 1e-9)


def baseline_score(udp) -> float:
    """Refuse to continue if the previously verified solution is unavailable."""
    if not BASELINE.is_file():
        raise SystemExit(
            "Missing results/best_trajectory-matching.json. "
            "Restore the verified -194 candidate before trying improvements."
        )
    data = json.loads(BASELINE.read_text(encoding="utf-8"))
    vector = data[0]["decisionVector"]
    score = float(udp.fitness(vector)[0])
    if not math.isfinite(score) or score >= 0.0:
        raise SystemExit(f"Saved baseline no longer validates: ESA fitness={score}")
    return score


def main():
    import pykep as pk

    from src.advanced_capture_refine import initial_guess, lunar_state_si
    from src.advanced_departures import L, T, V, MU_MOON, MOON_RATIO
    from src.advanced_midcourse_refine import (
        build_three_burn_vector, refine_middle_impulse, target_position,
    )
    from src.advanced_probe import best_destination, build_vector
    from src.esa_problem import load_udp
    from vsi.esa import write_submission

    udp = load_udp("trajectory-matching")
    physics = udp._validate_transfer.__globals__
    propagate, state2moon = physics["propagate"], physics["state2moon"]
    baseline = baseline_score(udp)
    best = baseline

    earth_id = moon_id = 0
    destination_id, _ = best_destination(udp.ltl_dict, moon_id)
    moon_a, moon_e, moon_i = map(float, udp.moon_data[moon_id])
    if abs(moon_e) >= 1e-6:
        raise SystemExit("Circular-capture model cannot handle this target eccentricity")

    seeds = load_scan_seeds()
    if not seeds:
        raise SystemExit("No candidate seeds in results/ scan files")
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    report = {
        "method": "10 candidate seeds, 3 midcourse timing fractions, official ESA scoring",
        "baseline_fitness": baseline,
        "best_fitness_seen": best,
        "best_new_submission": None,
        "candidates": rows,
    }

    def checkpoint():
        report["best_fitness_seen"] = best
        REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Verified baseline ESA fitness: {baseline:.9f}", flush=True)
    print(f"Testing {len(seeds)} seeds x {len(TIME_FRACTIONS)} midcourse timing fractions.", flush=True)
    print("Original best_trajectory-matching.json will NOT be overwritten.", flush=True)
    checkpoint()

    for index, seed in enumerate(seeds, 1):
        print(f"\nSeed {index}/{len(seeds)}: {seed}", flush=True)
        try:
            state, first_mps, days, side, _ = initial_guess(pk, udp, seed)
            first_nd = (np.asarray(first_mps, dtype=float) / V).tolist()
            total_duration_nd = days * 86400.0 / T
            goal = target_position(1.0 - MOON_RATIO, moon_a / L, side)
        except (ValueError, RuntimeError, OverflowError, FloatingPointError) as exc:
            rows.append({"seed": seed, "status": "initial_guess_error", "message": str(exc)})
            checkpoint()
            continue

        for fraction in TIME_FRACTIONS:
            print(f"  Fraction {fraction:.2f}", flush=True)
            row = {"seed": seed, "fraction": fraction, "first_burn_mps": norm(first_mps)}
            try:
                t1, t2 = total_duration_nd * fraction, total_duration_nd * (1.0 - fraction)
                fit = refine_middle_impulse(
                    propagate, state, first_nd, t1, t2, goal, L,
                    max_iterations=10,
                )
                row.update(status=fit["status"], propagations=int(fit["calls"]))
                if fit["status"] != "evaluated":
                    rows.append(row)
                    checkpoint()
                    continue

                middle = np.asarray(fit["middle_mps"], dtype=float)
                final_before = fit["final_state_before_capture"]
                r_si, v_si = lunar_state_si(final_before)
                wanted_v = inclined_circular_velocity(r_si, MU_MOON, moon_i)
                capture_nd = ((wanted_v - v_si) / V).tolist()
                capture_mps = norm(wanted_v - v_si)
                total_dv = norm(first_mps) + norm(middle) + capture_mps

                vector = build_three_burn_vector(
                    build_vector, earth_id, moon_id, destination_id, state,
                    first_nd, (middle / V).tolist(), capture_nd, t1, t2,
                )
                score = float(udp.fitness(vector)[0])
                end = propagate(state, 0.0, [first_nd, (middle / V).tolist(), capture_nd], [t1, t2])
                if end:
                    elements = state2moon(end)
                    errors = [abs(float(elements[0]) - moon_a) / L,
                              abs(float(elements[1]) - moon_e),
                              abs(float(elements[2]) - moon_i)]
                else:
                    errors = [float("inf")] * 3

                row.update({
                    "status": "evaluated",
                    "position_error_km": float(fit["position_error_km"]),
                    "middle_burn_mps": norm(middle),
                    "capture_burn_mps": capture_mps,
                    "total_delta_v_mps": total_dv,
                    "orbit_errors_a_over_L_e_i": errors,
                    "official_ESA_fitness": score,
                    "valid_delivery": score < 0.0,
                })
                print(f"  Total dV={total_dv:,.1f} m/s | ESA fitness={score:.9f}", flush=True)
                if better_than(score, best):
                    # Re-check before writing; never touch baseline JSON.
                    confirmed = float(udp.fitness(vector)[0])
                    if better_than(confirmed, best):
                        best = confirmed
                        write_submission(
                            "spoc-4-luna-tomato-logistics", "trajectory-matching",
                            vector, str(IMPROVED_SUBMISSION),
                        )
                        report["best_new_submission"] = str(IMPROVED_SUBMISSION.relative_to(ROOT))
                        print(f"  NEW BEST! {best:.9f} saved: {IMPROVED_SUBMISSION}", flush=True)
                rows.append(row)
            except (ValueError, RuntimeError, OverflowError, FloatingPointError) as exc:
                row.update(status="error", message=str(exc))
                rows.append(row)
                print(f"  Candidate failed: {exc}", flush=True)
            checkpoint()

    print(f"\nBaseline ESA fitness: {baseline:.9f}", flush=True)
    print(f"Best ESA fitness found: {best:.9f}", flush=True)
    if report["best_new_submission"]:
        print(f"Improved candidate saved separately: {report['best_new_submission']}")
    else:
        print("No improvement found; the original verified best remains unchanged.")
    print(f"Diagnostic results: {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
