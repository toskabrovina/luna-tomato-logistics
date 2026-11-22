"""Load the official ESA problem (UDP = "user defined problem") for this challenge.

`python tasks.py data` (or `start`) downloads, from the challenge page:
  - the official evaluation code, one file per problem -> official/<problem id>.py
  - the official data files -> data/... (the same paths the official code expects)
Every official file ends with a ready object `udp = ...` offering fitness(x), get_bounds() and usually
pretty(x), plot(x), example(). load_udp() returns that object.

Its Python packages are listed in requirements-official.txt (pykep / pygmo / heyoka: easiest with conda).
"""

from __future__ import annotations

import os
from pathlib import Path

from vsi.data import udp_path
from vsi.esa import load_module

ROOT = Path(__file__).resolve().parent.parent

CHALLENGE = "{challenge_id}"      # id used in submission files (see docs/PROBLEM.md)
PROBLEM_IDS = {problem_ids}      # official problem ids (docs/PROBLEM.md)


def udp_file(problem_id: str) -> Path:
    return udp_path(problem_id, ROOT)


def load_udp(problem_id: str):
    """The official `udp` object for one problem (SystemExit / ImportError with a clear message otherwise)."""
    path = udp_file(problem_id)
    if not path.exists():
        raise SystemExit(f"Official evaluation code missing ({path.name}): run `python tasks.py data`.")
    cwd = os.getcwd()
    os.chdir(ROOT)                    # the official code opens data/... relative to the project root
    try:
        return load_module(path).udp
    finally:
        os.chdir(cwd)
