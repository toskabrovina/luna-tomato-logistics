"""ESA SpOC4 Luna Tomato Logistics: safely try a SECOND independent transfer.

Usage (from project root, in the luna-esa environment):
    python -m src.advanced_multitransfer_v3
    python -m src.advanced_multitransfer_v3 --pairs 10

Reads the successful single-transfer v2 submission, tries alternative Earth/Moon
orbit pairs, and writes a two-transfer submission ONLY after ESA's official
fitness confirms improvement. The original v2 file is never modified.

This is a small pilot toward the 400-transfer Advanced problem, not a promise
of a high leaderboard rank. May take minutes because ESA propagation is costly.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / "results" / "submission_trajectory-matching_v2.json"
REPORT = ROOT / "results" / "advanced_multitransfer_v3.json"
OUTPUT = ROOT / "results" / "submission_trajectory-matching_v3.json"
SLOT_SIZE = 21
SLOT_COUNT = 400
TOL = 1e-6
FIRST_BURN_CAP_MPS = 5500.0   # screen out candidates unlikely to retain payload
PHASES = ((210.0, 0.0, 3.0), (150.0, 90.0, 3.0))
MIDCOURSE_FRACTION = 0.35


def active_slots(vector):
    """List the 21-value transfers that have an active Earth-orbit id."""
    if len(vector) != SLOT_SIZE * SLOT_COUNT:
        raise ValueError("ESA Advanced vector must contain exactly 8400 values")
    return [vector[i:i + SLOT_SIZE] for i in range(0, len(vector), SLOT_SIZE)
            if vector[i] != -1]


def combine_transfers(baseline_vector, new_slot):
    """Append one conflict-free slot without modifying the original vector."""
    existing = active_slots(baseline_vector)
    if len(new_slot) != SLOT_SIZE or new_slot[0] == -1:
        raise ValueError("New ESA transfer slot is invalid")
    if len(existing) >= SLOT_COUNT:
        raise ValueError("Maximum of 400 transfers reached")
    for index, label in enumerate(("Earth orbit", "Moon orbit", "destination")):
        if any(int(slot[index]) == int(new_slot[index]) for slot in existing):
            raise ValueError(f"Duplicate {label} ID: {int(new_slot[index])}")
    result = list(baseline_vector)
    result[len(existing) * SLOT_SIZE:(len(existing) + 1) * SLOT_SIZE] = list(new_slot)
    return result


def elliptical_capture_velocity(r_si, moon_a, moon_e, moon_i, mu_moon):
    """Desired Moon-centered velocity tangent to an elliptic orbit at apoapsis.

    The arrival target is set at r=a(1+e). At that distance, a tangential
    velocity with vis-viva magnitude yields the target a and e. Orientation
    of the tangent is chosen to achieve the target inclination.
    """
    from src.advanced_fuel_sweep import inclined_circular_velocity

    r_si = np.asarray(r_si, dtype=float)
    radius = float(np.linalg.norm(r_si))
    if moon_a <= 0 or not (0 <= moon_e < 1) or radius <= 0:
        raise ValueError("Invalid lunar orbital elements or arrival radius")
    tangent = inclined_circular_velocity(r_si, mu_moon, moon_i)
    speed2 = float(mu_moon) * (2.0 / radius - 1.0 / float(moon_a))
    if speed2 <= 0:
        raise ValueError("Target Moon orbit is energetically incompatible")
    return tangent / np.linalg.norm(tangent) * math.sqrt(speed2)


def choose_destination(udp, moon_id, unavailable):
    options = [(float(rate), int(d)) for (moon, d), rate in udp.ltl_dict.items()
               if int(moon) == moon_id and int(d) not in unavailable and rate > 0]
    return max(options)[1] if options else None


def candidate_pairs(udp, occupied_earth, occupied_moon, limit):
    """Prioritize nearly coplanar orbits, including one grounded ESA pair.

    Screening is heuristic only: every resulting solution still needs the
    full official propagator and fitness validation.
    """
    from src.advanced_departures import L

    moon = []
    for i, (a, e, inc) in enumerate(udp.moon_data):
        a, e, inc = float(a), float(e), float(inc)
        if i in occupied_moon or not (0 <= e <= 0.12 and 0 <= inc <= 0.40):
            continue
        # Reject target orbits that dip into the Moon (approx. 1737.4km radius).
        if a * (1 - e) <= 1_767_400.0:
            continue
        moon.append((i, 4 * e + inc + abs(a / L - 0.0048)))
    moon.sort(key=lambda t: t[1])

    earth = []
    for i, (a, e, inc) in enumerate(udp.earth_data):
        a, e, inc = float(a), float(e), float(inc)
        if i in occupied_earth or not (0 <= e <= 0.20 and 0 <= inc <= 0.40):
            continue
        if a * (1 - e) <= 6_478_000.0:  # roughly Earth radius + 100km
            continue
        # Favor low inclination and eccentricity; larger a reduces injection.
        rank = 2 * inc + e - 0.08 * math.log(a / 6.545e6)
        earth.append((i, rank))
    earth.sort(key=lambda t: t[1])

    result = []
    # ESA's published data has E12 and L3 as a low-inclination pair;
    # only include when they pass the same screening as all other pairs.
    if any(i == 12 for i, _ in earth) and any(i == 3 for i, _ in moon):
        result.append((12, 3))
    # Interleave Moon IDs, not just Earth IDs, to encourage independent routes.
    for k in range(max(len(earth[:10]), len(moon[:8]))):
        if not earth or not moon:
            break
        e = earth[k % min(len(earth), 10)][0]
        m = moon[k % min(len(moon), 8)][0]
        if (e, m) not in result:
            result.append((e, m))
        if len(result) >= limit:
            break
    for e, _ in earth[:8]:
        for m, _ in moon[:8]:
            if len(result) >= limit:
                return result[:limit]
            if (e, m) not in result:
                result.append((e, m))
    return result[:limit]


def initial_lambert_guess(pk, udp, earth_id, target_radius, raan_deg,
                          anomaly_deg, flight_days, side, L, T, V, moon_ratio):
    from src.advanced_phase_scan import earth_state_with_angles
    from src.advanced_lambert_scan import (
        initial_earth_inertial, lambert_departure_velocity,
    )
    from src.advanced_departures import MU_EARTH

    a, e, inc = map(float, udp.earth_data[earth_id])
    state = earth_state_with_angles(pk, a, e, inc,
                                    math.radians(raan_deg), math.radians(anomaly_deg))
    r0, v0 = initial_earth_inertial(state, L, V, moon_ratio)
    seconds = float(flight_days) * 86400.0
    angle = seconds / T
    radius = L + (-target_radius if side == "near" else target_radius)
    target = [radius * math.cos(angle), radius * math.sin(angle), 0.0]
    wanted = lambert_departure_velocity(pk, r0, target, seconds, MU_EARTH)
    return state, np.asarray(wanted) - np.asarray(v0), seconds / T


def save_report(rows, baseline_reported, best_score, best_file):
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({
        "description": "Pilot: second independent Earth-Moon-destination transfer",
        "baseline_fitness_from_v2_report": baseline_reported,
        "best_combined_esa_fitness": best_score,
        "improved_submission": best_file,
        "trials": rows,
    }, indent=2, allow_nan=False), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pairs", type=int, default=4,
                        help="Distinct Earth/Moon pairs to screen (default: 4)")
    args = parser.parse_args()
    if not 1 <= args.pairs <= 40:
        parser.error("--pairs must be between 1 and 40")
    if not BASELINE.exists():
        raise SystemExit("Missing results/submission_trajectory-matching_v2.json")

    baseline_payload = json.loads(BASELINE.read_text(encoding="utf-8"))
    baseline_vec = baseline_payload[0]["decisionVector"]
    occupied = active_slots(baseline_vec)
    if not occupied:
        raise SystemExit("Baseline submission has no active transfers")
    if len(occupied) != 1:
        raise SystemExit("This v3 pilot expects exactly one active v2 transfer")
    used_e = {int(slot[0]) for slot in occupied}
    used_m = {int(slot[1]) for slot in occupied}
    used_d = {int(slot[2]) for slot in occupied}

    import pykep as pk
    from src.advanced_departures import L, T, V, MU_MOON, MOON_RATIO
    from src.advanced_capture_refine import lunar_state_si
    from src.advanced_midcourse_refine import (
        target_position, refine_middle_impulse, build_three_burn_vector,
    )
    from src.advanced_probe import build_vector
    from src.advanced_phase_scan import MAX_POSITIVE_DV
    from src.esa_problem import load_udp
    from vsi.esa import write_submission

    udp = load_udp("trajectory-matching")
    physics = udp._validate_transfer.__globals__
    propagate, state2moon = physics["propagate"], physics["state2moon"]
    # Independently verify the single-transfer baseline once. If this is slow,
    # the user can let it run; do not silently skip official validation.
    print("Verifying saved v2 submission with official ESA evaluator...", flush=True)
    incumbent = float(udp.fitness(baseline_vec)[0])
    if not math.isfinite(incumbent) or incumbent >= 0:
        raise SystemExit(f"Baseline ESA validation failed: {incumbent}")
    print(f"Verified baseline fitness: {incumbent:.9f}", flush=True)

    rows, best, improved_file = [], incumbent, None
    pairs = candidate_pairs(udp, used_e, used_m, args.pairs)
    print(f"Testing {len(pairs)} new Earth/Moon pairs, {len(PHASES)} phases each", flush=True)
    print("All v2 files remain unchanged.", flush=True)
    save_report(rows, incumbent, best, improved_file)
    for pi, (earth_id, moon_id) in enumerate(pairs, 1):
        moon_a, moon_e, moon_i = map(float, udp.moon_data[moon_id])
        dest = choose_destination(udp, moon_id, used_d)
        if dest is None:
            continue
        # Target the Moon orbit's apoapsis so vis-viva capture matches a,e.
        target_radius = moon_a * (1.0 + moon_e)
        goal = target_position(1.0 - MOON_RATIO, target_radius / L, "near")
        print(f"\nPair {pi}/{len(pairs)}: Earth {earth_id} -> Moon {moon_id} -> Destination {dest}",
              flush=True)
        for raan, anomaly, days in PHASES:
            row = {"earth_id": earth_id, "moon_id": moon_id, "destination_id": dest,
                   "raan_deg": raan, "anomaly_deg": anomaly, "flight_days": days}
            try:
                state, dv_mps, flight_nd = initial_lambert_guess(
                    pk, udp, earth_id, target_radius, raan, anomaly, days,
                    "near", L, T, V, MOON_RATIO)
                first_cost = float(np.linalg.norm(dv_mps))
                row["first_burn_mps"] = first_cost
                if not math.isfinite(first_cost) or first_cost >= FIRST_BURN_CAP_MPS:
                    row["status"] = "screened_first_burn"
                    rows.append(row)
                    save_report(rows, incumbent, best, improved_file)
                    continue
                t1 = flight_nd * MIDCOURSE_FRACTION
                t2 = flight_nd - t1
                first_nd = (dv_mps / V).tolist()
                fit = refine_middle_impulse(
                    propagate, state, first_nd, t1, t2, goal, L,
                    max_iterations=10,
                )
                row.update(status=fit["status"], propagations=fit["calls"])
                if fit["status"] != "evaluated":
                    rows.append(row)
                    save_report(rows, incumbent, best, improved_file)
                    continue
                arrival_error = float(fit["position_error_km"])
                row["arrival_error_km"] = arrival_error
                # Target eccentric-orbit tolerance is 1e-6, so a poor arrival
                # cannot become a valid match just by selecting a final burn.
                if arrival_error >= 0.5:
                    row["status"] = "arrival_not_refined"
                    rows.append(row)
                    save_report(rows, incumbent, best, improved_file)
                    continue
                mid = np.asarray(fit["middle_mps"], dtype=float)
                before = fit["final_state_before_capture"]
                r_si, v_si = lunar_state_si(before)
                desired = elliptical_capture_velocity(r_si, moon_a, moon_e,
                                                       moon_i, MU_MOON)
                final_nd = ((desired - v_si) / V).tolist()
                total_dv = (first_cost + float(np.linalg.norm(mid))
                            + float(np.linalg.norm(desired - v_si)))
                row["total_delta_v_mps"] = total_dv
                if total_dv >= MAX_POSITIVE_DV:
                    row["status"] = "nonpositive_payload"
                    rows.append(row)
                    save_report(rows, incumbent, best, improved_file)
                    continue
                new_vec = build_three_burn_vector(
                    build_vector, earth_id, moon_id, dest, state, first_nd,
                    (mid / V).tolist(), final_nd, t1, t2,
                )
                end = propagate(state, 0.0,
                                [first_nd, (mid / V).tolist(), final_nd], [t1, t2])
                if not end:
                    row["status"] = "invalid_after_capture"
                    rows.append(row)
                    save_report(rows, incumbent, best, improved_file)
                    continue
                elements = state2moon(end)
                errs = [abs(float(elements[0]) - moon_a) / L,
                        abs(float(elements[1]) - moon_e),
                        abs(float(elements[2]) - moon_i)]
                row["orbit_errors"] = errs
                if not all(math.isfinite(err) and err < TOL for err in errs):
                    row["status"] = "orbit_mismatch"
                    rows.append(row)
                    save_report(rows, incumbent, best, improved_file)
                    continue
                single_score = float(udp.fitness(new_vec)[0])
                row["single_esa_fitness"] = single_score
                if single_score >= 0:
                    row["status"] = "esa_rejected_single"
                    rows.append(row)
                    save_report(rows, incumbent, best, improved_file)
                    continue
                combined = combine_transfers(baseline_vec, new_vec[:SLOT_SIZE])
                print(f"  Candidate valid: {single_score:.6f}. Checking combined ESA fitness...",
                      flush=True)
                combined_score = float(udp.fitness(combined)[0])
                row["combined_esa_fitness"] = combined_score
                row["status"] = "combined_valid" if combined_score < 0 else "combined_rejected"
                if combined_score < best - 1e-8:
                    # Confirm once more before persisting a new submission.
                    reconfirmed = float(udp.fitness(combined)[0])
                    if reconfirmed < best - 1e-8:
                        best = reconfirmed
                        write_submission("spoc-4-luna-tomato-logistics",
                                         "trajectory-matching", combined, str(OUTPUT))
                        improved_file = str(OUTPUT.relative_to(ROOT))
                        print(f"  NEW TWO-TRANSFER RECORD: {best:.9f}", flush=True)
                rows.append(row)
            except (ValueError, RuntimeError, OverflowError, FloatingPointError) as exc:
                row.update(status="exception", message=str(exc))
                rows.append(row)
                print(f"  Skipped: {exc}", flush=True)
            save_report(rows, incumbent, best, improved_file)

    print(f"\nBaseline official ESA fitness: {incumbent:.9f}", flush=True)
    print(f"Best combined ESA fitness: {best:.9f}", flush=True)
    if improved_file:
        print(f"Two-transfer submission: {improved_file}", flush=True)
    else:
        print("No verified second transfer found. Original v2 submission is safe.", flush=True)
    print(f"Diagnostic report: {REPORT.relative_to(ROOT)}", flush=True)


if __name__ == "__main__":
    main()
