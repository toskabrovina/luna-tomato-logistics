"""Ready-made diagrams: project pipeline, problem model (one per project), classic algorithm templates.

`write_docs(target, project)` writes docs/DIAGRAMS.md (Mermaid: GitHub shows it, AI agents read it) and
docs/diagrams/*.png (for the report). Students adapt the algorithm templates to their own algorithms.
"""

from __future__ import annotations

from pathlib import Path

from .diagrams import Diagram, Node as N


def _chain(*ids: str) -> list[tuple[str, str, str]]:
    return [(a, b, "") for a, b in zip(ids, ids[1:])]


# --------------------------------------------------------------------------- algorithm templates
ALGORITHMS = {
    "greedy": Diagram("Greedy (template)", [
        N("s", "Start: empty solution", "round"),
        N("c", "Candidates that keep\nthe solution valid"),
        N("q", "Any candidate left?", "diamond"),
        N("p", "Pick the best by the\ngreedy rule\nmeter.count()"),
        N("a", "Add it to the solution"),
        N("r", "Return solution", "round")],
        _chain("s", "c", "q") + [("q", "p", "yes"), ("p", "a", ""), ("a", "c", "update"), ("q", "r", "no")]),
    "local_search": Diagram("Local search (template)", [
        N("s", "Start: initial solution\n(greedy or random)", "round"),
        N("n", "Neighbour of current\n(swap / move / 2-opt)"),
        N("e", "Evaluate it\nmeter.count()"),
        N("b", "Better than current?", "diamond"),
        N("a", "current = neighbour\nmeter.record(best)"),
        N("t", "Time / iterations left?", "diamond"),
        N("r", "Return best", "round")],
        _chain("s", "n", "e", "b") + [("b", "a", "yes"), ("b", "t", "no"), ("a", "t", ""),
                                      ("t", "n", "yes"), ("t", "r", "no")]),
    "simulated_annealing": Diagram("Simulated annealing (template)", [
        N("s", "Start: solution x,\ntemperature T = T0", "round"),
        N("n", "Random neighbour y\nmeter.count()"),
        N("d", "Δ = cost(y) − cost(x)"),
        N("b", "Δ < 0 or\nrandom < exp(−Δ/T)?", "diamond"),
        N("a", "x = y; keep best\nmeter.record(best)"),
        N("c", "Cool down: T = α·T"),
        N("t", "Stop? (T small / time)", "diamond"),
        N("r", "Return best", "round")],
        _chain("s", "n", "d", "b") + [("b", "a", "accept"), ("b", "c", "reject"), ("a", "c", ""),
                                      ("c", "t", ""), ("t", "n", "no"), ("t", "r", "yes")]),
    "genetic": Diagram("Genetic algorithm (template)", [
        N("s", "Start: random population", "round"),
        N("e", "Evaluate fitness\nmeter.count() per individual"),
        N("t", "Generations / time left?", "diamond"),
        N("l", "Select parents\n(tournament / roulette)"),
        N("x", "Crossover + mutation\n(keep solutions valid)"),
        N("p", "New population\n(+ elitism)"),
        N("r", "Return best individual", "round")],
        _chain("s", "e", "t") + [("t", "l", "yes"), ("l", "x", ""), ("x", "p", ""), ("p", "e", ""),
                                 ("t", "r", "no")]),
    "branch_and_bound": Diagram("Branch & bound (template)", [
        N("s", "Start: root node,\nbest = ∞ (or greedy)", "round"),
        N("q", "Open nodes left?", "diamond"),
        N("t", "Take node (best-first\nor depth-first)"),
        N("b", "Bound ≥ best?", "diamond"),
        N("p", "Prune it\nmeter.prune()"),
        N("c", "Complete solution?", "diamond"),
        N("u", "Update best\nmeter.record(best)"),
        N("x", "Branch: add children\nmeter.count()"),
        N("r", "Return best (optimal)", "round")],
        [("s", "q", ""), ("q", "t", "yes"), ("q", "r", "no"), ("t", "b", ""), ("b", "p", "yes"),
         ("b", "c", "no"), ("c", "u", "yes"), ("c", "x", "no"), ("p", "q", ""), ("u", "q", ""), ("x", "q", "")]),
    "dijkstra_astar": Diagram("Dijkstra / A* (template)", [
        N("s", "dist[source] = 0\npush (0, source)", "round"),
        N("q", "Priority queue empty?", "diamond"),
        N("p", "Pop u with smallest\ndist (+ h(u) for A*)\nmeter.count()"),
        N("g", "u is the target?", "diamond"),
        N("r", "Rebuild path from\nparents", "round"),
        N("e", "For each edge u→v:\nrelax dist[v]"),
        N("f", "No path", "round")],
        [("s", "q", ""), ("q", "p", "no"), ("q", "f", "yes"), ("p", "g", ""), ("g", "r", "yes"),
         ("g", "e", "no"), ("e", "q", "")]),
}


# --------------------------------------------------------------------------- project pipeline
def pipeline(project: dict) -> Diagram:
    esa = project["kind"] == "esa"
    nodes = [
        N("d", "data/ + official/\n(downloaded from ESA)" if esa else "src/generator.py\ninstances small → large", "data"),
        N("a", "src/algorithms.py\nYOUR algorithms"),
        N("e", "official fitness\n(udp.fitness)" if esa else "score() / your evaluator\n(validity + cost)"),
        N("m", "tasks.py run\nMeter: time, memory, states"),
        N("c", "results/metrics.csv\nhistory.csv, fronts.json", "data"),
        N("p", "tasks.py plots\nscaling, convergence, Pareto"),
        N("r", "Report\nREADME / docs/REPORT.md", "round"),
    ]
    edges = _chain("d", "a", "e", "m", "c", "p", "r")
    if esa:
        nodes.append(N("s", "ESA submission JSON\nresults/submission_*.json", "data"))
        edges.append(("m", "s", ""))
    return Diagram(f"Project pipeline — {project['title']}", nodes, edges)


# --------------------------------------------------------------------------- problem models
MODELS = {
    "torso-decompositions": Diagram("Problem model — Torso Decompositions", [
        N("g", "Graph G (edge list)\nvertices 0…n−1", "data"),
        N("x", "Decision vector\npermutation p1…pn + t"),
        N("o", "Orient edges by the order"),
        N("f", "Fill-in: connect the\nout-neighbours of each vertex"),
        N("t", "Torso = last n − t vertices"),
        N("w", "size = n − t (maximise)\nwidth = max out-degree (minimise)"),
        N("h", "Up to 20 vectors\nscored by hypervolume", "round")],
        _chain("g", "x", "o", "f", "t", "w", "h")),
    "interferometric-mission": Diagram("Problem model — Interferometric Mission", [
        N("m", "Mothership orbit\n(DRO or halo)", "data"),
        N("x", "x = relative position +\nvelocity of N satellites"),
        N("p", "Propagate orbits:\nt = 0, 1, 2 periods"),
        N("g", "Project on XY, XZ, YZ\nand snap to a grid"),
        N("b", "Count unique baselines\n→ fill factors"),
        N("f", "f = −max over times of\nsum of fill factors", "round")],
        _chain("m", "x", "p", "g", "b", "f")),
    "programmable-cubes": Diagram("Problem model — Programmable Cubes", [
        N("i", "Initial cube ensemble\n+ target shape", "data"),
        N("x", "x = [cube, move, cube,\nmove, …, −1]"),
        N("v", "Move legal?\n(connected, no collision)", "diamond"),
        N("a", "Apply pivot move"),
        N("c", "C(x) = cubes on correct\ntarget cells"),
        N("f", "Fitness: more correct\ncubes, fewer moves", "round")],
        [("i", "x", ""), ("x", "v", "next command"), ("v", "a", "yes"), ("v", "x", "skip"), ("a", "x", "next"),
         ("a", "c", "after −1"), ("c", "f", "")]),
    "luna-tomato-logistics": Diagram("Problem model — Luna Tomato Logistics (matching)", [
        N("t", "Transfers (e, l, d, weight)\nEarth orbit → Moon orbit → destination", "data"),
        N("x", "x = 0/1 per transfer"),
        N("v", "Every e, l, d used\nat most once?", "diamond"),
        N("w", "Fitness = total weight\n(maximise)", "round"),
        N("z", "Fitness = 0 (invalid)", "round")],
        _chain("t", "x", "v") + [("v", "w", "yes"), ("v", "z", "no")]),
    "luna-tomato-advertising": Diagram("Problem model — Luna Tomato Advertising", [
        N("m", "Target Morse signal\n\"Tomatoes for sale\"", "data"),
        N("o", "Orbit databases\nDRO · Lyapunov · Axial", "data"),
        N("x", "x = spacecraft per orbit\n(0…5) + their phases"),
        N("s", "Occultations →\nreconstructed signal"),
        N("e", "MSE ≤ 0.05?", "diamond"),
        N("f", "Feasible: fewer\nspacecraft is better", "round"),
        N("i", "Infeasible: lower\nMSE is better", "round")],
        [("m", "s", ""), ("o", "x", ""), ("x", "s", ""), ("s", "e", ""), ("e", "f", "yes"), ("e", "i", "no")]),
    "keplerian-tomato-tsp": Diagram("Problem model — Keplerian Tomato TSP", [
        N("i", "Tomato orbits around\nthe Moon (a, e, i, Ω, ω, ν)", "data"),
        N("x", "x = departure times +\ntimes of flight + visit order"),
        N("l", "Lambert transfer for\neach hop → ΔV"),
        N("v", "ΔV ≤ limit (or one of\nE exceptions)? times in order?", "diamond"),
        N("f", "Minimise mission time\nt(N−1) + tof(N−1)", "round"),
        N("z", "Infeasible", "round")],
        _chain("i", "x", "l", "v") + [("v", "f", "yes"), ("v", "z", "no")]),
    "morphing-rovers": Diagram("Problem model — Morphing Rovers", [
        N("d", "6 Mars height maps\n30 landing → sample scenarios", "data"),
        N("x", "x = 4 terrain masks +\nneural network weights"),
        N("s", "Simulate 500 steps:\nnetwork steers + switches mode"),
        N("v", "Speed = mask vs terrain"),
        N("f", "Score = time ratio ×\n(1 + remaining distance)\nmean over scenarios", "round")],
        _chain("d", "x", "s", "v", "f")),
    "quantum-communications-constellations": Diagram("Problem model — Quantum Constellations", [
        N("r", "100 candidate rover sites", "data"),
        N("x", "x = 2 Walker constellations\n(orbit, S, P, F, η) + 4 rovers"),
        N("g", "Time-varying link graph\nmotherships ↔ satellites ↔ rovers"),
        N("c", "Constraints: rovers ≥ 3000 km,\nsatellites ≥ 50 km", "diamond"),
        N("j", "J1 = avg shortest path cost\nJ2 = constellation cost"),
        N("h", "Pareto set\nscored by hypervolume", "round")],
        [("r", "x", ""), ("x", "g", ""), ("g", "c", ""), ("c", "j", "ok"), ("j", "h", "")]),
    "trappist-tour": Diagram("Problem model — Trappist Tour", [
        N("x", "x = entry leg + 6 legs\n(flyby, DSM, duration) + order"),
        N("p", "Order is a permutation\nof planets b…h?", "diamond"),
        N("t", "Propagate legs:\nLambert + flybys"),
        N("d", "Closest approach to the\nstar ≥ 834 840 km?", "diamond"),
        N("j", "Objectives: total ΔV,\nmission time"),
        N("h", "Pareto set (≤ 100)\nhypervolume ref [2500, 4000]", "round")],
        [("x", "p", ""), ("p", "t", "yes"), ("t", "d", ""), ("d", "j", "yes"), ("j", "h", "")]),
    "delivery-scheduling": Diagram("Problem model — Delivery Scheduling", [
        N("c", "candidates: asteroid →\nstation → opportunities", "data"),
        N("w", "x part 1: 12 station\nactivity windows"),
        N("a", "x part 2: 340 × (asteroid,\nstation, opportunity)"),
        N("v", "Windows disjoint, gap ≥ 1 day,\narrivals inside windows?", "diamond"),
        N("m", "Mass per station and\nmaterial A, B, C"),
        N("f", "Maximise the minimum\nmass M_min", "round")],
        [("c", "a", ""), ("w", "v", ""), ("a", "v", ""), ("v", "m", "yes"), ("m", "f", "")]),
    "mining": Diagram("Problem model — Mining the Belt", [
        N("c", "10 000 asteroids:\norbit, mass, material", "data"),
        N("x", "x = arrival times +\nstay times + asteroid order"),
        N("t", "Lambert transfer\nΔV from the tank"),
        N("p", "Propellant left?", "diamond"),
        N("s", "Stay: prepare material or\nrefuel (1/30 per day)"),
        N("f", "Maximise min(m0, m1, m2)\nwithin 1827 days", "round")],
        _chain("c", "x", "t", "p") + [("p", "s", "yes"), ("s", "t", "next asteroid"), ("p", "f", "no / end")]),
    "trigger-arc-tsp": Diagram("Problem model — Trigger Arc TSP", [
        N("g", "Directed graph with arc costs\n+ trigger rules", "data"),
        N("t", "Tour visiting every node"),
        N("r", "Traversing a trigger arc\nchanges other arc costs"),
        N("c", "Tour cost with\nall trigger effects"),
        N("f", "Minimise tour cost", "round")],
        _chain("g", "t", "r", "c", "f")),
    "dna-genome-reconstruction": Diagram("Problem model — DNA Genome Reconstruction", [
        N("r", "Noisy reads (errors,\nreverse complements)", "data"),
        N("k", "k-mer index →\ncandidate pairs"),
        N("o", "Approximate overlaps\n(edit distance)"),
        N("g", "Overlap graph\n(weights = overlap)"),
        N("a", "Assembly: path through\nthe graph → contigs"),
        N("c", "Consensus: error correction\n+ variant detection"),
        N("q", "Compare with the true genome:\naccuracy, edit distance", "round")],
        _chain("r", "k", "o", "g", "a", "c", "q")),
    "protein-structure-prediction": Diagram("Problem model — Protein Structure Prediction", [
        N("s", "Amino-acid sequence\n→ H/P string", "data"),
        N("f", "Fold = self-avoiding walk\non a 2D/3D lattice"),
        N("v", "Valid? (no two residues\non the same cell)", "diamond"),
        N("e", "Energy: −1 per non-consecutive\nH–H neighbour pair"),
        N("o", "Minimise energy\n(GA, SA, beam, B&B…)", "round")],
        _chain("s", "f", "v") + [("v", "e", "yes"), ("v", "f", "no: repair"), ("e", "o", "")]),
    "chronos-nexus": Diagram("Problem model — Chronos Nexus", [
        N("g", "Galaxy graph: planets,\nroutes, ships, missions", "data"),
        N("r", "Multi-objective routing\n(time, fuel, risk)"),
        N("a", "Resource allocation\n(min-cost flow)"),
        N("s", "Mission scheduling"),
        N("i", "Infrastructure under budget\n(knapsack)"),
        N("e", "Events: blocked routes,\npirates…", "diamond"),
        N("p", "Re-plan → stable,\nefficient civilisation", "round")],
        [("g", "r", ""), ("g", "a", ""), ("g", "s", ""), ("g", "i", ""), ("r", "e", ""), ("a", "e", ""),
         ("s", "e", ""), ("i", "e", ""), ("e", "p", "")]),
    "multi-robot-coordination": Diagram("Problem model — Multi-Robot Coordination", [
        N("w", "Grid: static + moving\nobstacles, robots, tasks", "data"),
        N("a", "Task allocation\n(auction by priority)"),
        N("p", "Path planning per robot\n(A* / RRT*)"),
        N("c", "Conflict / collision?", "diamond"),
        N("r", "Resolve by priority\nor re-plan"),
        N("m", "Move one time step\n(learned policy: MADQL / PPO)"),
        N("f", "All tasks done:\nmakespan, collisions, reward", "round")],
        _chain("w", "a", "p", "c") + [("c", "r", "yes"), ("r", "p", ""), ("c", "m", "no"),
                                      ("m", "a", "new tasks"), ("m", "f", "done")]),
    "time-travel-paradox": Diagram("Problem model — Time Travel Paradox", [
        N("e", "Events + causal edges\n+ time-travel edges", "data"),
        N("g", "Directed timeline graph"),
        N("c", "Cycle? (DFS / SCC)", "diamond"),
        N("p", "Paradox: events +\nresponsible edge"),
        N("r", "Repair: remove / modify /\ndelay with costs"),
        N("o", "Consistent timeline\nat minimum cost", "round")],
        _chain("e", "g", "c") + [("c", "p", "yes"), ("p", "r", ""), ("r", "g", "re-check"),
                                 ("c", "o", "no")]),
    "traffic-flow-optimization": Diagram("Problem model — Traffic Flow (Dijkstra & A*)", [
        N("g", "City grid: intersections,\nroads with delays", "data"),
        N("q", "Query: source → target"),
        N("d", "Dijkstra / A*\n(heuristic: free-flow time)"),
        N("r", "Fastest route +\ntravel time"),
        N("u", "Congestion update?", "diamond"),
        N("o", "Report route", "round")],
        _chain("g", "q", "d", "r", "u") + [("u", "d", "yes: new weights"), ("u", "o", "no")]),
}


# --------------------------------------------------------------------------- docs
MAKE_YOUR_OWN = '''## Make a diagram of YOUR algorithm

```python
from vsi.diagrams import Diagram, Node
d = Diagram("My greedy for <problem>", [
    Node("s", "Start", "round"),
    Node("p", "Pick the vertex with\\nthe smallest degree"),
    Node("q", "Vertices left?", "diamond"),
    Node("r", "Return order", "round")],
    [("s", "p", ""), ("p", "q", ""), ("q", "p", "yes"), ("q", "r", "no")])
print(d.mermaid())                       # paste into the README (GitHub draws it)
d.png("docs/diagrams/my_greedy.png")     # picture for the report
```
Shapes: `box` step · `round` start/end · `diamond` decision · `data` input/output.
'''


def all_diagrams(project: dict) -> dict[str, Diagram]:
    out = {"pipeline": pipeline(project)}
    if project["slug"] in MODELS:
        out["model"] = MODELS[project["slug"]]
    out.update({f"algorithm_{k}": v for k, v in ALGORITHMS.items()})
    return out


def write_docs(target: str | Path, project: dict, png: bool = True) -> Path:
    """docs/DIAGRAMS.md (Mermaid) + docs/diagrams/<name>.png."""
    docs = Path(target) / "docs"
    diagrams = all_diagrams(project)
    parts = [f"# Diagrams — {project['title']}\n",
             "Generated by VSI. GitHub shows the Mermaid blocks as pictures; AI agents read them as text.",
             "PNG versions for the report are in `docs/diagrams/` (`python tasks.py visualize` redraws them).",
             "The algorithm templates are generic: adapt them to **your** algorithm "
             "(rename steps, add your pruning / neighbourhood / greedy rule).\n"]
    for name, d in diagrams.items():
        parts += [f"## {d.title}\n", d.mermaid(), f"\n![{d.title}](diagrams/{name}.png)\n"]
    pictures = sorted((docs / "diagrams").glob("instance_*.png"))
    if pictures:
        parts.append("## Instance pictures\n")
        parts += [f"![{p.stem}](diagrams/{p.name})\n" for p in pictures]
    parts.append(MAKE_YOUR_OWN)
    path = docs / "DIAGRAMS.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts), encoding="utf-8")
    if png:
        for name, d in diagrams.items():
            d.png(docs / "diagrams" / f"{name}.png")
    return path
