"""`python tasks.py start`: take a fresh project as far as VSI can, in one command.

Steps: packages -> data + official code -> official packages -> tests -> first run -> charts
       -> requirement ticks -> report -> progress + next step.
Every step reports ✅ done, ⏭ skipped (with the reason) or ⚠️ problem, and never stops the others.
"""

from __future__ import annotations

import contextlib
import importlib
import importlib.util
import io
import os
import subprocess
import sys
from pathlib import Path

from . import data, progress, report

OK, SKIP, WARN = "✅", "⏭ ", "⚠️ "


def _say(icon: str, label: str, detail: str = "") -> None:
    print(f"{icon} {label:<31} {detail}")


def _in_venv() -> bool:
    return sys.prefix != sys.base_prefix


def venv_python(root: Path) -> Path:
    return root / ".venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def _pip_install(args: list[str]) -> int:
    if os.environ.get("VSI_SIMULATE_BLOCKED_PIP") and not _in_venv():   # tests: behave like Ubuntu / Homebrew
        return 1
    return subprocess.call([sys.executable, "-m", "pip", "install", "-q", *args])


def _packages(root: Path) -> Path | None:
    """Install pytest + matplotlib. If the system Python refuses installs (PEP 668: Ubuntu, Debian, Homebrew
    macOS, ...), create .venv in the project and return its Python, so start can continue inside it."""
    missing = [m for m in ("pytest", "matplotlib") if importlib.util.find_spec(m) is None]
    if not missing:
        _say(OK, "Packages / Paketat", "pytest, matplotlib")
        return None
    if _pip_install(["-r", str(root / "requirements.txt")]) == 0:
        importlib.invalidate_caches()
        _say(OK, "Packages / Paketat", "installed")
        return None
    if _in_venv():
        _say(WARN, "Packages / Paketat", "pip install failed — check your internet, then `python tasks.py setup`")
        return None
    py = venv_python(root)
    if not py.exists() and subprocess.call([sys.executable, "-m", "venv", str(root / ".venv")]) != 0:
        _say(WARN, "Packages / Paketat", "this Python blocks installs and cannot create .venv "
             "(Ubuntu/Debian: `sudo apt install python3-venv`, then run start again)")
        return None
    _say(OK, "Packages / Paketat", "your system Python blocks installs -> created .venv, continuing inside it")
    return py


def _data(root: Path, man: dict) -> None:
    if man.get("data") or man.get("udp"):
        try:
            files = data.download(root)
            n_code = sum(1 for f in files if f.parent.name == "official")
            detail = f"{len(files) - n_code} data file(s) in data/" + (f" + {n_code} official evaluation file(s) in official/" if n_code else "")
            _say(OK, "Data / Të dhënat", detail)
        except Exception as exc:  # network problems must not stop the rest
            hint = "" if isinstance(exc, data.DownloadError) else "; retry with `python tasks.py data`"
            _say(WARN, "Data / Të dhënat", f"{exc}{hint}")
    elif man.get("kind") == "esa":
        _say(SKIP, "Data / Të dhënat", "nothing to download for this challenge")
    elif "data" in progress.facts(root):
        _say(OK, "Data / Të dhënat", "instance generator works (src/generator.py)")
    else:
        _say(WARN, "Data / Të dhënat", "src/generator.py does not produce an instance yet")


def _tests(root: Path) -> None:
    if importlib.util.find_spec("pytest") is None:
        _say(SKIP, "Tests / Testet", "pytest not installed")
        return
    res = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=root, capture_output=True, text=True)
    last = (res.stdout.strip().splitlines() or ["no output"])[-1]
    _say(OK if res.returncode == 0 else WARN, "Tests / Testet", last)


HEAVY = {"torch", "torchvision"}   # gigabytes: never installed automatically, only suggested


def _official_packages(root: Path) -> None:
    """Install what the official ESA code imports (binary wheels only, one by one, so one failure blocks nothing)."""
    missing = data.missing_packages(root)
    if not missing:
        if data.manifest(root).get("requires"):
            _say(OK, "Official packages / Paketat ESA", "all installed")
        return
    for req in missing:
        if data.module_name(req) not in HEAVY:
            subprocess.call([sys.executable, "-m", "pip", "install", "-q", "--only-binary=:all:", req],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    importlib.invalidate_caches()
    still = data.missing_packages(root)
    if not still:
        _say(OK, "Official packages / Paketat ESA", "installed: " + ", ".join(missing))
    else:
        _say(SKIP, "Official packages / Paketat ESA",
             "still missing: " + ", ".join(still) + " — see requirements-official.txt "
             "(pykep/pygmo/heyoka: conda + Python 3.11; your agent can set it up)")


def _first_run(root: Path, man: dict) -> None:
    label = "First run / Ekzekutimi i parë"
    out = io.StringIO()
    try:
        if man.get("kind") == "esa":
            missing_code = [p for p in data.missing(root) if p.parent.name == "official"]
            if missing_code:
                _say(SKIP, label, "official evaluation code not downloaded: run `python tasks.py data`")
                return
            with contextlib.redirect_stdout(out):
                importlib.import_module("run").main(["--budget", "2"])
            skipped = [l.split(":")[0].replace("skipping ", "") for l in out.getvalue().splitlines()
                       if l.startswith("skipping ")]
            ran = len(man.get("problem_ids", [])) - len(skipped)
            _say(OK, label, f"random-search baseline with the OFFICIAL fitness on {ran} problem(s)"
                 + (f" (skipped: {', '.join(skipped)} — missing packages)" if skipped else ""))
        else:
            gen = importlib.import_module("generator")
            with contextlib.redirect_stdout(out):
                importlib.import_module("run").main(["--sizes", next(iter(gen.SIZES))])
            _say(OK, label,
                 "pipeline works (src/algorithms.py `baseline` is still a placeholder — your first algorithm goes there)")
    except SystemExit as exc:
        _say(SKIP if man.get("kind") == "esa" else WARN, label, str(exc))
    except Exception as exc:
        _say(WARN, label, f"{type(exc).__name__}: {exc}")


def _charts(root: Path) -> None:
    if not (root / "results" / "metrics.csv").exists():
        _say(SKIP, "Charts / Grafikët", "no results yet")
        return
    try:
        from . import plots
        with contextlib.redirect_stdout(io.StringIO()):
            plots.main()
        n = len(list((root / "results").glob("*.png")))
        _say(OK, "Charts / Grafikët", f"{n} chart(s) -> docs/figures/")
    except Exception as exc:
        _say(WARN, "Charts / Grafikët", f"{type(exc).__name__}: {exc}")


def _pictures(root: Path) -> None:
    label = "Diagrams / Diagramet"
    try:
        from . import visualize
        with contextlib.redirect_stdout(io.StringIO()):
            pictures = visualize.main(root)
        n = len(list((root / "docs" / "diagrams").glob("*.png")))
        _say(OK, label, f"{n} picture(s) in docs/diagrams/ + docs/DIAGRAMS.md"
             + (f" (incl. {len(pictures)} of the instance)" if pictures else ""))
    except Exception as exc:
        _say(WARN, label, f"{type(exc).__name__}: {exc}")


def main(root: str | Path = ".") -> int:
    root = Path(root).resolve()
    man = data.manifest(root)
    print(f"\nVSI start — {man.get('title', root.name)}\n")
    venv_py = _packages(root)
    if venv_py:   # continue the whole start inside the new .venv
        sys.stdout.flush()
        code = subprocess.call([str(venv_py), str(root / "tasks.py"), "start"], cwd=root)
        activate = r".venv\Scripts\activate" if sys.platform == "win32" else "source .venv/bin/activate"
        print()
        print(f"From now on run `{activate}` once per terminal before `python tasks.py ...` "
              "(your AI agent can do it for you).")
        return code
    _data(root, man)
    _official_packages(root)
    _tests(root)
    _first_run(root, man)
    _charts(root)
    _pictures(root)

    req = root / "docs" / "REQUIREMENTS.md"
    if req.exists():
        ticked = progress.auto_tick(req, progress.facts(root))
        _say(OK, "Requirements / Kërkesat", f"{len(ticked)} ticked automatically" if ticked else "nothing new to tick")
    written = report.update(root)
    _say(OK, "Report / Raporti", f"{written.relative_to(root)} (status + results)")

    if req.exists():
        done, total, nxt = progress.summary(req)
        print(f"\nProgress / Progresi: {progress.bar(done, total)}")
        if nxt:
            print(f"Next step / Hapi i radhës: {nxt}")
            print(f'Tell your agent / Thuaji agjentit: "Do the next step: {nxt}. Explain it to me simply."')
    return 0
