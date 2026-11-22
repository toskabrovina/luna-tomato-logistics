# Problem: ESA SpOC 2 — Morphing Rovers

Source: https://optimise.esa.int/challenge/spoc-2-morphing-rovers/About
Official repo / discussions: https://github.com/esa/SpOC2
Single-objective · continuous, very high-dimensional (neuro-evolution) · GECCO 2023.

## Story in one line
Design one rover with 4 shape "modes" plus the neural network that steers it, so that copies of it reach
30 samples on 6 Mars-like maps as fast as possible.

## Problem
Problem id: `morphing-rovers`. 6 maps × 5 scenarios = 30 scenarios, 500 time steps each.
Data: height maps `https://api.optimize.esa.int/data/spoc2/morphing/Maps/` (`MapX.JPG`), scenarios `https://api.optimize.esa.int/data/spoc2/morphing/coordinates.txt`
(rows `[map, Lx, Ly, Ax, Ay]` = landing site and sample). Default local path `./data/spoc2/morphing`.

## Simulation
- Each mode `i ∈ 0..3` is an 11×11 mask `F(i)`; speed factor `ν = V(F(i), T) ∈ [0,1]` compares it with the 11×11
  terrain under the rover. Position update `r(t+1) = r(t) + ν · v_max · (cos α, sin α)`.
- A neural network (2 conv layers on an 89×89 terrain view + dense layers on the rover state + recurrent layer)
  outputs a mode-switch signal and an angular velocity `ω ∈ [-π/4, π/4]`.
- Stops when the sample is reached (distance ≤ 6), jumps to the end if the rover leaves the map.

## Decision vector (19 133 values)
1. 484 mask values (4 × 11 × 11), in `[-100, 100]`, mask centres in `[1e-16, 100]`.
2. 146 biases + 18 496 weights of the network, in `[-100, 100]` (layer order given on the official page / UDP).
3. 7 integer hyper-parameters `[p1, p2, a1, a2, a3, a4, a5]`: pooling type (0 max, 1 avg) after each conv layer and
   activation functions (0 Sigmoid, 1 Hard Sigmoid, 2 Tanh, 3 Hard Tanh, 4 Softsign, 5 Softplus, 6 ReLU; a5 only 0–4).

## Objective (minimise)
Per scenario `f = (T / T_min) · (1 + d / d0)` — `T` time used, `T_min` straight-line time at max speed,
`d0` start distance, `d` final distance (0 if reached). Score = mean over all scenarios.

## Submission format
JSON file (one decision vector), uploaded at https://optimise.esa.int/submit:
```json
[
  {
    "decisionVector": [ x ],
    "problem": "morphing-rovers",
    "challenge": "spoc-2-morphing-rovers"
  }
]
```
Python: `from submission_helper import create_submission` (https://api.optimize.esa.int/data/tools/submission_helper.py), or `vsi.esa.write_submission`.

## Useful UDP features
`udp.fitness(x)`, `udp.pretty(x)` (table per scenario), `udp.plot(x, plot_modes=True, plot_mode_efficiency=True)`,
`udp.example()`; constants `NUM_BIASES`, `NUM_WEIGHTS`, `NUM_MODES`, `MASK_SIZE`, `MASK_CENTRES`;
`MAPS_PER_EVALUATION` / `SCENARIOS_PER_MAP` to train on fewer scenarios. Gradients are off by default
(remove `self._turn_off_gradients()` to train with gradient descent).

## Why it is hard
~19 000 continuous parameters, a non-differentiable simulator and an expensive fitness. Typical approaches:
evolution strategies (CMA-ES / sep-CMA, OpenAI-ES) on a subset of parameters, hand-designed masks + a simple
controller first, then neuro-evolution.
