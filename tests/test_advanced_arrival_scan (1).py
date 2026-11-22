"""Fast unit tests for the candidate sampling used by advanced_arrival_scan.
These tests do not need pykep or the expensive ESA propagator.
"""
from src.advanced_arrival_scan import choose_spread


def _candidate(burn, raan, anomaly=0):
    return {"burn_mps": burn, "raan_deg": raan, "anomaly_deg": anomaly}


def test_choose_spread_empty():
    assert choose_spread([], 6) == []


def test_choose_spread_avoids_duplicate_orbital_phases():
    candidates = [
        _candidate(3000, 0, 90),
        _candidate(3010, 90, 0),  # same combined phase: 90 degrees
        _candidate(3100, 30, 90),
    ]
    chosen = choose_spread(candidates, 6)
    assert len(chosen) == 2
    assert chosen[0]["burn_mps"] == 3000


def test_choose_spread_keeps_energy_diversity():
    candidates = [_candidate(3000 + i*100, 30*i) for i in range(12)]
    chosen = choose_spread(candidates, 6)
    assert len(chosen) == 6
    assert chosen[0]["burn_mps"] == 3000
    assert chosen[-1]["burn_mps"] == 4100
