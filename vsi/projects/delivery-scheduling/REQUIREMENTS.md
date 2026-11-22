# Requirements checklist

Tick a box (`[x]`) only when it is done **and** verified. `python tasks.py check` reads this file.

## Problem & data
- [x] Problem statement copied from the official page (docs/PROBLEM.md)
- [ ] Official data + evaluation code downloaded and wired (`python tasks.py data`) <!-- auto:data -->
- [ ] Own loader for candidates.txt into our data structures (asteroid -> station -> opportunities)
- [ ] Own evaluator (M_min + all constraints) equals udp.fitness on udp.example() and random solutions
- [ ] Official example / sample solution evaluates to the expected value (test)

## Algorithms
- [ ] Baseline (random search) runs end to end with the official fitness <!-- auto:baseline -->
- [ ] Greedy constructive (assign to the poorest station/material within windows)
- [ ] Window / station-order optimisation
- [ ] Improvement method (move / swap local search, simulated annealing or tabu)
- [ ] (Optional) exact model (ILP) on a small sub-instance to measure the optimality gap
- [ ] At least one idea designed or modified by us (documented in DECISIONS.md)

## Analysis
- [ ] Pseudocode for every algorithm (README)
- [ ] Time & space complexity for every algorithm (README)
- [ ] Why the problem is hard / why heuristics are used

## Experiments
- [ ] Metrics recorded: fitness, runtime, peak memory, fitness evaluations <!-- auto:metrics -->
- [ ] Results on every problem instance
- [ ] Algorithm comparison table
- [ ] Convergence plot (best fitness over time) per problem
- [ ] Theory vs measured performance (scaling discussion)

## Delivery
- [ ] Submission JSON per problem, checked with the official fitness function
- [ ] README report complete (all sections filled)
- [ ] Defense preparation: can explain every algorithm and design decision
