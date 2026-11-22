# Problem: ESA SpOC 2 — Quantum Communications Constellations

Source: https://optimise.esa.int/challenge/spoc-2-quantum-communications-constellations/About
Official repo / discussions: https://github.com/esa/SpOC2 ·
UDP: https://api.optimize.esa.int/media/problems/spoc-2-quantum-communications-constellations-quantum-communications-constellatio_DhZfx09.py
**Bi-objective** · mixed integer + continuous · GECCO 2023.

## Story in one line
Design two Walker constellations and choose 4 rover sites so that quantum links from 7 motherships to the rovers
are cheap, while keeping the number and quality of satellites (cost) low.

## Problem
Problem id: `quantum-communications-constellations`.
Data: 100 candidate rover positions (lat, lon in rad) `https://api.optimize.esa.int/data/spoc2/constellations/rovers.txt`
(local path expected `./data/spoc2/constellations/rovers.txt`).

## Decision vector (20 values)
`x = [a1, e1, i1, w1, eta1] + [a2, e2, i2, w2, eta2] + [S1, P1, F1] + [S2, P2, F2] + [r1, r2, r3, r4]`
- Constellation 1: `a1 ∈ [1.06, 1.8]` (normalised), `e1 ∈ [0, 0.02]`, `i1 ∈ [0, π]`, `w1 ∈ [0, 2π]`, `eta1 ∈ [1, 1000]`.
- Constellation 2: `a2 ∈ [2, 3.5]`, `e2 ∈ [0, 0.1]`, `i2 ∈ [0, π]`, `w2 ∈ [0, 2π]`, `eta2 ∈ [1, 1000]`.
- Walker parameters (integers): satellites per plane `S ∈ [4, 10]`, planes `P ∈ [2, 10]`, phasing `F ∈ [0, 9]`.
- Rovers: 4 line indices `r ∈ [0, 99]` in `rovers.txt`.

## Constraints (satisfied when ≤ 0)
- Any two selected rovers at least 3 000 km apart.
- Two satellites can be part of a path only if at least 50 km apart.

## Objectives (both minimised, normalised)
- `J1` = average over mothership–rover pairs and 10 years of the cheapest path cost
  `QC = Σ ( -log(η_(i+1)) + 2·log(L_i) ) + 1 / sin(π/2 - θ_Z)`, with line of sight on every link and zenith angle
  `θ_Z ≤ π/3` on the last link.
- `J2 = η1·S1·P1 + η2·S2·P2` (cost of the constellations).

`J1, J2, c1, c2 = udp.fitness(x)`.
Score: **hypervolume** of the submitted set with reference point `[1.2, 1.4]`, × 10 000. Up to **100** vectors.

## Submission format
JSON file (a list of decision vectors), uploaded at https://optimise.esa.int/submit:
```json
[
  {
    "decisionVector": [ x1, x2, ... ],
    "problem": "quantum-communications-constellations",
    "challenge": "spoc-2-quantum-communications-constellations"
  }
]
```
Python: `from submission_helper import create_submission` (https://api.optimize.esa.int/data/tools/submission_helper.py), or `vsi.esa.write_submission`.

## Why it is hard
Mixed integer/continuous, two conflicting objectives, constraints, and an expensive simulation
(shortest paths in a time-varying graph over 10 years). Typical approach: multi-objective EA (NSGA-II / MOEA/D)
or a sweep over the integer Walker parameters with continuous local optimisation, plus Pareto filtering.
