# Problem: ESA SpOC 3 — Interferometric Mission

Source: https://optimise.esa.int/challenge/spoc-3-interferometric-mission/About
Official code (UDP, tutorial notebook): https://github.com/esa/SpOC3/tree/main/Challenge%202%20Interferometric%20Mission
Single-objective · continuous · GECCO 2024.

## Story in one line
Place satellites around a "mothership" so that, seen from three directions and at three moments,
they form as many **distinct baselines** (pairwise displacements) as possible — a Golomb-ruler-like pattern.

## Problems
| Problem id | Mothership orbit | Satellites N | Grid | Dimension |
|---|---|---|---|---|
| `tiny-observatory-in-dro` | Distant Retrograde Orbit | 5 | 11×11 | 30 |
| `large-observatory-in-dro` | Distant Retrograde Orbit | 40 | 21×21 | 240 |
| `large-observatory-in-halo` | Halo orbit | 40 | 21×21 | 240 |

## Decision vector
Relative initial position and velocity of each satellite w.r.t. the mothership (normalised units):
`x = [dx1..dxN, dy1..dyN, dz1..dzN, dvx1..dvxN, dvy1..dvyN, dvz1..dvzN]` (length 6N).

## Evaluation
- The satellites are propagated (Earth–Moon three-body dynamics) and measured at t = 0, 1 and 2 mothership periods.
- At each time the positions are projected on the XY, XZ and YZ planes and snapped to a square grid centred on the
  mothership. Positions -1 / +1 are the grid edges; satellites outside the grid are ignored.
- After each period the grid grows by the factor 1.23.
- Two satellites in the same grid square count as one.
- For each plane, the **fill factor** grows with the number of unique baselines.

## Objective (minimise)
`f = - max over i in {1,2,3} of ( f_i,XY + f_i,XZ + f_i,YZ )`

## Submission format
JSON file (one decision vector), uploaded at https://optimise.esa.int/submit:
```json
[
  {
    "decisionVector": [ x ],
    "problem": "tiny-observatory-in-dro",
    "challenge": "spoc-3-interferometric-mission"
  }
]
```
Python: `from submission_helper import create_submission` (https://api.optimize.esa.int/data/tools/submission_helper.py), or `vsi.esa.write_submission`.

Problem ids: `tiny-observatory-in-dro`, `large-observatory-in-dro`, `large-observatory-in-halo`.

## Dependencies (official)
`heyoka == 3.2.0` (mandatory — 4.x fails to load the UDP), `pygmo`, `numpy`, `scipy`, `PIL`, `matplotlib`.

## Why it is hard
Maximising distinct pairwise distances is a Golomb-ruler-type combinatorial problem (hard even in 1D), here coupled
with orbital dynamics that move the pattern over time. Each evaluation needs numerical propagation, so evaluations
are expensive: use a fast surrogate (e.g. count baselines at t = 0 only) before the official fitness.
