"""ESA Luna Tomato Logistics: numerical refinement of one lunar approach.

Place this file at src/advanced_capture_refine.py in the existing VSI project.
Run in the `luna-esa` Conda environment from project root:
    python -m src.advanced_capture_refine

This is an experimental *shooting* solver, not a claim of a valid transfer.
It uses the official ESA BCP propagator and checks the official fitness.
No entry is marked as a success unless the official fitness is negative.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from src.advanced_departures import (
    L, T, V, MU_EARTH, MU_MOON, MOON_RATIO,
)
from src.advanced_lambert_scan import (
    initial_earth_inertial, lambert_departure_velocity,
)
from src.advanced_phase_scan import (
    earth_state_with_angles, MAX_POSITIVE_DV,
)
from src.advanced_probe import best_destination, build_vector
from src.esa_problem import load_udp

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / 'results' / 'advanced_capture_refine.json'


def norm(v):
    return float(np.linalg.norm(np.asarray(v, dtype=float)))


def lunar_state_si(state):
    """Moon-centered inertial (at the rotating frame's instant), in SI units.

    The conversions mirror the project departure-state conversion and
    the official lunar orbital-elements check.
    """
    (x, y, z), (vx, vy, vz) = state
    r = np.array([(x - (1.0 - MOON_RATIO)) * L, y * L, z * L], dtype=float)
    v = np.array([(vx - y) * V, (vy + x - (1.0 - MOON_RATIO)) * V,
                  vz * V], dtype=float)
    return r, v


def circular_capture_burn(state):
    """Estimate the final prograde equatorial circularisation impulse.

    This is a useful target for the almost-equatorial, almost-circular
    Moon orbit 0, NOT a general solution for arbitrary lunar orbits.
    """
    r, v = lunar_state_si(state)
    radius = norm(r)
    if radius <= 0 or not math.isfinite(radius):
        raise ValueError('invalid lunar radius')
    # Prograde direction is tangent to the Moon-centered equatorial circle.
    horizontal = math.hypot(r[0], r[1])
    if horizontal <= 1:
        raise ValueError('cannot define equatorial tangent here')
    tangent = np.array([-r[1] / horizontal, r[0] / horizontal, 0.0])
    desired = math.sqrt(MU_MOON / radius) * tangent
    dv_si = desired - v
    return dv_si / V, norm(dv_si)


def initial_guess(pk, udp, data):
    """Rebuild a scanned candidate from the official Earth orbit."""
    earth_id, moon_id = 0, 0
    earth_a, earth_e, earth_i = map(float, udp.earth_data[earth_id])
    moon_a = float(udp.moon_data[moon_id][0])
    state = earth_state_with_angles(
        pk, earth_a, earth_e, earth_i,
        math.radians(float(data['raan_deg'])),
        math.radians(float(data['anomaly_deg'])),
    )
    r0, v0 = initial_earth_inertial(state, L, V, MOON_RATIO)
    days = float(data['flight_days'])
    tof = days * 86400
    angle = tof / T
    side = data['side']
    radius_from_earth = L + (-moon_a if side == 'near' else moon_a)
    target = [radius_from_earth * math.cos(angle),
              radius_from_earth * math.sin(angle), 0.0]
    dep_v = lambert_departure_velocity(pk, r0, target, tof, MU_EARTH)
    dv_mps = np.asarray(dep_v, dtype=float) - np.asarray(v0, dtype=float)
    return state, dv_mps, days, side, moon_a


def local_shooting(residual, x0, low, high, max_iterations=20):
    """Our own damped finite-difference Gauss-Newton shooting algorithm.

    Only numpy's linear algebra is used; no black-box optimisation solver.
    The Jacobian approximates how the arrival error changes with each
    launch-impulse component and the flight duration.
    """
    x = np.asarray(x0, dtype=float).copy()
    f = residual(x)
    cost = float(f @ f)
    lam = 0.1
    n_evaluations = 1
    accepted = 0
    steps = np.array([0.002, 0.002, 0.002, 0.004])
    for k in range(max_iterations):
        jac = np.zeros((len(f), len(x)), dtype=float)
        for j in range(len(x)):
            trial = x.copy()
            trial[j] = min(high[j], x[j] + steps[j])
            if trial[j] == x[j]:
                trial[j] = max(low[j], x[j] - steps[j])
            if trial[j] == x[j]:
                continue
            fj = residual(trial)
            n_evaluations += 1
            jac[:, j] = (fj - f) / (trial[j] - x[j])
        grad = jac.T @ f
        if float(np.linalg.norm(grad)) < 1e-9:
            break
        succeeded = False
        for _ in range(6):
            try:
                change = np.linalg.solve(jac.T @ jac + lam * np.eye(len(x)), -grad)
            except np.linalg.LinAlgError:
                lam *= 10.0
                continue
            # Don't jump too far on a highly non-linear Earth-Moon path.
            change = np.clip(change, [-0.4, -0.4, -0.4, -0.25],
                             [0.4, 0.4, 0.4, 0.25])
            trial = np.clip(x + change, low + 1e-8, high - 1e-8)
            ft = residual(trial)
            n_evaluations += 1
            new_cost = float(ft @ ft)
            if new_cost < cost:
                x, f, cost = trial, ft, new_cost
                lam = max(1e-6, lam / 2.5)
                succeeded = True
                accepted += 1
                break
            lam = min(1e10, lam * 5.0)
        print(f"  iteration {k+1:02d}: scaled error={math.sqrt(cost):.5g}; "
              f"accepted={succeeded}", flush=True)
        if not succeeded:
            break
    return {"x": x, "n_evaluations": n_evaluations,
            "message": f"Accepted {accepted} of at most {max_iterations} steps"}


def main():
    import pykep as pk

    scan = ROOT / 'results' / 'advanced_arrival_scan.json'
    if not scan.exists():
        raise SystemExit('Missing results/advanced_arrival_scan.json; run advanced_arrival_scan first.')
    report = json.loads(scan.read_text(encoding='utf-8'))
    if not report.get('top_candidates'):
        raise SystemExit('No successful earlier propagations to start from.')
    start = report['top_candidates'][0]

    udp = load_udp('trajectory-matching')
    propagate = udp._validate_transfer.__globals__['propagate']
    earth_id, moon_id = 0, 0
    dest_id, _ = best_destination(udp.ltl_dict, moon_id)
    state, first_dv_mps, start_days, side, target_a = initial_guess(pk, udp, start)

    # We target one fixed point on the near/far side of the Moon.
    # Choosing a point instead of just an arrival *radius* gives a smooth
    # three-coordinate aiming error for numerical shooting.
    moon_x = 1.0 - MOON_RATIO
    chosen_x = moon_x + (-target_a / L if side == 'near' else target_a / L)
    goal = np.array([chosen_x, 0.0, 0.0])

    # Optimise the three launch delta-v components and flight time.
    # Scaling makes all four parameters similar in magnitude for the solver.
    x0 = np.array([*first_dv_mps / 1000.0, start_days], dtype=float)
    max_abs_dv_component_kms = 8.0
    low = np.array([-max_abs_dv_component_kms] * 3 + [2.0])
    high = np.array([max_abs_dv_component_kms] * 3 + [9.0])
    x0 = np.clip(x0, low + 1e-8, high - 1e-8)

    best = {'error_km': float('inf'), 'x': x0.copy(), 'calls': 0}

    def propagate_candidate(x):
        dv = np.asarray(x[:3]) * 1000.0
        days = float(x[3])
        return propagate(
            state, 0.0,
            [(dv / V).tolist(), [0.0] * 3, [0.0] * 3],
            [days * 86400.0 / T, 0.0],
        )

    def residual(x):
        best['calls'] += 1
        try:
            final = propagate_candidate(x)
            if not final:
                # A collision is invalid. A fixed penalty prevents spurious success.
                return np.array([500.0, 500.0, 500.0, 0.0])
            error_km = (np.asarray(final[0], dtype=float) - goal) * L / 1000.0
            magnitude = norm(x[:3]) * 1000.0
            dist = norm(error_km)
            if dist < best['error_km']:
                best.update(error_km=dist, x=np.array(x, dtype=float).copy())
            # Smooth small regularisation: prefer lower first burn among
            # otherwise close shots. Never interpret this as valid delivery.
            return np.array([*(error_km / 1000.0), 0.005 * magnitude / 1000.0])
        except (ValueError, RuntimeError, OverflowError, FloatingPointError):
            return np.array([500.0, 500.0, 500.0, 0.0])

    print('Refining arrival using the OFFICIAL ESA propagator...', flush=True)
    print('Seed:', {k: start[k] for k in ('raan_deg','anomaly_deg','flight_days','side')})
    print('Initial first burn: {:,.1f} m/s'.format(norm(first_dv_mps)))
    print('Search goal: Moon orbit-0 radius {:,.2f} km, equatorial near/far point'.format(target_a / 1000))
    fit = local_shooting(residual, x0, low, high)

    # Evaluate both solver endpoint and the closest state we recorded.
    trials = [np.asarray(fit['x'], dtype=float), np.asarray(best['x'], dtype=float)]
    summaries = []
    for idx, x in enumerate(trials):
        try:
            final = propagate_candidate(x)
            if not final:
                continue
            r, v = lunar_state_si(final)
            distance_km = norm(r) / 1000
            first_burn = norm(x[:3]) * 1000.0
            final_impulse, capture_burn = circular_capture_burn(final)
            total_dv = first_burn + capture_burn
            vector = build_vector(
                earth_id, moon_id, dest_id, 0.0, state,
                (np.asarray(x[:3]) * 1000.0 / V).tolist(),
                float(x[3]) * 86400.0 / T,
            )
            # 21-value slot: final DV components occupy entries 16..18.
            vector[16:19] = [float(z) for z in final_impulse]
            score = float(udp.fitness(vector)[0])
            label = 'solver_endpoint' if idx == 0 else 'closest_encounter'
            summary = {
                'label': label,
                'flight_days': float(x[3]),
                'first_burn_mps': first_burn,
                'capture_burn_mps': capture_burn,
                'total_delta_v_mps': total_dv,
                'estimated_final_moon_radius_km': distance_km,
                'radius_gap_km': abs(distance_km - target_a / 1000),
                'official_ESA_fitness': score,
                'valid_delivery': score < 0,
            }
            summaries.append(summary)
            print(f"{label}: radius={distance_km:,.2f} km; "
                  f"first={first_burn:,.0f} m/s; capture={capture_burn:,.0f} m/s; "
                  f"ESA fitness={score}", flush=True)
            if score < 0:
                from vsi.esa import write_submission
                out = ROOT / 'results' / 'submission_trajectory-matching_refined.json'
                write_submission('spoc-4-luna-tomato-logistics',
                                 'trajectory-matching', vector, str(out))
                print('VALID delivery! Saved candidate to:', out, flush=True)
        except (ValueError, RuntimeError, OverflowError) as exc:
            print(f'Unable to inspect endpoint {idx}: {exc}', flush=True)

    OUTPUT.parent.mkdir(exist_ok=True, parents=True)
    OUTPUT.write_text(json.dumps({
        'status': 'experimental_numerical_shooting',
        'target_moon_a_km': target_a / 1000,
        'function_evaluations': int(fit['n_evaluations']),
        'propagator_calls': best['calls'],
        'optimizer_message': str(fit['message']),
        'best_position_error_km': best['error_km'],
        'results': summaries,
    }, indent=2), encoding='utf-8')
    print('Saved:', OUTPUT.relative_to(ROOT), flush=True)
    if not any(row['valid_delivery'] for row in summaries):
        print('No valid ESA delivery yet. This is a targeting experiment, not a leaderboard score.')
    if any(row['total_delta_v_mps'] >= MAX_POSITIVE_DV for row in summaries):
        print('Warning: total delta-v is at or above the positive-payload limit.')


if __name__ == '__main__':
    main()
