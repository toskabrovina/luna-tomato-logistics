# DNA Genome Reconstruction from Noisy Sequencing Reads

Source: professor's brief (condensed here; keep the original brief next to this file if you have it).

## Goal
Reconstruct an unknown DNA sequence from many short, unordered, noisy reads. Reads may overlap, contain
substitutions/insertions/deletions, be duplicated, and appear forward or as reverse complement.
Minimise time and memory while maximising reconstruction accuracy.

## Required components
1. Efficient overlap detection between reads.
2. Indexing (k-mer hashing, suffix arrays/trees, inverted index) to avoid all-pairs O(n²) comparison.
3. Overlap graph: reads = nodes, overlaps = weighted directed edges (quality / length / confidence).
4. Reconstruction by traversing/simplifying the graph (greedy, graph optimisation, DP, own method).
5. Error handling with approximate matching / edit distance (local or banded alignment).
6. Consensus building, error correction, detection of mutations (substitutions, insertions, deletions).
7. Scalability evaluation on growing datasets (thousands → hundreds of thousands of reads).

## Input
Reads (varying lengths), optional quality scores, parameters: minimum overlap, allowed error rate, k-mer size.

## Output
Reconstructed sequence; variant/mutation report; statistics: reads used, overlaps found, average overlap
quality, reconstruction length, execution time, memory.

## Metrics
Accuracy vs reference, edit distance to the original, correctly detected mutations, % reads incorporated,
time, memory, number of candidate read comparisons, scalability.

## Challenges
Avoiding O(n²); noise vs real mutations; huge overlap graphs; choosing k and thresholds; repeats;
accuracy vs resources.

## VSI starter
`src/generator.py` simulates a reference genome and noisy reads (with known truth, so accuracy can be measured).
