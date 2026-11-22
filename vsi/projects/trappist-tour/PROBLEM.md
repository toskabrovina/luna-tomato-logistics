# Problem: ESA SpOC — Trappist Tour

Source: https://optimise.esa.int/challenge/spoc-trappist-tour/About (evaluation code / UDP linked from the problem page)
**Bi-objective** · mixed integer + continuous · GECCO 2022.

## Story in one line
Fly a spacecraft from 10 AU into the TRAPPIST-1 system and visit all 7 planets once, trading total ΔV against
total mission time.

## Problem
Problem id: `trappist-tour`. No data file: the planets are inside the UDP.

## Decision vector (34 values)
- Entry leg `[u, v, T0]` — entry angles and duration of the first leg.
- 6 planet-to-planet legs `[beta, rp/rP, eta, T]` — flyby geometry, fraction of the leg before the deep-space
  manoeuvre, leg duration (in the order of the sequence).
- Planet sequence `[s0 … s6]`, integers `0..6` = planets b, c, d, e, f, g, h — must be a permutation.
- Bounds: `lb, ub = udp.get_bounds()`. Example: `udp.example()`. Encoding based on pykep `mga_1dsm`.

## Constraints
- Sequence is a permutation (equality constraint = 0).
- Closest approach to the star ≥ 834 840 km (inequality ≤ 0).

## Objectives (both minimised)
- Total impulsive ΔV [m/s]; total mission time [days].
- `DV, T, eq_constraint, ineq_constraint = udp.fitness(x)`.

Score: **hypervolume** with reference point `[2500, 4000]` — only solutions with ΔV < 2500 m/s and T < 4000 days count.
Up to **100** vectors. Score 0 = no submitted vector inside the reference box.

## Submission format
JSON file (a list of decision vectors), uploaded at https://optimise.esa.int/submit:
```json
[
  {
    "decisionVector": [ x1, x2, ... ],
    "problem": "trappist-tour",
    "challenge": "spoc-trappist-tour"
  }
]
```
Python: `from submission_helper import create_submission` (https://api.optimize.esa.int/data/tools/submission_helper.py), or `vsi.esa.write_submission`.

## Why it is hard
The planet order is a permutation problem (7! = 5 040 orders) and, for each order, the trajectory is a nonlinear
continuous optimisation with many local optima. Typical approach: enumerate / prune orders, optimise the continuous
legs per order (DE / CMA-ES / multi-start local search), then build the Pareto front.
