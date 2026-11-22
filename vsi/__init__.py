"""VSI — agent-ready infrastructure for Algorithm Design & Analysis projects.

Core helpers (use them in any project):
    from vsi.measure import Meter              # time, peak memory, states explored, pruning %
    from vsi.experiment import run_experiments # every algorithm x every instance -> results/metrics.csv
    from vsi.pareto import pareto_filter, hypervolume, select_best   # 2 objectives, both minimised
    from vsi import plots, check

Project catalog: vsi/projects/index.json  (CLI: `vsi list`, `vsi find <words>`, `vsi new <slug> <dir>`)
"""

__version__ = "0.1.0"
