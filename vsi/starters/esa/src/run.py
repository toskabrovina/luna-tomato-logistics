"""Run every optimiser on every problem instance with the official ESA fitness; save metrics + submissions."""

from __future__ import annotations

import argparse
import random

from vsi.esa import write_submission
from vsi.experiment import run_experiments

from algorithms import ALGORITHMS
from esa_problem import CHALLENGE, PROBLEM_IDS, load_udp


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--budget", type=float, default=10.0, help="seconds per optimiser per problem")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--problems", nargs="*", default=PROBLEM_IDS, choices=PROBLEM_IDS)
    args = parser.parse_args(argv)

    instances = {}
    for p in args.problems:          # a problem whose official code cannot load is skipped, not fatal
        try:
            instances[p] = load_udp(p)
        except (ImportError, SystemExit) as exc:
            print(f"skipping {p}: {exc}")
    if not instances:
        raise SystemExit("No official problem could be loaded: run `python tasks.py data` and install "
                         "requirements-official.txt.")

    def wrap(name, algo):
        def run(udp, meter):
            return algo(udp, args.budget, meter, random.Random(args.seed))
        return run

    def score(inst_name, udp, vectors):
        if not vectors:
            return {"fitness": None}
        fits = [list(udp.fitness(x)) for x in vectors]
        if inst_name != "None":
            write_submission(CHALLENGE, inst_name, vectors[0] if len(vectors) == 1 else vectors,
                             f"results/submission_{inst_name}.json")
        if len(fits[0]) >= 2 and getattr(udp, "get_nobj", lambda: 1)() >= 2:   # multi-objective
            return {"fitness": min(f[0] for f in fits), "solutions": len(vectors), "_front": [f[:2] for f in fits]}
        return {"fitness": min(fits)[0]}

    run_experiments({name: wrap(name, algo) for name, algo in ALGORITHMS.items()}, instances, score)


if __name__ == "__main__":
    main()
