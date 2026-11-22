<!-- vsi:generated -->
# Instructions for AI coding agents (Codex, Copilot, Gemini, Claude, Cursor, …)

Read this whole file before changing anything.

## Project
**Luna Tomato Logistics** — Algorithm Design & Analysis university project.
- Problem statement: `docs/PROBLEM.md` (source: https://optimise.esa.int/challenge/spoc-4-luna-tomato-logistics/About)
- Requirements checklist (definition of done): `docs/REQUIREMENTS.md`
- Milestones: `docs/PLAN.md` · Design log: `docs/DECISIONS.md`
- Diagrams: `docs/DIAGRAMS.md` (Mermaid: project pipeline, problem model, algorithm templates; PNGs in
  `docs/diagrams/`). Read the problem model first. For each algorithm the student designs, add its own diagram
  (`from vsi.diagrams import Diagram, Node`, see the end of DIAGRAMS.md) and use it in the report.
- ESA SpOC challenge (SpOC 4). Data + official scorer come from ESA: https://github.com/esa/SpOC4.
- Final answers must be checked with the official ESA fitness function before submitting.

This project was scaffolded by **VSI** (`python -m vsi new luna-tomato-logistics`). VSI provides the infrastructure;
the student's own algorithms are the point of the project.
- The `vsi/` folder is the VSI library, bundled so nothing needs installing. **Do not edit it**; import from it.

## Commands (run from the project root)
```
python tasks.py start      everything at once (data, tests, first run, charts, report, progress) — run it first
python tasks.py setup      install dependencies
python tasks.py data       download official data (if any)
python tasks.py test       run tests — must stay green
python tasks.py run        run all algorithms on all instances -> results/metrics.csv
python tasks.py plots      charts -> results/*.png
python tasks.py visualize  diagrams + pictures of the instances -> docs/diagrams/
python tasks.py report     refresh the automatic report blocks (status, results table, charts)
python tasks.py check      progress + next step (reads docs/REQUIREMENTS.md)
python tasks.py context    CONTEXT.md bundle for chat-only AIs
```

## VSI helpers (use them, do not rebuild them)
- `from vsi.measure import Meter` — time, peak memory, `meter.count()` per explored state, `meter.prune()` per skipped state.
- `from vsi.experiment import run_experiments` — every algorithm × every instance -> CSV.
- `from vsi.pareto import pareto_filter, hypervolume, select_best` — two minimised objectives.
- `from vsi.esa import load_module, write_submission` — ESA SpOC challenges.
- `src/generator.py` (custom projects) — instance generator with sizes in `SIZES`.

## When the student asks "what now?" / "çfarë bëj tash?"
1. Run `python tasks.py check` and take the **next step** it prints (first open requirement).
2. Propose it in 2–3 simple sentences: what it is, why it matters for the grade, how long it takes. Ask to start.
3. After finishing a step: `python tasks.py test`, tick the requirement, `python tasks.py report`,
   then tell the student the new progress and the next step.
Reply in the student's language (often Albanian). Assume they may be a beginner.

## Where code goes
- `src/algorithms.py` (or `src/<package>/algorithms/`) — one function per algorithm, registered in `ALGORITHMS`.
- `src/run.py` — experiment entry point (already wired).
- `tests/` — correctness tests for evaluator and algorithms.

## Rules
1. **Core algorithms are implemented in this repo**, not imported from optimisation / solver libraries
   (the course requires the student's own design and analysis). Libraries are fine for plotting, testing, I/O.
2. Every algorithm counts explored states with `meter.count()` (and `meter.prune()` when pruning).
3. Write a correctness test for every evaluator / algorithm (compare with brute force on tiny inputs when possible).
4. After every change run `python tasks.py test`. Never report a task as done while tests fail.
5. For every algorithm added or changed: append an entry to `docs/DECISIONS.md` (what, why, complexity,
   alternatives) and a README section (idea, pseudocode, time & space complexity).
6. When a requirement is truly done and verified, tick it in `docs/REQUIREMENTS.md`.
7. Keep code simple and commented: the student must explain every line at the defense.
   After finishing a feature, give the student a short plain-language explanation of it.
8. Never commit `data/`, `results/` or secrets.
9. Be transparent: keep the README "Tools used" section true (what VSI generated, what the student designed,
   which AI was used). VSI diagrams are templates; the student's own algorithms get their own diagrams.

## Definition of done
`python tasks.py check` shows 100% and `python tasks.py test` passes.
