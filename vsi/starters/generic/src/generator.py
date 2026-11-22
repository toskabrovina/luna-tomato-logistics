"""Instance generator / loader. Replace with the real data of your problem."""

from __future__ import annotations

import random

SIZES = {"small": 10, "medium": 100, "large": 1000}


def make_instance(size: str, seed: int = 0):
    rng = random.Random(seed)
    n = SIZES[size]
    return {"n": n, "values": [rng.randint(1, 100) for _ in range(n)]}
