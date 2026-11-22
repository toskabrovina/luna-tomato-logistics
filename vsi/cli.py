"""VSI command line.  (No install? Use `python -m vsi ...` instead of `vsi ...`.)

    vsi list                          all projects in the catalog
    vsi find <words>                  find a project by name (e.g. "torso", "dna assembly")
    vsi show <slug>                   details + source links
    vsi new <slug> [dir] [--force]    scaffold a ready project (use --force inside an existing repo)
    vsi agents <slug> [dir]           (re)write instruction files for Codex/Copilot/Gemini/Claude/Cursor
    vsi context [dir]                 CONTEXT.md bundle for ChatGPT / Copilot 365 / Gemini web
    vsi check [dir]                   requirements progress
    vsi chat [dir]                    chat packs (one file per project) for ChatGPT / Gemini / Claude web & app
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import catalog
from .check import check as run_check
from .context import write_context


def _line(p: dict) -> str:
    flag = "" if p.get("verified") else "  (spec not verified yet)"
    return f"  {p['slug']:<40} {p['kind']:<7} {p['title']}{flag}"


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):  # progress bars / ✅ on Windows terminals and agent logs
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    parser = argparse.ArgumentParser(prog="vsi", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    f = sub.add_parser("find"); f.add_argument("words", nargs="+")
    s = sub.add_parser("show"); s.add_argument("slug")
    n = sub.add_parser("new"); n.add_argument("slug"); n.add_argument("dir", nargs="?")
    n.add_argument("--force", action="store_true", help="write into a non-empty folder (existing repo)")
    a = sub.add_parser("agents"); a.add_argument("slug"); a.add_argument("dir", nargs="?", default=".")
    c = sub.add_parser("context"); c.add_argument("dir", nargs="?", default=".")
    k = sub.add_parser("check"); k.add_argument("dir", nargs="?", default=".")
    ch = sub.add_parser("chat"); ch.add_argument("dir", nargs="?", default=str(catalog.PKG.parent / "chat"))
    args = parser.parse_args(argv)

    if args.cmd == "list":
        for p in catalog.load():
            print(_line(p))
    elif args.cmd == "find":
        hits = catalog.find(" ".join(args.words))
        if not hits:
            print("No match. Try `vsi list`.")
            return 1
        for _, p in hits[:5]:
            print(_line(p))
    elif args.cmd == "show":
        p = catalog.get(args.slug)
        print(f"{p['title']}  [{p['slug']}]\n  kind: {p['kind']}  series: {p.get('series')}\n"
              f"  source: {p.get('source')}\n  official repo: {p.get('official_repo')}\n"
              f"  verified spec: {p.get('verified')}\n  {p['summary']}")
    elif args.cmd == "new":
        p = catalog.get(args.slug)
        target = catalog.scaffold(p["slug"], args.dir or p["slug"], force=args.force)
        print(f"Created {p['title']} in {target.resolve()}\nNext:\n  cd {target}\n"
              f"  {'python' if os.name == 'nt' else 'python3'} tasks.py start\n"
              "Then open the folder in VS Code and let your AI agent read AGENTS.md.")
    elif args.cmd == "agents":
        for path in catalog.write_agent_files(Path(args.dir), catalog.get(args.slug)):
            print(path)
    elif args.cmd == "context":
        print(write_context(args.dir))
    elif args.cmd == "chat":
        from .chatpack import write_all
        print(f"{len(write_all(args.dir))} chat packs in {args.dir}")
    elif args.cmd == "check":
        return 1 if run_check(Path(args.dir) / "docs" / "REQUIREMENTS.md") else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
