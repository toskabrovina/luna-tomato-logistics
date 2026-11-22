"""Project catalog: find a student's project by name and scaffold it."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

PKG = Path(__file__).resolve().parent
PROJECTS = PKG / "projects"
STARTERS = PKG / "starters"
TEMPLATES = PKG / "templates"

AGENT_FILES = {  # file -> how to render AGENTS.md for each AI tool
    "AGENTS.md": "plain",                               # Codex, Cursor, Copilot (also reads it), many others
    "GEMINI.md": "plain",                               # Gemini CLI
    ".github/copilot-instructions.md": "plain",         # GitHub Copilot
    ".cursor/rules/vsi.mdc": "cursor",              # Cursor rules
    "CLAUDE.md": "claude",                              # Claude Code (imports AGENTS.md)
}


def load() -> list[dict]:
    return json.loads((PROJECTS / "index.json").read_text(encoding="utf-8"))["projects"]


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9*]+", text.lower()))


def find(query: str) -> list[tuple[int, dict]]:
    """Rank projects by word overlap with title, slug and aliases (exact slug wins)."""
    q = _words(query)
    ranked = []
    for p in load():
        if query.strip().lower() == p["slug"]:
            return [(100, p)]
        hay = _words(" ".join([p["title"], p["slug"].replace("-", " "), *p["aliases"]]))
        score = len(q & hay)
        score += sum(2 for a in p["aliases"] if a in query.lower())
        if score:
            ranked.append((score, p))
    return sorted(ranked, key=lambda sp: -sp[0])


def get(slug: str) -> dict:
    for p in load():
        if p["slug"] == slug:
            return p
    matches = find(slug)
    if matches:
        return matches[0][1]
    raise KeyError(f"unknown project '{slug}' — try `vsi list`")


def _render(text: str, project: dict) -> str:
    kind_notes = ""
    if project["kind"] == "esa":
        kind_notes = (
            f"- ESA SpOC challenge ({project.get('series')}). Data + official scorer come from ESA"
            + (f": {project['official_repo']}" if project.get("official_repo") else " (find the repo on the challenge page)")
            + ".\n- Final answers must be checked with the official ESA fitness function before submitting.\n"
        )
        if not project.get("verified"):
            kind_notes += ("- docs/PROBLEM.md is only a stub: FIRST read the challenge page (it is JavaScript-rendered: "
                           "open it in a browser) and replace PROBLEM.md and REQUIREMENTS.md with the real spec.\n")
    for key, value in {"title": project["title"], "slug": project["slug"],
                       "source": project.get("source") or "not provided — ask the professor",
                       "kind_notes": kind_notes, "slug_esa": project["slug"],
                       "challenge_id": project.get("challenge_id") or project["slug"],
                       "problem_ids": json.dumps(project.get("problem_ids") or [])}.items():
        text = text.replace(f"[[{key}]]", value).replace("{" + key + "}", value)
    return text


def _copy_tree(src: Path, dst: Path, project: dict, keep: frozenset = frozenset()) -> None:
    for path in src.rglob("*"):
        if path.is_dir() or "__pycache__" in path.parts:
            continue
        target = dst / path.relative_to(src)
        if target.resolve() in keep:  # the student's own file: never overwrite it
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix in {".md", ".py", ".txt", ".toml", ".json", ""} or path.name == ".gitignore":
            target.write_text(_render(path.read_text(encoding="utf-8"), project), encoding="utf-8")
        else:
            shutil.copy2(path, target)


def _esa_stub_docs(project: dict) -> tuple[str, str]:
    problem = (f"# {project['title']}\n\nESA {project.get('series')} challenge.\n"
               f"Source: {project['source']}\n"
               + (f"Official repo: {project['official_repo']}\n" if project.get("official_repo") else "")
               + f"\n{project['summary']}\n\n**TODO (first task):** open the source page in a browser and copy the "
               "problem definition here: input/data, decision vector, objectives, constraints, submission format.\n")
    requirements = """# Requirements checklist

## Problem & data
- [ ] Real problem statement copied into docs/PROBLEM.md
- [ ] Official repo cloned, UDP wired in src/esa_problem.py, data downloaded
- [ ] Official example solution evaluates correctly (test)

## Algorithms
- [ ] Baseline (random search) runs end to end
- [ ] Constructive / greedy heuristic
- [ ] Improvement method (local search / SA / GA / …)
- [ ] At least one idea designed or modified by us (DECISIONS.md)

## Analysis
- [ ] Pseudocode, time & space complexity for every algorithm
- [ ] Why the problem is hard / why heuristics

## Experiments
- [ ] Metrics: fitness, time, memory, evaluations
- [ ] Results on all problem instances, comparison table, charts
- [ ] Theory vs measured performance

## Delivery
- [ ] Submission file(s) verified with the official fitness
- [ ] README report complete
- [ ] Defense preparation
"""
    return problem, requirements


def scaffold(slug: str, target: str | Path, force: bool = False) -> Path:
    """Create a ready-to-work project for `slug` in `target`."""
    project = get(slug)
    target = Path(target)
    if target.exists() and any(target.iterdir()) and not force:
        raise SystemExit(f"{target} is not empty (use --force to add VSI files into an existing repo).")
    target.mkdir(parents=True, exist_ok=True)
    # Files the student already had (existing repo + --force) stay untouched.
    keep = frozenset(f.resolve() for f in target.rglob("*") if f.is_file() and "vsi" not in f.relative_to(target).parts[:1])

    starter = project.get("starter", "generic")
    _copy_tree(STARTERS / "common", target, project, keep)
    if starter != "esa":
        _copy_tree(STARTERS / "generic", target, project, keep)  # run.py, algorithms.py, generator.py
    if (STARTERS / starter).exists():
        _copy_tree(STARTERS / starter, target, project, keep)    # project-specific files override

    docs = target / "docs"
    docs.mkdir(exist_ok=True)
    report = docs / "REPORT.md"
    if (target / "README.md").resolve() in keep and report.resolve() not in keep:
        # The student kept their own README: the report template (with its automatic blocks) goes to docs/REPORT.md.
        template = _render((STARTERS / "common" / "README.md").read_text(encoding="utf-8"), project)
        report.write_text(template.replace("](docs/", "]("), encoding="utf-8")
    pdir = PROJECTS / project["slug"]
    if (pdir / "PROBLEM.md").exists():
        files = {name: (pdir / name).read_text(encoding="utf-8") for name in ("PROBLEM.md", "REQUIREMENTS.md")}
    else:
        files = dict(zip(("PROBLEM.md", "REQUIREMENTS.md"), _esa_stub_docs(project)))
    files["PROMPTS.md"] = (TEMPLATES / "PROMPTS.md").read_text(encoding="utf-8")
    for name, text in files.items():
        if (docs / name).resolve() not in keep:
            (docs / name).write_text(text, encoding="utf-8")

    if project.get("requires") and (target / "requirements-official.txt").resolve() not in keep:
        (target / "requirements-official.txt").write_text(
            "# Packages needed by the official ESA evaluation code (official/*.py).\n"
            "# pykep / pygmo / heyoka install most easily with conda + Python 3.11:\n"
            "#   conda install -c conda-forge pykep pygmo heyoka\n" + "\n".join(project["requires"]) + "\n",
            encoding="utf-8")
    if (docs / "DIAGRAMS.md").resolve() not in keep:
        from .diagram_specs import write_docs
        write_docs(target, project, png=False)
    write_agent_files(target, project)
    write_manifest(target, project)
    bundle_library(target)
    return target


def write_manifest(target: Path, project: dict) -> Path:
    """vsi.json: what tasks.py needs to know about the project (kind, ids, official data files)."""
    keys = ("slug", "title", "kind", "source", "summary", "challenge_id", "problem_ids", "data", "udp", "requires")
    path = Path(target) / "vsi.json"
    path.write_text(json.dumps({k: project[k] for k in keys if project.get(k) is not None}, indent=2,
                               ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def bundle_library(target: Path) -> Path:
    """Put the whole VSI folder inside the project as `vsi/`, so it works without `pip install`.

    Skipped when VSI already lives in that project (the student copied the folder there).
    """
    dest = Path(target) / "vsi"
    if dest.resolve() != PKG:
        shutil.copytree(PKG, dest, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return dest


GENERATED = "<!-- vsi:generated -->"
BOOTSTRAP = "<!-- vsi:bootstrap -->"
BLOCK = ("<!-- vsi:agents:start -->", "<!-- vsi:agents:end -->")


def write_agent_files(target: Path, project: dict) -> list[Path]:
    """Write the same instructions in the file each AI tool reads automatically.

    A file VSI wrote (or the bootstrap AGENTS.md shipped with the vsi folder) is replaced.
    A file the student wrote is kept: the VSI instructions are added in a marked block at its end
    (and that block is refreshed on later runs).
    """
    body = _render((TEMPLATES / "AGENTS.md").read_text(encoding="utf-8"), project)
    written = []
    for rel, style in AGENT_FILES.items():
        path = Path(target) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        content = "@AGENTS.md\n" if style == "claude" else body
        if style == "cursor":
            ours = f"---\ndescription: VSI project rules\nalwaysApply: true\n---\n{GENERATED}\n\n{body}"
        else:
            ours = f"{GENERATED}\n{content}"
        existing = path.read_text(encoding="utf-8") if path.exists() else None
        if existing is None or GENERATED in existing or BOOTSTRAP in existing:
            text = ours
        else:
            block = f"{BLOCK[0]}\n{content.rstrip()}\n{BLOCK[1]}"
            pattern = re.compile(re.escape(BLOCK[0]) + r".*?" + re.escape(BLOCK[1]), re.S)
            text = pattern.sub(lambda _: block, existing) if pattern.search(existing) \
                else existing.rstrip() + "\n\n" + block + "\n"
        path.write_text(text, encoding="utf-8")
        written.append(path)
    return written
