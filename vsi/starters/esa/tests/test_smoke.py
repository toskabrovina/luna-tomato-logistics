"""The official UDP loads and its bounds make sense. Skipped until `python tasks.py data` has run and the
packages in requirements-official.txt are installed. Add real tests for your own evaluator next to it."""

import pytest

import esa_problem


@pytest.mark.parametrize("problem_id", esa_problem.PROBLEM_IDS)
def test_official_udp_loads(problem_id):
    if not esa_problem.udp_file(problem_id).exists():
        pytest.skip("official code not downloaded yet: python tasks.py data")
    try:
        udp = esa_problem.load_udp(problem_id)
    except ImportError as exc:
        pytest.skip(f"official code needs a package: {exc} (see requirements-official.txt)")
    lower, upper = udp.get_bounds()
    assert len(lower) == len(upper) > 0
