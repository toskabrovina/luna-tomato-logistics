# Time Travel Paradox Detection and Timeline Optimization

Source: professor's brief (condensed).

## Goal
Historical events and their causal dependencies form a directed graph. Time-travel actions add dependencies that
go backward in time and may create causal contradictions (paradoxes, e.g. the grandfather paradox).
Detect them, explain them, and repair the timeline with **minimum total modification cost**.

## Requirements
- Events as nodes, causal relations as directed edges; events have timestamp, location, affected entities,
  dependencies, consequences, importance/cost.
- Detect cycles and causal contradictions (topological sort, DFS/BFS, SCC, condensation, SAT/CSP…).
- Decide if a proposed time-travel sequence is valid; identify the events and dependency responsible.
- Repair operations with costs: remove / change / delay an event, prevent a time-travel action, branch a timeline.
- Find a consistent timeline with minimum cost (e.g. remove B = 10, remove E = 3, modify C = 5 → choose cheapest fix).
- Compare multiple approaches; complexity analysis; tests on increasingly complex timelines.

## Input
Number of events, timestamps, dependencies, time-travel operations, affected entities, modification costs,
constraints, maximum number of alternative timelines to explore.

## Output
Consistency verdict; detected paradoxes; events and dependency per paradox; repaired timeline; total repair cost;
alternative timelines explored; time; memory; metrics (paradoxes detected, events analysed, candidates explored,
minimum cost, scalability, % search space pruned).

## Note
Choosing a minimum-cost set of events/edges to break all cycles is a feedback vertex/arc set problem (NP-hard
in general) — justify exact methods for small inputs and heuristics/pruning for large ones.

## VSI starter
`src/generator.py` creates random timelines (forward DAG + time-travel back edges + costs) with a known number of paradoxes.
