"""Grid worlds for multi-robot coordination.

make_instance(size) -> dict with:
    grid        2D list, 0 = free, 1 = static obstacle
    robots      list of start cells
    tasks       list of {pickup, dropoff, priority, release_time}
    movers      moving obstacles: {start, direction} (bounce off walls), use `step_movers`
"""

from __future__ import annotations

import random

# grid side, robots, tasks, moving obstacles
SIZES = {"small": (10, 2, 4, 2), "medium": (25, 5, 15, 6), "large": (50, 10, 40, 15), "huge": (100, 25, 120, 40)}
DIRS = [(0, 1), (1, 0), (0, -1), (-1, 0)]


def make_instance(size: str, seed: int = 0, obstacle_density: float = 0.15) -> dict:
    rng = random.Random(seed)
    side, n_robots, n_tasks, n_movers = SIZES[size]
    grid = [[1 if rng.random() < obstacle_density else 0 for _ in range(side)] for _ in range(side)]
    free = [(r, c) for r in range(side) for c in range(side) if grid[r][c] == 0]
    rng.shuffle(free)
    robots = free[:n_robots]
    cells = free[n_robots:]
    tasks = [{"pickup": rng.choice(cells), "dropoff": rng.choice(cells), "priority": rng.randint(1, 5),
              "release_time": rng.randint(0, side * 2)} for _ in range(n_tasks)]
    movers = [{"start": rng.choice(cells), "direction": rng.choice(DIRS)} for _ in range(n_movers)]
    return {"grid": grid, "robots": robots, "tasks": tasks, "movers": movers}


def step_movers(grid, positions, directions):
    """Advance moving obstacles one step; they reverse direction at walls / static obstacles."""
    side = len(grid)
    new_pos, new_dir = [], []
    for (r, c), (dr, dc) in zip(positions, directions):
        nr, nc = r + dr, c + dc
        if not (0 <= nr < side and 0 <= nc < side) or grid[nr][nc]:
            dr, dc = -dr, -dc
            nr, nc = r + dr, c + dc
            if not (0 <= nr < side and 0 <= nc < side) or grid[nr][nc]:
                nr, nc = r, c
        new_pos.append((nr, nc))
        new_dir.append((dr, dc))
    return new_pos, new_dir
