"""Helpers for ESA SpOC challenges (https://optimise.esa.int).

Each SpOC challenge publishes a Python "UDP" (user-defined problem) class in an official GitHub repo,
with fitness(x), pretty(x), plot(x), example(). These helpers load that class from a local clone and
write submission files in the format the ESA site expects.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def load_module(path: str | Path):
    """Import a Python file from a cloned official repo (e.g. the challenge's UDP file)."""
    path = Path(path)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_submission(challenge: str, problem: str, vectors: list, path: str | Path) -> Path:
    """Save decision vector(s) as an ESA submission JSON.

    `vectors` is one decision vector or a list of them (multi-objective challenges allow several).
    Check the challenge page for the exact limit and whether a single vector or a list is expected.
    """
    data = [{"decisionVector": vectors, "problem": problem, "challenge": challenge}]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))
    return path
