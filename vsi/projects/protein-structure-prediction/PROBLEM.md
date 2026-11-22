# AI-Based Protein Structure Prediction and Optimization

Source: professor's brief (condensed here; keep the original brief next to this file if you have it).

## Goal
Given an amino-acid sequence, find a plausible 2D or 3D structure (lattice positions) that minimises an
energy (or maximises a fitness) function. Exhaustive search is infeasible, so design efficient search.

## Required components
1. Representation: amino acids placed in 2D/3D space; invalid structures (two residues on one cell) are
   detected and rejected.
2. Energy/fitness function, clearly explained, e.g. `E(S) = E_interaction + E_collision + E_structure`
   (attractions, repulsions, collisions, neighbours, compactness).
3. **At least two different search algorithms** (GA, simulated annealing, beam search, A*, branch & bound,
   local search, hybrids), with justification.
4. **At least one search-space reduction** (pruning, bounds, beam width, duplicate elimination, symmetry
   reduction, branch ordering) and its effect on complexity and practice.
5. Local improvement moves that keep validity (rotations, mutations, local moves, segment rearrangement).
6. Time & space complexity analysis; experiments on proteins of different lengths; comparison.

## Input
Sequence (e.g. `ACDEFGHIKLMNPQRSTVWY`), length, energy parameters, time/compute budget, optional constraints.

## Output
Structure, final energy, configurations explored, valid vs invalid configurations, time, memory,
visualisation/text representation, algorithm comparison.

## Metrics
Energy, validity, configurations explored, % search space pruned, time, memory, convergence speed,
scalability with length, solution quality. Graphs and tables vs problem size are required.

## Advanced (optional)
Hybrid pipeline (e.g. GA → beam search → local search/SA) compared experimentally to the single algorithms.

## Important (from the brief)
Using an existing protein-folding library without your own algorithm and analysis does **not** satisfy the project.

## VSI starter
`src/generator.py` creates random sequences and maps them to the HP model (hydrophobic/polar) — a common,
simple energy model you may use or extend.
