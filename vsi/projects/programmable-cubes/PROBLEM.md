# Problem: ESA SpOC 3 — Programmable Cubes

Source: https://optimise.esa.int/challenge/spoc-3-programmable-cubes/About
Official code + data + 4 tutorial notebooks: https://github.com/esa/SpOC3/tree/main/Challenge%203%20Programmable%20Cubes
Single-objective (with a secondary length term) · combinatorial / planning · GECCO 2024.

## Story in one line
An ensemble of cubes must reshape itself, one pivoting move at a time, into a target spacecraft,
using as few moves as possible.

## Problems
| Problem id | Target | Cubes | Cube types | Max commands |
|---|---|---|---|---|
| `iss` | International Space Station | 148 | 3 | 6 000 |
| `jwst` | James Webb Space Telescope | 643 | 6 | 30 000 |
| `enterprise` | USS Enterprise | 1 472 | 10 | 100 000 |

Data (initial + target positions and types): `https://api.optimize.esa.int/data/spoc3/cubes/data/ISS`, `.../JWST/`, `.../Enterprise/`,
problem configs `https://api.optimize.esa.int/data/spoc3/cubes/problems/`, move logic `https://api.optimize.esa.int/data/spoc3/cubes/CubeMoveset.py`.
Cubes of the same type are interchangeable.

## Moves
A command picks a cube and rotates it around an edge (pivot around one cube or traverse to a neighbour — chosen automatically):
`0/1` = counter-clockwise / clockwise around z · `2/3` = around x · `4/5` = around y.
A move is legal only if (1) removing the cube keeps the ensemble connected and (2) the cube does not collide and
reconnects at its new place.

## Decision vector
`x = [c0, m0, c1, m1, …, cN, mN, -1]` — cube index then command. Evaluation stops at the first `-1`;
the chromosome must end with `-1`.

## Objective (minimise)
- `C(x)` = cubes on a correct target position (right type), `C_max` = number of cubes
- `L(x)` = commands used, `L_max` = maximum commands
- `F(x) = (1 - α)·C(x)/C_max + α·(1 - L(x)/L_max)`, `α = 0.1`, `F0 = F` with no moves
- `f(x) = -(F(x) - F0) / (1 - F0)` → 0 = unchanged, -1 = theoretical best

## Submission format
JSON file (one decision vector), uploaded at https://optimise.esa.int/submit:
```json
[
  {
    "decisionVector": [ x ],
    "problem": "iss",
    "challenge": "spoc-3-programmable-cubes"
  }
]
```
Python: `from submission_helper import create_submission` (https://api.optimize.esa.int/data/tools/submission_helper.py), or `vsi.esa.write_submission`.

Problem ids: `iss`, `jwst`, `enterprise`.

## Useful UDP features
`udp = programmable_cubes_UDP('ISS')` · `udp.fitness(x)` · `udp.pretty(x)` prints illegal moves ·
`udp.plot('ensemble' | 'target', [types])` · `udp.fitness(x, initial_configuration=cfg)` evaluates from an
intermediate state (much faster for incremental search).

## Dependencies (official)
Python 3.8+, `numba >= 0.56.4`, `numpy >= 1.23.5`, `matplotlib >= 3.6.3`.

## Why it is hard
Modular-robot reconfiguration: the state space is all connected shapes of the ensemble, moves are constrained
(connectivity + collisions) and later moves depend on earlier ones. Shortest reconfiguration is a search/planning
problem far too large for exhaustive search: use heuristic search (greedy matching of cubes to targets, BFS/A* for
single-cube paths, local search on the move sequence).
