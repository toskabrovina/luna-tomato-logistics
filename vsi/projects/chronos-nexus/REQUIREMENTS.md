# Requirements checklist

## Model & data
- [ ] Galaxy graph with all route / planet / ship / mission / infrastructure attributes
- [ ] Dataset generator: small, medium, large, extreme <!-- auto:data -->
- [ ] Dynamic event stream

## Algorithms (≥ 3 different techniques, ≥ 1 own design)
- [ ] Multi-objective route planning (Dijkstra / A* / Pareto)
- [ ] Resource allocation (min-cost flow or alternative)
- [ ] Mission scheduling (greedy / local search / GA / B&B)
- [ ] Infrastructure selection under budget (knapsack / DP / B&B)
- [ ] Incremental dynamic re-planning (only affected decisions)
- [ ] Shortage prediction + proactive scheduling
- [ ] Uncertainty handling (risk / failure probability / variable times)
- [ ] Search-space reduction (pruning, dominance, memoization, beam…)
- [ ] Algorithm designed or significantly modified by us (DECISIONS.md)
- [ ] (Advanced) Meta-optimisation layer choosing algorithms
- [ ] (Advanced) Hybrid pipeline compared experimentally

## Analysis
- [ ] Formal problem definition + mathematical formulation + scoring function with justified weights
- [ ] Pseudocode, correctness arguments, complexity (best/avg/worst, space) per algorithm
- [ ] NP-hard components identified and justified heuristics

## Experiments
- [ ] All required statistics reported (score, deliveries, shortages, states explored, re-planning time, memory…)
- [ ] Scalability across all dataset sizes
- [ ] Algorithm comparison, worst-case behaviour, pruning effectiveness
- [ ] Respects time/memory budget

## Delivery
- [ ] Technical report in GitHub README (all sections)
- [ ] Build/run instructions and tests
- [ ] Defense preparation
