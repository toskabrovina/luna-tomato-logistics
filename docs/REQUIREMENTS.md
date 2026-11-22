# Requirements checklist

Tick a box (`[x]`) only when it is done **and** verified. `python tasks.py check` reads this file.

## Problem & data
- [x] Problem statement copied from the official page (docs/PROBLEM.md)
- [x] Official data + evaluation code downloaded and wired (`python tasks.py data`) <!-- auto:data -->
- [x] Own instance parser (e l d weight) + validity checker written
- [x] Own fitness = official fitness on sample solutions (including invalid → 0)
- [x] Official example / sample solution evaluates to the expected value (test)

## Algorithms
- [x] Baseline (random search) runs end to end with the official fitness <!-- auto:baseline -->
- [x] Greedy by weight (sort transfers, add if no conflict)
- [x] Improvement method (local search with 1-swap / 2-swap, simulated annealing or tabu)
- [x] Upper bound for comparison (e.g. LP relaxation or best 2D matching) to measure the optimality gap
- [ ] (Optional) Advanced trajectory-matching problem
- [x] At least one idea designed or modified by us (documented in DECISIONS.md)

## Analysis
- [x] Pseudocode for every algorithm (README)
- [x] Time & space complexity for every algorithm (README)
- [x] Why the problem is hard / why heuristics are used
- [x] Proof sketch / reference that weighted 3D matching is NP-hard

## Experiments
- [x] Metrics recorded: fitness, runtime, peak memory, fitness evaluations <!-- auto:metrics -->
- [ ] Results on every problem instance
- [x] Algorithm comparison table
- [x] Convergence plot (best fitness over time) per problem
- [x] Theory vs measured performance (scaling discussion)

## Delivery
- [ ] Submission JSON per problem, checked with the official fitness function
- [x] README report complete (all sections filled)
- [ ] Defense preparation: can explain every algorithm and design decision
