"""Chat packs: ONE file per project for students who use ChatGPT, Gemini or Claude in the browser / app
(no access to their files). They upload `chat/<slug>.md` and the AI guides them step by step.

Regenerate after changing the catalog:  python -m vsi chat   (writes chat/*.md next to the vsi folder)
"""

from __future__ import annotations

from pathlib import Path

from . import catalog

REPO = "https://github.com/andikuqi/vsi"

AI_RULES = """\
## Instructions for the AI (read this first, follow it the whole conversation)

You are helping a university student with an **Algorithm Design & Analysis** project. The student may be a
beginner. **Reply in the student's language** (often Albanian). You cannot see their computer, so:

1. Work in **small steps**. Give the exact commands to copy, then **wait** for the student to paste the output.
2. Before the first command, ask which system they use. Use `python` on **Windows** and `python3` on
   **macOS / Linux** in every command you give.
3. When you write code, give the **complete content of one file** and its path (e.g. `src/algorithms.py`),
   never fragments to merge. After every change the student runs `python tasks.py test`.
4. The algorithms are the **student's own work**: explain the idea, pseudocode and complexity, keep the code
   simple and commented, and check they understand it (they must defend it in front of the professor).
   Do not import solver / optimisation libraries for the core algorithm.
5. Never invent results. Numbers in the report come from `results/metrics.csv`.

### Step 1 — set up the project (once)
1. Python 3.10 or newer: `python --version` (Windows) / `python3 --version` (macOS, Linux).
   If it is missing or older: install it from https://www.python.org/downloads/ (Windows: tick "Add to PATH").
2. Download VSI: {repo} → **Code → Download ZIP**, unzip it.
3. Copy the folder **`vsi`** and the file **`AGENTS.md`** into the student's project folder
   (an empty folder or their existing GitHub repo).
4. Open a terminal **in the project folder** (Windows: in the folder, type `cmd` in the address bar and press
   Enter; macOS: right-click the folder → New Terminal at Folder; Linux: right-click → Open in Terminal) and run:
   ```
   python -m vsi new {slug} . --force
   python tasks.py start
   ```
   (`python3` instead of `python` on macOS / Linux.) `start` installs what is needed, downloads the data,
   runs the tests and a first run, makes charts, starts the report and prints **progress + the next step**.
   Ask the student to paste that output, then explain it in a few simple sentences.

### Step 2 — every work session
1. The student runs `python tasks.py context` and uploads the new **`CONTEXT.md`** (their current code,
   progress and results) to this chat.
2. Take the **next step** it shows (first open requirement), explain it, write the code, then:
   `python tasks.py test` → tick the requirement in `docs/REQUIREMENTS.md` → `python tasks.py report`.
3. Useful commands: `python tasks.py run` (experiments), `python tasks.py plots` (charts),
   `python tasks.py check` (progress + next step).
"""


def build(project: dict) -> str:
    slug = project["slug"]
    pdir = catalog.PROJECTS / slug
    problem = (pdir / "PROBLEM.md").read_text(encoding="utf-8") if (pdir / "PROBLEM.md").exists() \
        else catalog._esa_stub_docs(project)[0]
    reqs = (pdir / "REQUIREMENTS.md").read_text(encoding="utf-8") if (pdir / "REQUIREMENTS.md").exists() \
        else catalog._esa_stub_docs(project)[1]
    head = (f"# VSI chat pack — {project['title']}\n\n"
            "> **For students using ChatGPT, Gemini or Claude in the browser or the app.**\n"
            "> Upload this file to the chat and write: *\"Read this file and guide me step by step.\"*\n"
            "> SQ: Ngarkoje këtë skedar në chat dhe shkruaj: *\"Lexo këtë skedar dhe më udhëhiq hap pas hapi.\"*\n\n"
            f"Project id (slug): `{slug}` · Source: {project.get('source') or 'ask the professor'}\n\n")
    from .diagram_specs import MODELS, pipeline
    diagrams = "\n---\n\n## Diagrams\n\n### Problem model\n\n" + (MODELS[slug].mermaid() if slug in MODELS else "")
    diagrams += "\n\n### Project pipeline\n\n" + pipeline(project).mermaid() + "\n"
    return (head + AI_RULES.format(repo=REPO, slug=slug)
            + "\n---\n\n## The project (docs/PROBLEM.md)\n\n" + _demote(problem)
            + diagrams
            + "\n---\n\n## Requirements checklist (docs/REQUIREMENTS.md)\n\n" + _demote(reqs))


def _demote(markdown: str) -> str:
    """Nest the document's headings one level below the pack's '##' sections."""
    return "\n".join("#" + line if line.startswith("#") else line for line in markdown.splitlines()) + "\n"


def write_all(out_dir: str | Path) -> list[Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for project in catalog.load():
        path = out / f"{project['slug']}.md"
        path.write_text(build(project), encoding="utf-8")
        written.append(path)
    return written
