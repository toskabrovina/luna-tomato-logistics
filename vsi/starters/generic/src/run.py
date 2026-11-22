"""Run every algorithm in algorithms.ALGORITHMS on generated instances and save results/metrics.csv."""

from __future__ import annotations

import argparse

from vsi.experiment import run_experiments

import generator
from algorithms import ALGORITHMS, score


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="*", default=["small", "medium"], choices=list(generator.SIZES))
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args(argv)

    instances = {size: generator.make_instance(size, seed=args.seed) for size in args.sizes}
    run_experiments(ALGORITHMS, instances, lambda name, inst, result: score(inst, result))


if __name__ == "__main__":
    main()
