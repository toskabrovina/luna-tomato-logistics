# Problem: ESA SpOC — Mining the Belt

Source: https://optimise.esa.int/challenge/spoc-mining/About
UDP (evaluation code): https://api.optimize.esa.int/media/problems/spoc-mining-mine-the-belt-1647616672543.py
Single-objective · routing + scheduling (orienteering-like) · GECCO 2022.

## Story in one line
With one ship and a limited propellant tank, hop between asteroids of a belt in the TRAPPIST-1 system for 1 827 days,
preparing gold, platinum and nickel and refuelling on propellant asteroids, to maximise the scarcest material.

## Problem
Problem id: `mine-the-belt`. Data: `https://api.optimize.esa.int/data/spoc/mining/candidates.txt` (local `./data/spoc/mining/candidates.txt`),
10 000 asteroids, one per line:
`ID  a [m]  e  i [rad]  Ω [rad]  ω [rad]  true anomaly [rad]  mass [0..1]  material`
— material `0, 1, 2` = minable materials, `3` = propellant. `MU_TRAPPIST = G · 8.98266512e-2 · 1.989e30`.

## Rules
- Pick a start asteroid (does not count). Then repeatedly: next asteroid `a_i`, arrival time `t_i_arr ∈ [0, 1827]`,
  stay `t_i_m ∈ [1, 60]` days.
- Each day at an asteroid prepares / collects `1/30` mass (up to the asteroid's mass).
- Tank holds ΔV for 10 000 m/s; collecting 1.0 propellant mass refills it fully. Transfers are Lambert arcs (pykep).
- Running out of propellant ignores all later transfers. Only arrivals before day 1 827 count.

## Decision vector
`[t0_arr … tn_arr, t0_m … tn_m, a0 … an]`, made fixed-length (30 000) with `convert_to_chromosome`.

## Constraints
Each asteroid visited once (equality = 0); arrivals strictly increasing; `1 ≤ t_m ≤ 60` (inequalities ≤ 0).

## Objective (maximise; board shows `-J`)
`J = min(m0, m1, m2)` — the smallest prepared amount among the three materials.
The example chain on the official page (start 0, then 1446, 5131, 4449, 8091, 1516, 151, 4905, 8490) scores J = 0.58
(`udp.pretty(x)` prints the per-stop table).

## Submission format
JSON file (one decision vector), uploaded at https://optimise.esa.int/submit:
```json
[
  {
    "decisionVector": [ x ],
    "problem": "mine-the-belt",
    "challenge": "spoc-mining"
  }
]
```
Python: `from submission_helper import create_submission` (https://api.optimize.esa.int/data/tools/submission_helper.py), or `vsi.esa.write_submission`.

## Why it is hard
A time-dependent orienteering / prize-collecting TSP with a resource (propellant) constraint and a max-min objective,
over 10 000 nodes whose transfer costs change with time. Typical approach: precompute cheap transfer candidates
(nearby orbits), greedy / beam search choosing the next asteroid by material need and ΔV, then local search on the route.
