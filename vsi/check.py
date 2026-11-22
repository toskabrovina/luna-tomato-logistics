"""Progress report from docs/REQUIREMENTS.md checkboxes: percentage, open items, next step."""

from __future__ import annotations

from pathlib import Path

from . import progress


def check(path: str | Path = "docs/REQUIREMENTS.md") -> int:
    """Print progress and the open requirements. Returns how many are still open."""
    done, total, nxt = progress.summary(path)
    print(f"Progress: {progress.bar(done, total)}")
    for it in progress.items(path):
        if not it["done"]:
            print(f"  [ ] {it['text']}")
    if nxt:
        print()
        print(f"Next step: {nxt}")
    return total - done


if __name__ == "__main__":
    check()
