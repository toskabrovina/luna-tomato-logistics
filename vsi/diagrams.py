"""Diagrams from ONE description -> Mermaid text (GitHub + AI agents read it) and a PNG (for the report).

    d = Diagram("Greedy", [Node("s", "Start", "round"), Node("c", "Pick best", "box")], [("s", "c", "")])
    d.mermaid()      # ```mermaid flowchart TD ...```
    d.png("x.png")   # matplotlib only, no extra install

Shapes: box (step), round (start / end), diamond (decision), data (input / output / file).
Layout: top-down layers by longest path; edges that go back up (loops) are drawn as curves on the right.
"""

from __future__ import annotations

import textwrap
from dataclasses import dataclass, field
from pathlib import Path

STYLE = {  # fill, border
    "box": ("#e8f0fe", "#3b6fd8"),
    "round": ("#e6f6ec", "#2e8b57"),
    "diamond": ("#fff4e5", "#e08a00"),
    "data": ("#f3e8fd", "#7b3fc4"),
}
WRAP = 28


@dataclass
class Node:
    id: str
    label: str
    shape: str = "box"


@dataclass
class Diagram:
    title: str
    nodes: list[Node]
    edges: list[tuple[str, str, str]] = field(default_factory=list)   # (from, to, label)

    # ------------------------------------------------------------------ Mermaid
    def mermaid(self) -> str:
        def label(text: str) -> str:
            return text.replace('"', "#quot;").replace("\n", "<br/>")
        open_close = {"box": ('["', '"]'), "round": ('(["', '"])'), "diamond": ('{"', '"}'), "data": ('[("', '")]')}
        lines = ["```mermaid", "flowchart TD"]
        for n in self.nodes:
            a, b = open_close[n.shape]
            lines.append(f"    {n.id}{a}{label(n.label)}{b}")
        for u, v, text in self.edges:
            lines.append(f"    {u} -->|{label(text)}| {v}" if text else f"    {u} --> {v}")
        for shape, (fill, stroke) in STYLE.items():
            ids = [n.id for n in self.nodes if n.shape == shape]
            if ids:
                lines.append(f"    classDef {shape} fill:{fill},stroke:{stroke},color:#111")
                lines.append(f"    class {','.join(ids)} {shape}")
        lines.append("```")
        return "\n".join(lines)

    # ------------------------------------------------------------------ layout
    def _layout(self):
        ids = [n.id for n in self.nodes]
        out = {i: [] for i in ids}
        for u, v, _ in self.edges:
            out[u].append(v)
        back, state = set(), {}

        def dfs(u):                       # edges into the current DFS path are loops ("back edges")
            state[u] = 1
            for v in out[u]:
                if state.get(v) == 1:
                    back.add((u, v))
                elif v not in state:
                    dfs(v)
            state[u] = 2
        for i in ids:
            if i not in state:
                dfs(i)
        rank = {i: 0 for i in ids}
        for _ in ids:                     # longest path on the forward edges
            for u, v, _ in self.edges:
                if (u, v) not in back:
                    rank[v] = max(rank[v], rank[u] + 1)
        return rank, back

    # ------------------------------------------------------------------ PNG
    def png(self, path: str | Path) -> Path:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.patches import FancyBboxPatch, Polygon

        rank, back = self._layout()
        text = {n.id: "\n".join(line for part in n.label.split("\n") for line in (textwrap.wrap(part, WRAP, break_long_words=False) or [""]))
                for n in self.nodes}
        size = {}
        for n in self.nodes:
            lines = text[n.id].split("\n")
            w = max(len(l) for l in lines) * 0.12 + 0.5
            h = len(lines) * 0.32 + 0.3
            if n.shape == "diamond":
                w, h = w * 1.35, h * 1.5
            size[n.id] = (w, h)
        layers: dict[int, list[str]] = {}
        for n in self.nodes:
            layers.setdefault(rank[n.id], []).append(n.id)
        pos, row_y, top, bottom = {}, 0.0, {}, {}
        for r in sorted(layers):
            row = layers[r]
            row_h = max(size[i][1] for i in row)
            total = sum(size[i][0] for i in row) + 0.6 * (len(row) - 1)
            x = -total / 2
            for i in row:
                pos[i] = (x + size[i][0] / 2, row_y - row_h / 2)
                x += size[i][0] + 0.6
            top[r], bottom[r] = row_y, row_y - row_h
            row_y -= row_h + 0.9
        xs = [pos[i][0] + s * size[i][0] / 2 for i in pos for s in (-1, 1)]
        shape = {n.id: n.shape for n in self.nodes}
        right = [(u, v, l) for u, v, l in self.edges if (u, v) in back or rank[v] <= rank[u]]
        left = [(u, v, l) for u, v, l in self.edges if (u, v, l) not in right and rank[v] - rank[u] > 1]
        lane_r = {e: max(xs) + 0.5 + 0.45 * k for k, e in enumerate(right)}
        lane_l = {e: min(xs) - 0.5 - 0.45 * k for k, e in enumerate(left)}
        x_lo = min([min(xs)] + list(lane_l.values())) - 0.6
        x_hi = max([max(xs)] + list(lane_r.values())) + 0.6
        width, height = x_hi - x_lo, -row_y + 0.6

        fig, ax = plt.subplots(figsize=(max(5.0, width * 0.95), max(3.0, height * 0.95)))
        ax.set_xlim(x_lo, x_hi)
        ax.set_ylim(row_y + 0.3, 0.5)
        ax.axis("off")
        ax.set_title(self.title, fontsize=12, fontweight="bold")
        for n in self.nodes:
            (x, y), (w, h) = pos[n.id], size[n.id]
            fill, stroke = STYLE[n.shape]
            if n.shape == "diamond":
                ax.add_patch(Polygon([(x, y + h / 2), (x + w / 2, y), (x, y - h / 2), (x - w / 2, y)],
                                     closed=True, facecolor=fill, edgecolor=stroke, linewidth=1.5))
            else:
                style = {"box": "round,pad=0.02,rounding_size=0.06", "round": "round,pad=0.02,rounding_size=0.3",
                         "data": "square,pad=0.02"}[n.shape]
                ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle=style,
                                            facecolor=fill, edgecolor=stroke, linewidth=1.5))
            ax.text(x, y, text[n.id], ha="center", va="center", fontsize=9)
        def edge_y(i: str, dx: float, side: int) -> float:
            """y of node i's top (side=+1) or bottom (side=-1) border at horizontal offset dx from its centre."""
            (x, y), (w, h) = pos[i], size[i]
            if shape[i] == "diamond":
                return y + side * h / 2 * (1 - 2 * abs(dx) / w)
            return y + side * h / 2

        def label_at(x: float, y: float, text: str) -> None:
            if text:
                ax.text(x, y, text, fontsize=8, ha="center", va="center", color="#333",
                        bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none"))

        arrow = dict(arrowstyle="-|>", color="#444", lw=1.2, shrinkA=0, shrinkB=2)
        for u, v, label in self.edges:
            (x1, y1), (w1, h1) = pos[u], size[u]
            (x2, y2), (w2, h2) = pos[v], size[v]
            e = (u, v, label)
            if e in lane_r or e in lane_l:
                # right-angle route through the empty gaps between rows and a free lane at the side:
                # leave from the bottom, run along the lane, enter the target from the top
                sgn = 1 if e in lane_r else -1
                side = lane_r if e in lane_r else lane_l
                lane = side[e]
                k = list(side).index(e)                       # own height in the gap -> no overlapping lines
                j_out = [x for x in side if x[0] == u].index(e)
                j_in = [x for x in side if x[1] == v].index(e)
                sx = x1 + sgn * w1 * (0.22 + 0.1 * j_out)
                tx = x2 + sgn * w2 * (0.22 + 0.1 * j_in)
                gap_out = bottom[rank[u]] - 0.22 - 0.14 * (k % 4)
                gap_in = top[rank[v]] + 0.22 + 0.14 * (k % 4)
                pts = [(sx, edge_y(u, sx - x1, -1)), (sx, gap_out), (lane, gap_out), (lane, gap_in), (tx, gap_in)]
                ax.plot([p[0] for p in pts], [p[1] for p in pts], color="#444", lw=1.2)
                ax.annotate("", xy=(tx, edge_y(v, tx - x2, +1)), xytext=(tx, gap_in), arrowprops=arrow)
                label_at(lane, (gap_out + gap_in) / 2, label)
            else:
                start, end = (x1, y1 - h1 / 2), (x2, y2 + h2 / 2)
                ax.annotate("", xy=end, xytext=start, arrowprops=arrow)
                label_at((start[0] + end[0]) / 2, (start[1] + end[1]) / 2, label)
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.tight_layout()
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return path
