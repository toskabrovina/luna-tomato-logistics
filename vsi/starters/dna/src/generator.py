"""Simulated sequencing data with known truth (so accuracy can be measured).

make_instance(size) -> dict with:
    genome      the true reference sequence
    reads       list of reads (some reverse-complemented, with substitutions / insertions / deletions)
    truth       list of (start_position, is_reverse) per read  — for evaluation only, never for assembly!
    mutations   list of (position, ref_base, alt_base) planted in the sample vs the reference
"""

from __future__ import annotations

import random

BASES = "ACGT"
COMPLEMENT = str.maketrans("ACGT", "TGCA")

# genome length, read length, coverage, error rate
SIZES = {
    "small": (2_000, 100, 10, 0.01),
    "medium": (20_000, 150, 15, 0.01),
    "large": (200_000, 150, 20, 0.01),
    "huge": (1_000_000, 150, 30, 0.01),
}


def reverse_complement(seq: str) -> str:
    return seq.translate(COMPLEMENT)[::-1]


def add_errors(read: str, rate: float, rng: random.Random) -> str:
    out = []
    for base in read:
        r = rng.random()
        if r < rate / 3:                       # substitution
            out.append(rng.choice(BASES.replace(base, "")))
        elif r < 2 * rate / 3:                 # deletion
            continue
        elif r < rate:                         # insertion
            out.extend([base, rng.choice(BASES)])
        else:
            out.append(base)
    return "".join(out)


def make_instance(size: str, seed: int = 0, n_mutations: int = 5, reverse_prob: float = 0.5) -> dict:
    rng = random.Random(seed)
    length, read_len, coverage, error = SIZES[size]
    genome = "".join(rng.choice(BASES) for _ in range(length))

    sample = list(genome)                      # the sequenced individual differs by a few SNPs
    mutations = []
    for pos in rng.sample(range(length), n_mutations):
        alt = rng.choice(BASES.replace(sample[pos], ""))
        mutations.append((pos, sample[pos], alt))
        sample[pos] = alt
    sample = "".join(sample)

    reads, truth = [], []
    for _ in range(length * coverage // read_len):
        start = rng.randrange(0, length - read_len + 1)
        read = add_errors(sample[start:start + read_len], error, rng)
        rev = rng.random() < reverse_prob
        reads.append(reverse_complement(read) if rev else read)
        truth.append((start, rev))
    return {"genome": genome, "reads": reads, "truth": truth, "mutations": sorted(mutations),
            "params": {"read_len": read_len, "coverage": coverage, "error_rate": error}}
