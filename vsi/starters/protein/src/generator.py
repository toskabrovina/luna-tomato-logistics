"""Protein sequences + HP-model helpers.

The HP model (hydrophobic / polar) is the classic simplified folding model: each amino acid is H or P;
a fold is a self-avoiding walk on a lattice; every pair of H residues that are lattice neighbours but not
consecutive in the chain contributes -1 to the energy. You may use it as a starting point and extend it
(the brief asks you to define and justify your own energy function).
"""

from __future__ import annotations

import random

AMINO_ACIDS = "ACDEFGHIKLMNPQRSTVWY"
HYDROPHOBIC = set("AVILMFWC")          # common simple classification
SIZES = {"small": 12, "medium": 25, "large": 50, "huge": 100}
MOVES_2D = {"U": (0, 1), "D": (0, -1), "L": (-1, 0), "R": (1, 0)}


def to_hp(sequence: str) -> str:
    return "".join("H" if aa in HYDROPHOBIC else "P" for aa in sequence)


def make_instance(size: str, seed: int = 0) -> dict:
    rng = random.Random(seed)
    seq = "".join(rng.choice(AMINO_ACIDS) for _ in range(SIZES[size]))
    return {"sequence": seq, "hp": to_hp(seq)}


def coordinates(moves: str, start=(0, 0)) -> list[tuple[int, int]]:
    """Relative 2D moves (e.g. 'RRUL…', length n-1) -> lattice coordinates."""
    pos = [start]
    for m in moves:
        dx, dy = MOVES_2D[m]
        x, y = pos[-1]
        pos.append((x + dx, y + dy))
    return pos


def is_valid(coords) -> bool:
    """Self-avoiding: no two residues on the same lattice point."""
    return len(set(coords)) == len(coords)


def hp_energy(hp: str, coords) -> int:
    """Standard HP energy (lower is better). Returns a large penalty for invalid folds."""
    if not is_valid(coords):
        return 10**6
    index = {c: i for i, c in enumerate(coords)}
    energy = 0
    for i, (x, y) in enumerate(coords):
        if hp[i] != "H":
            continue
        for dx, dy in MOVES_2D.values():
            j = index.get((x + dx, y + dy))
            if j is not None and j > i + 1 and hp[j] == "H":
                energy -= 1
    return energy
