"""Random galaxies at the sizes required by the brief.

make_instance(size) -> dict with planets, routes, ships, missions, facilities, events.
Routes connect each planet to its k nearest neighbours (plus a ring to keep the galaxy connected).
"""

from __future__ import annotations

import math
import random

RESOURCES = ["food", "water", "energy", "fuel", "medicine", "rare_minerals", "construction"]
FACILITIES = ["energy_plant", "farm", "hospital", "factory", "defense", "research", "spaceport", "mining"]
EVENT_TYPES = ["wormhole_collapse", "route_blocked", "pirates", "ship_destroyed", "medical_emergency",
               "production_drop", "new_colony", "population_boom", "resource_unavailable",
               "priority_mission", "route_danger", "ship_failure"]

# planets, routes (approx), missions
SIZES = {
    "small": (100, 500, 50),
    "medium": (1_000, 10_000, 500),
    "large": (10_000, 100_000, 5_000),
    "extreme": (100_000, 1_000_000, 50_000),
}


def make_instance(size: str, seed: int = 0) -> dict:
    rng = random.Random(seed)
    n_planets, n_routes, n_missions = SIZES[size]
    k = max(1, n_routes // n_planets)

    planets = []
    for i in range(n_planets):
        planets.append({
            "id": i, "x": rng.uniform(0, 1000), "y": rng.uniform(0, 1000),
            "population": rng.randint(1_000, 1_000_000),
            "production": {r: rng.uniform(0, 100) for r in RESOURCES},
            "consumption": {r: rng.uniform(0, 100) for r in RESOURCES},
            "storage": {r: rng.uniform(1_000, 20_000) for r in RESOURCES},
            "technology": rng.randint(1, 10), "defense": rng.randint(1, 10), "importance": rng.randint(1, 10),
        })

    # k nearest neighbours via a coarse grid (avoids O(n^2) for big galaxies)
    cell = 1000 / max(1, int(math.sqrt(n_planets / 4)))
    grid: dict[tuple[int, int], list[int]] = {}
    for p in planets:
        grid.setdefault((int(p["x"] // cell), int(p["y"] // cell)), []).append(p["id"])

    def neighbours(p):
        cx, cy = int(p["x"] // cell), int(p["y"] // cell)
        cand = [q for dx in (-1, 0, 1) for dy in (-1, 0, 1) for q in grid.get((cx + dx, cy + dy), []) if q != p["id"]]
        cand.sort(key=lambda q: (planets[q]["x"] - p["x"]) ** 2 + (planets[q]["y"] - p["y"]) ** 2)
        return cand[:k]

    edges = {(i, (i + 1) % n_planets) for i in range(n_planets)}  # ring: connected
    for p in planets:
        edges.update((p["id"], q) for q in neighbours(p))

    routes = []
    for u, v in edges:
        d = math.dist((planets[u]["x"], planets[u]["y"]), (planets[v]["x"], planets[v]["y"]))
        routes.append({"from": u, "to": v, "distance": d, "time": d / rng.uniform(5, 15), "fuel": d * rng.uniform(1, 2),
                       "risk": rng.uniform(0, 0.3), "capacity": rng.randint(100, 1000),
                       "reliability": rng.uniform(0.9, 1.0), "available": True,
                       "time_range": (d / 15, d / 5)})

    ships = [{"id": s, "location": rng.randrange(n_planets), "capacity": rng.randint(100, 1000),
              "fuel_capacity": rng.randint(1_000, 10_000), "speed": rng.uniform(5, 15), "fuel": None,
              "available_at": 0, "reliability": rng.uniform(0.85, 1.0), "cost": rng.uniform(1, 10)}
             for s in range(max(10, n_missions // 5))]
    for s in ships:
        s["fuel"] = s["fuel_capacity"]

    missions = [{"id": m, "origin": rng.randrange(n_planets), "destination": rng.randrange(n_planets),
                 "cargo": rng.choice(RESOURCES), "amount": rng.randint(10, 500),
                 "deadline": rng.randint(10, 500), "priority": rng.randint(1, 5), "importance": rng.randint(1, 10)}
                for m in range(n_missions)]

    facilities = [{"type": f, "planet": rng.randrange(n_planets), "cost": rng.randint(100, 5_000),
                   "value": rng.randint(1, 100), "build_time": rng.randint(1, 50)}
                  for f in rng.choices(FACILITIES, k=max(20, n_planets // 10))]

    events = sorted(({"time": rng.randint(1, 500), "type": rng.choice(EVENT_TYPES),
                      "target": rng.randrange(max(len(routes), n_planets)), "severity": rng.uniform(0, 1)}
                     for _ in range(max(10, n_missions // 10))), key=lambda e: e["time"])

    return {"planets": planets, "routes": routes, "ships": ships, "missions": missions,
            "facilities": facilities, "budget": sum(f["cost"] for f in facilities) // 4, "events": events}
