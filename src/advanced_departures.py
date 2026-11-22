"""Prepare valid Earth-orbit departure states for ESA Luna Tomato Logistics.

Run with Miniforge's luna-esa environment, from the project's main folder:
    python -m src.advanced_departures

This is NOT a Moon transfer solver or a valid Advanced submission yet.
It only generates initial states that match ESA's allowed Earth orbits.
"""
from __future__ import annotations

import json
from pathlib import Path

import pykep as pk

from src.esa_problem import load_udp

# Scale values and gravitational parameters taken from ESA's official evaluator.
L = 3.84405000e8
T = 3.7567696752e5
V = L / T
MU_EARTH = 398600435507000.0
MU_MOON = 4902800118000.0
MOON_RATIO = MU_MOON / (MU_MOON + MU_EARTH)
ROOT = Path(__file__).resolve().parent.parent


def departure_state(semimajor: float, eccentricity: float, inclination: float):
    """Translate a physical Earth-centered Keplerian orbit into the ESA BCP frame."""
    orbital_elements = [
        semimajor, eccentricity, inclination,
        0.1,  # RAAN: angle not fixed by ESA's starting-orbit data
        0.2,  # argument of periapsis
        0.3,  # true anomaly
    ]
    r_earth, v_earth = pk.par2ic(orbital_elements, MU_EARTH)
    r_earth = [float(v) for v in r_earth]
    v_earth = [float(v) for v in v_earth]

    # Inverse of state2earth() from ESA's official evaluation code.
    x = r_earth[0] / L - MOON_RATIO
    y = r_earth[1] / L
    z = r_earth[2] / L
    vx = v_earth[0] / V + y
    vy = v_earth[1] / V - x - MOON_RATIO
    vz = v_earth[2] / V
    state = [[x, y, z], [vx, vy, vz]]

    # Independent round trip back to Earth-centered orbital elements.
    r_check = [(x + MOON_RATIO) * L, y * L, z * L]
    v_check = [(vx - y) * V, (vy + x + MOON_RATIO) * V, vz * V]
    a2, e2, i2 = pk.ic2par(r_check, v_check, MU_EARTH)[:3]
    ok = (abs(a2 - semimajor) / L < 1e-6
          and abs(e2 - eccentricity) < 1e-6
          and abs(i2 - inclination) < 1e-6)
    return state, bool(ok)


def main():
    udp = load_udp("trajectory-matching")
    departures = []
    for earth_id, (a, e, inc) in enumerate(udp.earth_data):
        state, ok = departure_state(float(a), float(e), float(inc))
        if not ok:
            raise RuntimeError(f"Earth orbit {earth_id}: the starting state does not match")
        departures.append({"earth_id": earth_id, "t0": 0.0, "posvel": state})

    output = ROOT / "results" / "advanced_departures.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({
        "note": "Initial Earth-orbit states ONLY; not a lunar transfer or an ESA submission",
        "departures": departures,
    }, indent=2), encoding="utf-8")
    print(f"OK: {len(departures)} Earth-orbit departure states validated.")
    print(f"Saved: {output.relative_to(ROOT)}")
    print("Next: search and optimize Earth-to-Moon trajectories (not done yet).")


if __name__ == "__main__":
    main()
