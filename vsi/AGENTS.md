# VSI — read this first (for AI agents)

The student copied this `vsi/` folder into their project so that you (the AI agent) can set it up for them.
The student may be a beginner: do the commands yourself and explain each step in simple words
(reply in the student's language — often Albanian).

## Setup (do this once)
Run from the student's project root (the folder that contains `vsi/`). Use `python3` instead of `python` on macOS / Linux.
If `start` reports it created `.venv`, activate it (`source .venv/bin/activate`, Windows: `.venv\Scripts\activate`) before later commands.

1. Find their project: `python -m vsi find <words from the project title>`
   If you are unsure which one it is, run `python -m vsi list` and ask the student.
2. Add the project files: `python -m vsi new <slug> . --force`
   - The student's existing files are never overwritten.
   - This creates `AGENTS.md` in the project root: **from now on follow that file**.
3. `python tasks.py start` — installs packages, downloads the official data, runs the tests and a first run,
   makes charts, ticks what VSI can verify, fills the report and prints progress + the next step.
4. Show the student that summary (the ✅ lines and the progress bar) and explain, in a few short sentences,
   what is ready and what the next step is. Then offer to do that step with them.

## Rules
- Do not edit anything inside `vsi/` — it is a library. Import from it (`from vsi.measure import Meter`, …).
- Keep `vsi/` committed in the project so classmates and other agents have it.
- VSI gives infrastructure, not solutions: the algorithms are the student's work. Help them understand every line.
