# Requirements checklist

Tick a box (`[x]`) only when it is done **and** verified. `python tasks.py check` reads this file.

## Problem & data
- [x] Problem statement copied from the official page (docs/PROBLEM.md)
- [ ] Official data + evaluation code downloaded and wired (`python tasks.py data`) <!-- auto:data -->
- [ ] Official packages installed (heyoka) and the target Morse signal generated
- [ ] Own signal reconstruction / MSE matches udp.fitness on sample solutions
- [ ] Official example / sample solution evaluates to the expected value (test)

## Algorithms
- [ ] Baseline (random search) runs end to end with the official fitness <!-- auto:baseline -->
- [ ] Constructive heuristic: greedily add (orbit, phase) occultations that cover target pulses
- [ ] Pruning step: remove spacecraft while mse ≤ 0.05
- [ ] Phase optimisation for fixed selection (local search / SA / CMA-ES)
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
