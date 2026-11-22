# Problem: ESA SpOC 4 — Luna Tomato Logistics

Source: https://optimise.esa.int/challenge/spoc-4-luna-tomato-logistics/About
Official repo / discussions: https://github.com/esa/SpOC4
Single-objective · combinatorial (Beginner) + trajectory design (Advanced).

## Story in one line
Pick transfers Earth orbit → Moon orbit → Moon destination so that as many tomatoes as possible arrive,
with every orbit and destination used at most once.

## Problems
| Problem id | Level | Dimension | Data |
|---|---|---|---|
| `matching-i` | Beginner | 25 000 | `https://api.optimize.esa.int/data/spoc4/ltl/random_harder_5000.txt` (25 000 transfers) |
| `matching-ii` | Beginner | 92 103 | `https://api.optimize.esa.int/data/spoc4/ltl/random_hard_10000.txt` (92 103 transfers) |
| `trajectory-matching` | Advanced | 8 400 | `https://api.optimize.esa.int/data/spoc4/ltl/Earth_orbits.txt`, `Moon_orbits.txt`, `LTL.txt` |

## Beginner problems: weighted 3-dimensional matching
- Sets `E` (Earth orbits), `L` (Moon orbits), `D` (destinations), numbered `1, 2, …`.
- Input file: one transfer per line `e l d weight`, e.g. `1 1 1 6.202`.
- A solution is a set of transfers where no `e`, no `l` and no `d` is used twice.
- **Decision vector:** binary array of length |T|, `x[i] = 1` if transfer i is selected.
- **Fitness:** sum of the weights of the selected transfers (maximise; the board shows it negated).
  **Invalid solutions score 0.**
- Example (10 transfers): `[1,0,1,0,0,0,0,0,0,0]` → 8.843 valid; `[1,1,0,…]` invalid (destination 1 twice).

## Advanced problem: trajectory matching
- Transfer Earth orbit → Moon orbit is a rendezvous with at most 3 impulses in the bi-circular problem
  (Earth, Moon, Sun; Simó et al. 1995). Orbits are given by Keplerian `(a, e, i)` only.
- Delivered mass: `m_l = m_w · exp(-ΔV_tot / (Isp·g0)) - m_dry`, `m_w = 5000 kg`, `m_dry = 500 kg`, `Isp = 311 s`, `g0 = 9.80665`.
- Discount for time: `m_d = min(m_l, (200 - ΔT) · c_ld)`, `c_ld` = LTL rate (kg/day) from Moon orbit l to destination d,
  `ΔT` = transfer duration in days. Horizon 200 days.
- **Decision vector:** up to 400 transfers × 21 values = 8 400:
  `e_id, l_id, d_id, t0, x0, y0, z0, vx0, vy0, vz0, DVx0, DVy0, DVz0, DVx1, DVy1, DVz1, DVx2, DVy2, DVz2, T1, T2`.
  Unused slots: `e_id = -1`. Two-impulse transfer: set the middle impulse to 0.
- Orbit match tolerance `1e-6` on `a, e, i` (non-dimensional).

## Submission format
JSON file (one decision vector), uploaded at https://optimise.esa.int/submit:
```json
[
  {
    "decisionVector": [ x ],
    "problem": "matching-i",
    "challenge": "spoc-4-luna-tomato-logistics"
  }
]
```
Python: `from submission_helper import create_submission` (https://api.optimize.esa.int/data/tools/submission_helper.py), or `vsi.esa.write_submission`.

Problem ids: `matching-i`, `matching-ii`, `trajectory-matching`.

## Why it is hard
Maximum-weight 3-dimensional matching is **NP-hard** (one of Karp's problems; 2D matching is polynomial).
Classic course material: greedy by weight, local search with swaps, LP relaxation / Lagrangian bounds,
reduction to 2D matching as a heuristic. The Advanced problem adds expensive trajectory optimisation.
