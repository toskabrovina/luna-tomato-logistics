# Requirements checklist

## Implementation
- [ ] Read simulator / dataset loader (small, medium, large) <!-- auto:data -->
- [ ] Indexing technique (k-mer hash / suffix array / inverted index) for candidate pairs
- [ ] Approximate overlap detection (edit distance / banded alignment)
- [ ] Overlap graph construction with edge weights
- [ ] Reconstruction algorithm (greedy / graph-based / DP / own)
- [ ] Reverse-complement handling
- [ ] Error correction via consensus
- [ ] Variant / mutation detection report
- [ ] At least one idea designed or modified by us (DECISIONS.md)

## Analysis
- [ ] Pseudocode for every algorithm
- [ ] Time & space complexity for every algorithm
- [ ] Discussion: how indexing avoids O(n²); repeats; k-mer and threshold choice

## Experiments
- [ ] Metrics: accuracy, edit distance, % reads used, comparisons, time, memory
- [ ] Scaling experiment (reads: thousands → hundreds of thousands)
- [ ] Comparison of at least two approaches / parameter settings
- [ ] Graphs and tables in README

## Delivery
- [ ] README report complete
- [ ] Defense preparation
