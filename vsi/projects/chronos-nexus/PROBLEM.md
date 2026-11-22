# Chronos Nexus: Autonomous Interstellar Civilization Optimization

Source: professor's brief (condensed here; the original is long — keep it next to this file if you have it).

## Goal
Manage an interstellar civilization on a large **dynamic weighted graph** (planets, colonies, stations,
spacecraft, resources, routes, wormholes, missions, hazards). Continuously make high-quality decisions while
minimising computational cost. Decompose into subproblems; several are NP-hard.

## Model (minimum attributes)
- **Route (edge):** distance, travel time, fuel, risk, capacity, reliability/failure probability, availability.
- **Planet:** population, production, consumption, storage, technology, defense, strategic importance, location.
- **Resources:** food, water, energy, fuel, medicine, rare minerals, construction materials.
- **Spacecraft:** location, cargo capacity, fuel capacity, speed, current fuel, availability, reliability, cost.
- **Mission:** origin, destination, cargo type/amount, deadline, priority, importance, required capabilities.
- **Infrastructure:** cost, resource/population/energy impact, strategic value, construction time.

## Subproblems
1. **Multi-objective routing:** `Cost = w1·Distance + w2·Fuel + w3·Time + w4·Risk`, weights per mission
   (Dijkstra, A*, bidirectional, Pareto/multi-objective, dynamic shortest paths).
2. **Resource allocation:** minimise transport cost + shortage penalty + risk + waste (max-flow, min-cost flow…).
3. **Mission scheduling:** assign ships, departure, route, cargo, priority, delays (greedy, B&B, local search, GA…).
4. **Colony development:** choose facilities under budget (knapsack, facility location, DP, B&B).
5. **Dynamic events:** wormhole collapse, blocked/dangerous routes, ship loss, emergencies, production drops,
   new colonies… → **incremental re-planning** (only recompute what became invalid).
6. **Prediction:** e.g. food 10,000, net −400/day → shortage in 25 days → schedule delivery proactively.
7. **Uncertainty:** variable travel times, failure probabilities.

## Hard requirements (selection)
- ≥ 3 fundamentally different algorithmic techniques; ≥ 1 designed or significantly modified by the team.
- Own implementations (no "just call a solver"); search-space reduction (pruning, memoization, dominance,
  beam, bounds…); solution within a time/memory budget.
- Complexity (best/average/worst, space) + measured performance; correctness arguments; identify NP-hard parts.
- Datasets: small (100 planets/500 routes/50 missions), medium (1k/10k/500), large (10k/100k/5k),
  extreme (100k+/1M+/50k+). Final evaluation on a hidden galaxy, score ≈ αQ − βT − γM − δR.

## Output
Plan, ship assignments, allocation plan, mission schedule, routes, construction decisions, predicted shortages,
re-planning decisions, civilization score, detailed statistics (nodes/states explored, % search space reduced,
events handled, average re-planning time, total time, peak memory…).

## Deliverables
Modular source code with docs and tests; **technical report as the GitHub README**; experimental evaluation.

## VSI starter
`src/generator.py` builds random galaxies (planets, routes, ships, missions, events) at the four required sizes.
