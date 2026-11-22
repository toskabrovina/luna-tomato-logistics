# Requirements checklist

## Implementation
- [ ] Timeline graph model (events, attributes, dependencies, time-travel edges)
- [ ] Generator / input parser for timelines of increasing size <!-- auto:data -->
- [ ] Cycle / contradiction detection (DFS, SCC, topological sort)
- [ ] Paradox explanation: events + responsible dependency
- [ ] Repair operations with costs
- [ ] Minimum-cost repair: exact method (small inputs)
- [ ] Minimum-cost repair: heuristic / pruned method (large inputs)
- [ ] Alternative timeline exploration with limit
- [ ] At least one idea designed or modified by us (DECISIONS.md)

## Analysis
- [ ] Pseudocode and complexity for every algorithm
- [ ] NP-hardness discussion of minimum-cost repair (feedback vertex/arc set)

## Experiments
- [ ] Metrics: paradoxes detected, events analysed, timelines explored, min cost, time, memory, % pruned
- [ ] Increasing timeline size
- [ ] Comparison of approaches, graphs and tables

## Delivery
- [ ] README report complete
- [ ] Defense preparation
