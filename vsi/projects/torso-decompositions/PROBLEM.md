# Problem: ESA SpOC 3 — Torso Decompositions

Source: https://optimise.esa.int/challenge/spoc-3-torso-decompositions/About
Official code (scorer, submission helper): https://github.com/esa/SpOC3
Discussions: https://github.com/esa/SpOC3/discussions

## Input
A connected, undirected, simple graph `G` given as an edge list (one `u v` per line).
Vertices are `0 … n-1`. Three instances:

| Problem id     | File        | URL |
|----------------|-------------|-----|
| `small-graph`  | `easy.gr`   | https://api.optimize.esa.int/data/spoc3/torso/easy.gr |
| `medium-graph` | `medium.gr` | https://api.optimize.esa.int/data/spoc3/torso/medium.gr |
| `large-graph`  | `hard.gr`   | https://api.optimize.esa.int/data/spoc3/torso/hard.gr |

## Decision vector
`x = [p1, p2, …, pn, t]` — a permutation of all `n` vertices followed by a threshold `t ∈ {0, …, n-1}`.

## Semantics
1. **Orientation:** edge `{u, v}` is oriented `u → v` iff `u` comes before `v` in the permutation.
2. **Fill-in:** scan the permutation left to right. When at vertex `u`, for every two out-neighbours
   `v, w` of `u` that are not adjacent, add edge `{v, w}` (oriented by the permutation).
   (This is the classic *elimination game*; the result is a chordal completion of `G`.)
3. **Torso:** the last `n - t` vertices of the permutation. **Size** = `n - t`.
4. **Width:** the maximum out-degree (counting fill edges) of any vertex in the torso.

Worked example (from the official page) — edges `0-1 0-2 1-6 2-8 3-8 3-9 4-5 4-6 4-7`,
`x = [0,1,2,4,5,3,6,8,9,7, 6]` → torso `[6,8,9,7]`, size 4, width 2 — use it as the first test of your evaluator.

## Objectives (bi-objective)
- **Maximise torso size** ⇔ minimise `t`.
- **Minimise torso width.**

Submit up to **20** decision vectors approximating the Pareto front. Quality is measured with the
**hypervolume indicator**. The width of the whole permutation is guaranteed/required to be ≤ 500;
worse solutions are scored as width 501.

## Submission format
```json
[
  {
    "decisionVector": [ x1, x2, ..., x20 ],
    "problem": "small-graph",
    "challenge": "spoc-3-torso-decompositions"
  }
]
```
`vsi.esa.write_submission` writes this file. For final scoring, verify with the official UDP from `esa/SpOC3`.

## Why it is hard
Choosing the ordering is equivalent to choosing an elimination ordering; minimising the width of an
elimination ordering is the treewidth problem, which is NP-hard. Hence heuristics / metaheuristics.
