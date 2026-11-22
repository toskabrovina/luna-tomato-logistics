"""Download a project's official data files and evaluation code (listed in vsi.json, written by `vsi new`).

data files                                        -> data/<same layout as the official server>
evaluation code (ESA "UDP", one file per problem) -> official/<problem id>.py
"""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
import time
import urllib.request
from pathlib import Path


def manifest(root: str | Path = ".") -> dict:
    """The project's vsi.json (slug, kind, challenge/problem ids, data files)."""
    path = Path(root) / "vsi.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def local_path(entry: dict | str, root: str | Path = ".") -> Path:
    """Where a data file goes: data/<path after '/data/' in the URL>, mirroring the official folder layout."""
    if isinstance(entry, str):
        entry = {"url": entry}
    if entry.get("file"):
        rel = entry["file"]
    else:
        url = entry["url"]
        rel = url.split("/data/", 1)[1] if "/data/" in url else url.rstrip("/").rsplit("/", 1)[-1]
    return Path(root) / "data" / rel


def udp_path(problem_id: str, root: str | Path = ".") -> Path:
    """Where the official evaluation code of one problem goes."""
    return Path(root) / "official" / f"{problem_id}.py"


def _targets(root: str | Path) -> list[tuple[str, Path]]:
    man = manifest(root)
    files = [(e if isinstance(e, str) else e["url"], local_path(e, root)) for e in man.get("data", [])]
    files += [(url, udp_path(pid, root)) for pid, url in man.get("udp", {}).items()]
    return files


def missing(root: str | Path = ".") -> list[Path]:
    return [dest for _, dest in _targets(root) if not dest.exists()]


def module_name(requirement: str) -> str:
    """'heyoka==3.2.0' -> 'heyoka', 'pillow' -> 'PIL' (the name to import)."""
    name = re.split(r"[<>=!~ ]", requirement, maxsplit=1)[0].strip()
    return {"pillow": "PIL"}.get(name.lower(), name)


def missing_packages(root: str | Path = ".") -> list[str]:
    """Requirements of the official evaluation code that cannot be imported yet."""
    return [r for r in manifest(root).get("requires", []) if importlib.util.find_spec(module_name(r)) is None]


class DownloadError(RuntimeError):
    """Some files could not be downloaded (the others were). Running the command again retries only those."""


def _fetch(url: str, dest: Path, timeout: float, attempts: int) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response, tmp.open("wb") as out:
                shutil.copyfileobj(response, out)
            tmp.replace(dest)
            return
        except OSError:                       # timeouts, dropped connections, HTTP errors
            tmp.unlink(missing_ok=True)
            if attempt == attempts:
                raise
            time.sleep(2 * attempt)


def download(root: str | Path = ".", timeout: float = 120, attempts: int = 3) -> list[Path]:
    """Download every data / evaluation-code file that is not there yet (with retries).

    Returns the files present afterwards. If some files still fail, the others are kept and DownloadError
    lists the failed ones (run again to retry just those)."""
    present, failed = [], []
    for url, dest in _targets(root):
        if not dest.exists():
            print(f"downloading {url}")
            try:
                _fetch(url, dest, timeout, attempts)
            except OSError as exc:
                failed.append(f"{dest.name} ({type(exc).__name__})")
                continue
        present.append(dest)
    if failed:
        raise DownloadError(f"{len(present)} file(s) ok, {len(failed)} failed: {', '.join(failed)} "
                            "- the ESA server may be slow; run `python tasks.py data` again")
    return present
