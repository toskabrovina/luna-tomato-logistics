"""Progress from docs/REQUIREMENTS.md: percentage, next step, and automatic ticks for what VSI can verify.

A requirement line can carry a hidden tag, e.g. `- [ ] Baseline runs end to end <!-- auto:baseline -->`.
`auto_tick` ticks such a line only when the matching fact is true on disk:
    data      official data files downloaded (ESA) / instance generator works (custom projects)
    baseline  the ESA random-search baseline ran with the official fitness (results/metrics.csv)
    metrics   results/metrics.csv contains time, memory and evaluation counts from a real run
Untagged lines are never ticked automatically: the student (or the agent) ticks them when truly done.
"""

from __future__ import annotations

import csv
import importlib.util
import re
from pathlib import Path

from . import data

ITEM = re.compile(r"^(\s*- \[)( |x|X)(\] )(.+?)(\s*<!-- auto:(\w+) -->)?\s*$")


def items(req: str | Path) -> list[dict]:
    out = []
    for i, line in enumerate(Path(req).read_text(encoding="utf-8").splitlines()):
        m = ITEM.match(line)
        if m:
            out.append({"line": i, "done": m.group(2).lower() == "x", "text": m.group(4).strip(), "auto": m.group(6)})
    return out


def facts(root: str | Path = ".") -> set[str]:
    root = Path(root)
    man = data.manifest(root)
    found = set()
    if man.get("kind") == "esa":
        if (man.get("data") or man.get("udp")) and not data.missing(root):
            found.add("data")
        rows = _rows(root / "results" / "metrics.csv")
        ran = [r for r in rows if r.get("fitness") not in (None, "", "None")]
        if any(r.get("algorithm") == "random_search" for r in ran):
            found.add("baseline")
        if ran and all(k in ran[0] for k in ("seconds", "peak_mb", "evaluated")):
            found.add("metrics")
    elif _generator_works(root):
        found.add("data")
    return found


def auto_tick(req: str | Path, found: set[str]) -> list[str]:
    """Tick tagged lines whose fact is true. Returns the texts that were ticked now."""
    req = Path(req)
    lines = req.read_text(encoding="utf-8").splitlines()
    ticked = []
    for it in items(req):
        if not it["done"] and it["auto"] in found:
            lines[it["line"]] = ITEM.sub(lambda m: f"{m.group(1)}x{m.group(3)}{m.group(4)}{m.group(5) or ''}",
                                         lines[it["line"]])
            ticked.append(it["text"])
    if ticked:
        req.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return ticked


def summary(req: str | Path) -> tuple[int, int, str | None]:
    """(done, total, first requirement still open)."""
    its = items(req)
    todo = [it["text"] for it in its if not it["done"]]
    return len(its) - len(todo), len(its), (todo[0] if todo else None)


def bar(done: int, total: int, width: int = 16) -> str:
    filled = round(width * done / max(total, 1))
    return "█" * filled + "░" * (width - filled) + f" {100 * done // max(total, 1)}%  ({done}/{total})"


def _rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _generator_works(root: Path) -> bool:
    path = root / "src" / "generator.py"
    if not path.exists():
        return False
    try:
        spec = importlib.util.spec_from_file_location(f"_vsi_gen_{abs(hash(str(path)))}", path)
        gen = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gen)
        return gen.make_instance(next(iter(gen.SIZES)), seed=0) is not None
    except Exception:
        return False
