# The Trigger Arc TSP

Source: **not provided in the assignment list** (only the title). Ask the professor for the official problem
statement and instances, then replace this file with it.

## What it usually means (verify!)
A Traveling Salesperson variant on a directed graph where traversing certain "trigger" arcs changes the cost
of other ("target") arcs later in the tour. The goal is a Hamiltonian tour of minimum total cost, taking those
cost changes into account. Like the TSP it is NP-hard, so exact methods (e.g. B&B, ILP) only scale to small
instances and heuristics/metaheuristics are needed for large ones.

## VSI starter
Generic template (measurement, experiments, plots, report). Add a loader once you have the official instances.
