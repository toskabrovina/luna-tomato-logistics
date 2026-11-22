"""Leximi i transfereve dhe kontrolli i zgjidhjes per Luna Tomato Logistics.

Ky file eshte kodi yne, i ndare nga biblioteka VSI dhe vleresuesi zyrtar ESA.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Transfer:
    earth: int         # Orbita rreth Tokes (E)
    moon: int          # Orbita rreth Henes (L)
    destination: int   # Destinacioni ne Hene (D)
    weight: float      # Sasia qe mund te transportohet


def load_transfers(file_path: str | Path) -> list[Transfer]:
    """Lexon rreshta ne formatin: E L D pesha."""
    transfers = []
    with open(file_path, encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            columns = line.split()
            if len(columns) != 4:
                raise ValueError(f"Rreshti {line_number}: duhen 4 vlera (E L D pesha)")

            try:
                earth = int(columns[0])
                moon = int(columns[1])
                destination = int(columns[2])
                weight = float(columns[3])
            except ValueError as error:
                raise ValueError(f"Rreshti {line_number}: vlere e pavlefshme") from error

            transfers.append(Transfer(earth, moon, destination, weight))

    return transfers


def is_valid(transfers: list[Transfer], selected_indices: list[int]) -> bool:
    """True kur asnje orbite E/L ose destinacion D nuk perseritet."""
    used_earth = set()
    used_moon = set()
    used_destinations = set()

    for index in selected_indices:
        if not isinstance(index, int) or not 0 <= index < len(transfers):
            return False

        transfer = transfers[index]
        if (transfer.earth in used_earth
                or transfer.moon in used_moon
                or transfer.destination in used_destinations):
            return False

        used_earth.add(transfer.earth)
        used_moon.add(transfer.moon)
        used_destinations.add(transfer.destination)

    return True


def total_weight(transfers: list[Transfer], selected_indices: list[int]) -> float:
    """Shuma e peshave; nese zgjidhja ka konflikt, rezultati eshte 0."""
    if not is_valid(transfers, selected_indices):
        return 0.0
    return sum(transfers[index].weight for index in selected_indices)


if __name__ == "__main__":
    # Shembull i vogel per me vertetu qe kontrolli punon.
    sample = [Transfer(1, 1, 1, 6.0),
              Transfer(2, 2, 1, 9.0),
              Transfer(3, 3, 2, 8.0)]

    assert is_valid(sample, [1, 2])
    assert total_weight(sample, [1, 2]) == 17.0
    assert not is_valid(sample, [0, 1])  # D1 perdoret dy here.
    assert total_weight(sample, [0, 1]) == 0.0
    print("OK: kontrolli i zgjidhjes kaloi testet e vogla.")

    # VSI i ka shkarkuar te dhenat zyrtare ne kete rruge.
    data_file = (Path(__file__).resolve().parent.parent
                 / "data" / "spoc4" / "ltl" / "random_harder_5000.txt")
    if data_file.exists():
        transfers = load_transfers(data_file)
        print(f"Matching I: u lexuan {len(transfers)} transfere.")
    else:
        print(f"Nuk u gjet dataset-i: {data_file}")
