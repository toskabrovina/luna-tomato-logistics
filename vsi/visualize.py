"""Pictures of the project's instances (`python tasks.py visualize`) -> docs/diagrams/instance_*.png.

Custom projects draw an instance from src/generator.py; ESA projects draw the downloaded official data.
Every picture is optional: a missing file or package just skips that picture.
"""

from __future__ import annotations

import importlib.util
import json
import math
import random
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from . import data


def _gen(root: Path):
    path = root / "src" / "generator.py"
    spec = importlib.util.spec_from_file_location(f"_vsi_vis_gen_{abs(hash(str(path)))}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _save(fig, out: Path, name: str) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"instance_{name}.png"
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def _lines(path: Path) -> list[list[str]]:
    return [l.split() for l in path.read_text(encoding="utf-8").splitlines() if l.strip() and l[0] not in "c#p"]


# --------------------------------------------------------------------------- custom projects
def traffic(root, out):
    g = _gen(root).make_instance("small", seed=0)
    fig, ax = plt.subplots(figsize=(6, 6))
    delays = list(g["edges"].values())
    lo, hi = min(delays), max(delays)
    cmap = plt.get_cmap("RdYlGn_r")
    for (u, v), d in g["edges"].items():
        if u < v:
            (r1, c1), (r2, c2) = g["pos"][u], g["pos"][v]
            ax.plot([c1, c2], [r1, r2], color=cmap((d - lo) / max(hi - lo, 1e-9)), lw=2.5)
    s, t = g["queries"][0]
    for node, color, text in ((s, "blue", "source"), (t, "black", "target")):
        r, c = g["pos"][node]
        ax.plot(c, r, "o", color=color, ms=12)
        ax.annotate(text, (c, r), textcoords="offset points", xytext=(8, 8))
    ax.set_title("City grid (small): road delay, green = fast, red = congested")
    ax.set_aspect("equal")
    ax.axis("off")
    return [_save(fig, out, "city_grid")]


def robots(root, out):
    g = _gen(root).make_instance("small", seed=0)
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.imshow(g["grid"], cmap="Greys", origin="upper")
    for i, (r, c) in enumerate(g["robots"]):
        ax.plot(c, r, "o", color="tab:blue", ms=12)
        ax.text(c, r, f"R{i}", color="white", ha="center", va="center", fontsize=7)
    for t in g["tasks"]:
        (pr, pc), (dr, dc) = t["pickup"], t["dropoff"]
        ax.plot(pc, pr, "^", color="tab:green", ms=9)
        ax.plot(dc, dr, "X", color="tab:red", ms=9)
        ax.annotate("", (dc, dr), (pc, pr), arrowprops=dict(arrowstyle="->", color="tab:green", alpha=0.5))
    for m in g["movers"]:
        r, c = m["start"]
        ax.plot(c, r, "s", color="tab:orange", ms=9)
    ax.set_title("Grid world (small)\nrobots (blue) · pickup ▲ → drop-off ✖ · moving obstacles (orange)")
    ax.set_xticks([]); ax.set_yticks([])
    return [_save(fig, out, "grid_world")]


def protein(root, out):
    gen = _gen(root)
    hp = gen.make_instance("small", seed=0)["hp"]
    width = max(3, int(math.sqrt(len(hp))) + 1)       # a simple valid "snake" fold, just to show the model
    moves, direction = [], "R"
    for i in range(1, len(hp)):
        if i % width == 0:
            moves.append("U")
            direction = "L" if direction == "R" else "R"
        else:
            moves.append(direction)
    coords = gen.coordinates("".join(moves))
    energy = gen.hp_energy(hp, coords)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot([c[0] for c in coords], [c[1] for c in coords], "-", color="grey", zorder=1)
    for (x, y), a in zip(coords, hp):
        ax.scatter(x, y, s=260, color="black" if a == "H" else "white", edgecolors="black", zorder=2)
    ax.set_title(f"HP model: {hp}\nexample snake fold, energy = {energy} (black = H, white = P)")
    ax.set_aspect("equal")
    ax.axis("off")
    return [_save(fig, out, "hp_fold")]


def timetravel(root, out):
    g = _gen(root).make_instance("small", seed=0)
    ts = {e["id"]: e["timestamp"] for e in g["events"]}
    lane = {e["id"]: (i % 3) for i, e in enumerate(g["events"])}
    fig, ax = plt.subplots(figsize=(9, 4))
    for u, v in g["dependencies"]:
        ax.annotate("", (ts[v], lane[v]), (ts[u], lane[u]), arrowprops=dict(arrowstyle="->", color="grey"))
    for u, v in g["time_travel"]:
        ax.annotate("", (ts[v], lane[v]), (ts[u], lane[u]),
                    arrowprops=dict(arrowstyle="->", color="red", lw=2, connectionstyle="arc3,rad=0.4"))
    for i, t in ts.items():
        ax.plot(t, lane[i], "o", color="tab:blue", ms=14)
        ax.text(t, lane[i], str(i), color="white", ha="center", va="center", fontsize=8)
    ax.set_title("Timeline (small): causal edges (grey) and time-travel edges back in time (red)")
    ax.set_xlabel("year"); ax.set_yticks([])
    return [_save(fig, out, "timeline")]


def chronos(root, out):
    g = _gen(root).make_instance("small", seed=0)
    p = g["planets"]
    fig, ax = plt.subplots(figsize=(7, 7))
    for r in g["routes"]:
        a, b = p[r["from"]], p[r["to"]]
        ax.plot([a["x"], b["x"]], [a["y"], b["y"]], color="grey", lw=0.6, alpha=0.6)
    sc = ax.scatter([q["x"] for q in p], [q["y"] for q in p], s=[q["population"] / 8000 + 10 for q in p],
                    c=[q["importance"] for q in p], cmap="viridis", edgecolors="black", zorder=2)
    fig.colorbar(sc, ax=ax, label="importance")
    ax.set_title("Galaxy (small): planets (size = population) and routes")
    ax.set_aspect("equal")
    return [_save(fig, out, "galaxy")]


def dna(root, out):
    g = _gen(root).make_instance("small", seed=0)
    length, read_len = len(g["genome"]), g["params"]["read_len"]
    cover = [0] * length
    for start, _ in g["truth"]:
        for i in range(start, min(length, start + read_len)):
            cover[i] += 1
    fig, ax = plt.subplots(figsize=(9, 3.5))
    ax.fill_between(range(length), cover, color="tab:blue", alpha=0.6)
    for pos, ref, alt in g["mutations"]:
        ax.axvline(pos, color="red", lw=1)
    ax.set_title(f"Reads coverage along the genome (small: {len(g['reads'])} reads); red = planted mutations")
    ax.set_xlabel("genome position"); ax.set_ylabel("coverage")
    return [_save(fig, out, "coverage")]


# --------------------------------------------------------------------------- ESA projects (official data)
def torso(root, out):
    outs = []
    for name in ("easy", "medium", "hard"):
        f = root / "data" / "spoc3" / "torso" / f"{name}.gr"
        if not f.exists():
            continue
        edges = [(int(a), int(b)) for a, b, *_ in _lines(f)]
        deg = Counter(x for e in edges for x in e)
        fig, axes = plt.subplots(1, 2 if name == "easy" else 1, figsize=(10 if name == "easy" else 6, 4.5))
        axes = axes if name == "easy" else [axes]
        axes[0].hist(list(deg.values()), bins=40, color="tab:blue")
        axes[0].set_yscale("log")
        axes[0].set_title(f"{name}.gr: {len(deg)} vertices, {len(edges)} edges — degree distribution")
        axes[0].set_xlabel("degree"); axes[0].set_ylabel("vertices (log)")
        if name == "easy":
            axes[1].scatter([a for a, b in edges] + [b for a, b in edges], [b for a, b in edges] + [a for a, b in edges],
                            s=0.3, color="black")
            axes[1].set_title("adjacency matrix (dot = edge)")
            axes[1].invert_yaxis(); axes[1].set_aspect("equal")
        outs.append(_save(fig, out, f"graph_{name}"))
    return outs


def logistics(root, out):
    f = root / "data" / "spoc4" / "ltl" / "random_harder_5000.txt"
    if not f.exists():
        return []
    rows = [(int(a), int(b), int(c), float(w)) for a, b, c, w in (r[:4] for r in _lines(f) if len(r) == 4)]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].hist([r[3] for r in rows], bins=50, color="tab:green")
    axes[0].set_title(f"matching-i: {len(rows)} transfers — weight distribution")
    axes[0].set_xlabel("tomatoes (weight)")
    # a small piece of the 3-part structure: Earth orbit -> Moon orbit -> destination (one line = one transfer)
    sample = [r for r in rows if r[0] <= min(r[0] for r in rows) + 7][:40]
    cols = [sorted({r[k] for r in sample}) for k in range(3)]
    y = [{v: i / max(len(c) - 1, 1) for i, v in enumerate(c)} for c in cols]
    cmap = plt.get_cmap("viridis")
    w_max = max(r[3] for r in sample)
    for e, l, d, w in sample:
        axes[1].plot([0, 1, 2], [y[0][e], y[1][l], y[2][d]], color=cmap(w / w_max), alpha=0.8, lw=1.2)
    for k, name in enumerate(("Earth orbit e", "Moon orbit l", "destination d")):
        axes[1].scatter([k] * len(cols[k]), [y[k][v] for v in cols[k]], color="black", s=18, zorder=3)
        axes[1].text(k, 1.06, name, ha="center", fontsize=9)
    counts = Counter(r[0] for r in rows)
    axes[1].set_title(f"a piece of the 3D matching (colour = weight); each node in ~{max(counts.values())} transfers",
                      fontsize=9, pad=18)
    axes[1].axis("off")
    return [_save(fig, out, "transfers")]


def kttsp(root, out):
    fig, ax = plt.subplots(figsize=(7, 5))
    found = False
    for name, marker in (("easy", "o"), ("medium", "s"), ("hard", "^")):
        f = root / "data" / "spoc4" / "kttsp" / "problems" / f"{name}.kttsp"
        if f.exists():
            rows = [list(map(float, r[:6])) for r in _lines(f) if len(r) >= 6]
            ax.scatter([r[0] / 1e6 for r in rows], [math.degrees(r[2]) for r in rows], marker=marker,
                       label=f"{name} ({len(rows)} tomatoes)", alpha=0.7)
            found = True
    if not found:
        plt.close(fig)
        return []
    ax.set_xlabel("semi-major axis a (1000 km)"); ax.set_ylabel("inclination (deg)")
    ax.set_title("Tomato orbits around the Moon"); ax.legend()
    return [_save(fig, out, "orbits")]


def delivery(root, out):
    f = root / "data" / "spoc" / "scheduling" / "candidates.txt"
    if not f.exists():
        return []
    db = json.loads(f.read_text(encoding="utf-8"))
    per_station, times = Counter(), []
    for stations in db.values():
        for st, opps in stations.items():
            per_station[int(st)] += 1
            times += [o[0] for o in opps]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].bar(sorted(per_station), [per_station[s] for s in sorted(per_station)], color="tab:purple")
    axes[0].set_title(f"{len(db)} asteroids: how many can reach each station")
    axes[0].set_xlabel("station")
    axes[1].hist(times, bins=40, color="tab:blue")
    axes[1].set_title("arrival times of all opportunities (80-day horizon)")
    axes[1].set_xlabel("day")
    return [_save(fig, out, "opportunities")]


def mining(root, out):
    f = root / "data" / "spoc" / "mining" / "candidates.txt"
    if not f.exists():
        return []
    rows = [list(map(float, r)) for r in _lines(f)]
    names = {0: "material 0", 1: "material 1", 2: "material 2", 3: "propellant"}
    fig, ax = plt.subplots(figsize=(7, 5))
    for m, name in names.items():
        sel = [r for r in rows if int(r[8]) == m]
        ax.scatter([r[1] / 1e9 for r in sel], [r[2] for r in sel], s=3, label=f"{name} ({len(sel)})", alpha=0.6)
    ax.set_xlabel("semi-major axis (10^9 m)"); ax.set_ylabel("eccentricity")
    ax.set_title(f"Asteroid belt: {len(rows)} asteroids by material"); ax.legend(markerscale=4)
    return [_save(fig, out, "belt")]


def quantum(root, out):
    f = root / "data" / "spoc2" / "constellations" / "rovers.txt"
    if not f.exists():
        return []
    rows = [list(map(float, r)) for r in _lines(f)]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.scatter([math.degrees(r[1]) for r in rows], [math.degrees(r[0]) for r in rows], color="tab:red")
    for i, r in enumerate(rows):
        ax.text(math.degrees(r[1]), math.degrees(r[0]), str(i), fontsize=6)
    ax.set_xlabel("longitude (deg)"); ax.set_ylabel("latitude (deg)")
    ax.set_title("100 candidate rover sites (pick 4, at least 3000 km apart)")
    return [_save(fig, out, "rover_sites")]


def morphing(root, out):
    base = root / "data" / "spoc2" / "morphing"
    if not (base / "coordinates.txt").exists() or not (base / "Maps" / "Map1.JPG").exists():
        return []
    img = plt.imread(base / "Maps" / "Map1.JPG")
    rows = [list(map(float, r)) for r in _lines(base / "coordinates.txt") if int(float(r[0])) == 0]
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.imshow(img, cmap="terrain")
    for _, lx, ly, ax_, ay in rows:
        ax.plot(lx, ly, "o", color="blue", ms=8)
        ax.plot(ax_, ay, "*", color="red", ms=12)
        ax.annotate("", (ax_, ay), (lx, ly), arrowprops=dict(arrowstyle="->", color="white"))
    ax.set_title("Map 1: landing sites (blue) → samples (red)")
    ax.axis("off")
    return [_save(fig, out, "map1")]


def cubes(root, out):
    import numpy as np
    base = root / "data" / "spoc3" / "cubes" / "data" / "ISS"
    if not (base / "Target_Config.npy").exists():
        return []
    pts, types = np.load(base / "Target_Config.npy"), np.load(base / "Target_Cube_Types.npy")
    fig = plt.figure(figsize=(7, 6))
    ax = fig.add_subplot(projection="3d")
    ax.scatter(pts[:, 0], pts[:, 1], pts[:, 2], c=types, cmap="tab10", s=40, depthshade=True)
    ax.set_title(f"Target: ISS ({len(pts)} cubes, colour = cube type)")
    return [_save(fig, out, "iss_target")]


VISUALS = {
    "traffic-flow-optimization": traffic, "multi-robot-coordination": robots,
    "protein-structure-prediction": protein, "time-travel-paradox": timetravel, "chronos-nexus": chronos,
    "dna-genome-reconstruction": dna, "torso-decompositions": torso, "luna-tomato-logistics": logistics,
    "keplerian-tomato-tsp": kttsp, "delivery-scheduling": delivery, "mining": mining,
    "quantum-communications-constellations": quantum, "morphing-rovers": morphing, "programmable-cubes": cubes,
}
NO_DATA_HINT = "No instance file to draw: the official code draws it — `udp.plot(udp.example())` in src/esa_problem.py."


def instance_pictures(root: str | Path = ".") -> list[Path]:
    root = Path(root)
    slug = data.manifest(root).get("slug")
    out = root / "docs" / "diagrams"
    for old in out.glob("instance_*.png"):
        old.unlink()
    fn = VISUALS.get(slug)
    return fn(root, out) if fn else []


def main(root: str | Path = ".") -> list[Path]:
    """Diagrams (docs/DIAGRAMS.md + PNGs) and instance pictures."""
    from . import catalog
    from .diagram_specs import write_docs
    root = Path(root)
    slug = data.manifest(root).get("slug")
    pictures = []
    try:
        pictures = instance_pictures(root)
    except Exception as exc:                     # a picture must never break the project
        print(f"instance picture skipped: {type(exc).__name__}: {exc}")
    if slug:
        write_docs(root, catalog.get(slug))
    if not pictures and slug and slug not in ("trigger-arc-tsp",):
        if catalog.get(slug)["kind"] == "esa":
            print(NO_DATA_HINT)
    return pictures
