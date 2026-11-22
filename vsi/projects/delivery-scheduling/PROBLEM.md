# Problem: ESA SpOC — Delivery Scheduling

Source: https://optimise.esa.int/challenge/spoc-delivery-scheduling/About (evaluation code / UDP linked from the problem page)
Single-objective · **purely combinatorial** (no astrodynamics needed) · GECCO 2022.

## Story in one line
Assign 340 asteroids to 12 processing stations (choosing one transfer opportunity each) and give every station
one non-overlapping activity window, so that the poorest station/material gets as much mass as possible.

## Problem
Problem id: `delivery-scheduling`. Data: `https://api.optimize.esa.int/data/spoc/scheduling/candidates.txt`
(local path `./data/spoc/scheduling/candidates.txt`), a dictionary
`{asteroid_id: {station_id: [[T_arr, mA, mB, mC], …]}}`.
Asteroids `1..340`, stations `1..12`, opportunity ids `1..8` (1-based, order in the list). Horizon 80 days.

## Decision vector (1 044 values)
`[T1i, T1f, …, T12i, T12f]` (24 window epochs in `[0, 80]`, by station id) followed by 340 triples
`[asteroid_id, station_id, opportunity_id]`; `station_id = 0` = not delivered.
`convert_to_chromosome()` fills in missing asteroids as unassigned.

## Constraints
- `0 ≤ Tki ≤ Tkf ≤ 80`; windows do not overlap; at least **1 day** between consecutive windows.
- Each asteroid assigned once, and `(asteroid, station, opportunity)` must exist in the database.
- Every delivered asteroid's arrival time lies inside its station's window.

## Objective (maximise)
`M_min = min over stations i, min over materials j ∈ {A, B, C} of M_(j,i)`.
`M_min, eq1, eq2, ineq1, ineq2 = udp.fitness(x)` (equalities satisfied at 0, inequalities at ≤ 0).

## Submission format
JSON file (one decision vector), uploaded at https://optimise.esa.int/submit:
```json
[
  {
    "decisionVector": [ x ],
    "problem": "delivery-scheduling",
    "challenge": "spoc-delivery-scheduling"
  }
]
```
Python: `from submission_helper import create_submission` (https://api.optimize.esa.int/data/tools/submission_helper.py), or `vsi.esa.write_submission`.

## Hint from the page
Given a valid assignment, the windows can always be set from the first to the last arrival at each station.

## Why it is hard
Max-min assignment with a scheduling (window ordering) layer — a generalised assignment / bin-balancing problem,
NP-hard. Typical approach: choose a station order and window boundaries, greedily assign asteroids to the currently
poorest station/material, then improve with swaps / moves (local search, simulated annealing, tabu) or an ILP on a
reduced model.
