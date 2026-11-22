"""Smoke test: every instance size can be generated. Add real correctness tests next to it."""

import pytest

generator = pytest.importorskip("generator")


@pytest.mark.parametrize("size", ["small"])
def test_generate_instance(size):
    instance = generator.make_instance(size, seed=0)
    assert instance is not None
