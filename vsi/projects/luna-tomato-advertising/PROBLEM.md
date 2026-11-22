# Problem: ESA SpOC 4 — Luna Tomato Advertising

Source: https://optimise.esa.int/challenge/spoc-4-luna-tomato-advertising/About
Official repo / discussions: https://github.com/esa/SpOC4 (UDP class `celestial_morse_code`)
Single-objective with a feasibility threshold · mixed integer + continuous.

## Story in one line
Spacecraft passing in front of the Moon dim its light; schedule a fleet so the dimming spells the Morse code of
"Tomatoes for sale" — with as few spacecraft as possible.

## Problem
Problem id: `tie-breaker` (dimension 4 674).

Orbit databases (CR3BP, Earth–Moon): 188 DRO, 291 Lyapunov, 300 Axial → `N = 779` orbit slots,
at most `max_per_orbit = 5` spacecraft per orbit. Each database row:
`[x, y, z, vx, vy, vz, period_rad, occultation_frequency, occultation_amplitude]`;
`period_days = period_rad / (2π) · 27.8511`.

Morse timing (units of one occultation width 0.1036 days): dot 2, dash 5, intra-character gap 2,
letter gap 5, word gap 7. Target: `t, target = udp.morse_to_signal(" Tomatoes for sale ")`, time grid of 2 710 samples.

## Decision vector (length N + 5N = 4 674)
- `sel = x[:N]` — integers in `[0, 5]`: number of spacecraft in orbit slot i (order: DRO, Lyapunov, Axial).
- `phs = x[N:]` — for slot i, phases `phs[5i : 5i+5]`, the first `sel[i]` are used, each in `[0, 2π)`.

## Objective
`obj, num_selected, mse = udp.fitness(x, postprocess=True)`; ranking:
1. Feasible (`mse ≤ 0.05`) beats infeasible.
2. Among feasible: fewer spacecraft is better.
3. Among infeasible: lower MSE-based penalty is better.

## Submission format
JSON file (one decision vector), uploaded at https://optimise.esa.int/submit:
```json
[
  {
    "decisionVector": [ x ],
    "problem": "tie-breaker",
    "challenge": "spoc-4-luna-tomato-advertising"
  }
]
```
Python: `from submission_helper import create_submission` (https://api.optimize.esa.int/data/tools/submission_helper.py), or `vsi.esa.write_submission`.

**Check the challenge id:** the page's own helper example uses `"spoc-4-luna-tomato-advertisment"` while the page
URL is `spoc-4-luna-tomato-advertising`. Confirm which one the platform accepts before the final submission.

## Dependencies (official)
`numpy`, `heyoka`, `matplotlib`.

## Hints from the page
Start feasible (many spacecraft), then remove spacecraft; with `sel` fixed, optimise phases to lower the MSE;
validate often with `udp.plot_signal(x)` / `udp.plot_orbits(x)`; keep `mse < 0.05` during edits.

## Why it is hard
Choosing which orbits to use is a set-cover-like combinatorial problem (minimise assets covering all pulses of the
signal), coupled with continuous phase tuning. Natural approaches: greedy cover of the Morse pulses,
then pruning + local search on phases.
