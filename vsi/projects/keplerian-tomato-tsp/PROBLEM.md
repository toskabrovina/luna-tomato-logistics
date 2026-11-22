# Problem: ESA SpOC 4 — Keplerian Tomato Traveling Salesperson

Source: https://optimise.esa.int/challenge/spoc-4-keplerian-tomato-traveling-salesperson/About
Official repo (utilities incl. Lambert solver `TomatoProblem`): https://github.com/esa/SpOC4
Single-objective · time-dependent TSP · GECCO 2026.

## Story in one line
Collect all tomatoes orbiting the Moon as fast as possible; every hop between two tomatoes is a Lambert transfer
whose ΔV must stay under a limit (a few exceptions allowed).

## Problems
| Problem id | Instance file |
|---|---|
| `small` | https://api.optimize.esa.int/data/spoc4/kttsp/problems/easy.kttsp |
| `medium` | https://api.optimize.esa.int/data/spoc4/kttsp/problems/medium.kttsp |
| `large` | https://api.optimize.esa.int/data/spoc4/kttsp/problems/hard.kttsp |

## Input file
- Lines starting with `c` are comments.
- Parameter line: `p kttsp t0 Δt_min t_max ΔV_max ΔV_max_exception E`
  (start time [d], minimum time of flight [d], maximum total time [d], max ΔV per transfer [m/s],
  max ΔV for special moves [m/s], number of special moves). Example: `p kttsp 0.0 0.001 150.0 100.0 600.0 5`.
- Then one orbit per tomato (index from 0): `a [m]  e  i [rad]  Ω [rad]  ω [rad]  ν (mean anomaly) [rad]`.

## Decision vector (length 3N - 2)
`x = [t1, …, t(N-1), tof1, …, tof(N-1), π1, …, πN]`
- `t_i` departure time of transfer i, `tof_i` its time of flight (days), `π` a permutation of `0 … N-1`.
- Transfer i goes from `π_i` to `π_(i+1)`; must hold `t_i + tof_i ≤ t_(i+1)` (waiting is allowed).
- `compute_transfer(π_i, π_(i+1), t_i, tof_i) ≤ ΔV_max`, except at most `E` transfers with `≤ ΔV_max_exception`.

## Objective (minimise)
Mission completion time `f = t_(N-1) + tof_(N-1)`.

## Submission format
JSON file (one decision vector), uploaded at https://optimise.esa.int/submit:
```json
[
  {
    "decisionVector": [ x ],
    "problem": "small",
    "challenge": "spoc-4-keplerian-tomato-traveling-salesperson"
  }
]
```
Python: `from submission_helper import create_submission` (https://api.optimize.esa.int/data/tools/submission_helper.py), or `vsi.esa.write_submission`.

Problem ids: `small`, `medium`, `large`.

## Utilities
`util = TomatoProblem("instance.kttsp")` · `util.compute_transfer(i_from, i_to, t_start, tof)` →ΔV ·
`util.plot_full_trajectory(x)`. Dependencies: `numpy`, `matplotlib`, `pykep` **2.x** (not 3.x).

## Why it is hard
A TSP (NP-hard) where edge costs depend on departure time and time of flight, and many edges are infeasible.
Typical approach: precompute a feasibility graph on a time grid, then a time-dependent nearest-neighbour /
beam search, improved with 2-opt / or-opt and timing re-optimisation.
