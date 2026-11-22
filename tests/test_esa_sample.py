"""Testet e shembullit zyrtar (10 transfere) nga ESA Luna Tomato Logistics.

Vendose kete file te: tests/test_esa_sample.py
Pastaj ekzekuto: python tasks.py test

Ky test perdor parser-in dhe fitness-in tone mbi shembullin e publikuar
nga ESA. Krahasimi me evaluatorin zyrtar per dataset-et e medha
behet vecmas te tests/test_official_fitness.py.
"""

import pytest

from matching import is_valid, load_transfers, total_weight


ESA_EXAMPLE = """\
1 1 1 6.202
2 2 1 6.386
3 2 2 2.641
4 3 2 0.577
5 3 3 0.254
6 4 3 8.042
7 4 4 8.221
8 5 4 8.800
9 5 5 0.213
10 6 5 4.275
"""


def test_shembulli_esa_lexohet(tmp_path):
    """Lexohen sakte 10 rreshtat e shembullit zyrtar."""
    file_path = tmp_path / "esa_example.txt"
    file_path.write_text(ESA_EXAMPLE, encoding="utf-8")

    transfers = load_transfers(file_path)
    assert len(transfers) == 10
    assert transfers[0].earth == 1
    assert transfers[0].moon == 1
    assert transfers[0].destination == 1
    assert transfers[0].weight == pytest.approx(6.202)


@pytest.mark.parametrize(
    "vector, expected_weight, valid",
    [
        ([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 0.0, True),
        ([1, 0, 0, 0, 0, 0, 0, 0, 0, 0], 6.202, True),
        ([1, 0, 1, 0, 0, 0, 0, 0, 0, 0], 8.843, True),
        ([1, 1, 0, 0, 0, 0, 0, 0, 0, 0], 0.0, False),
        ([0, 1, 1, 0, 0, 0, 0, 0, 0, 0], 0.0, False),
    ],
)
def test_rezultatet_e_publikuara_nga_esa(tmp_path, vector, expected_weight, valid):
    """Zgjidhjet e vlefshme dhe konfliktet perputhen me shembullin e ESA-s."""
    file_path = tmp_path / "esa_example.txt"
    file_path.write_text(ESA_EXAMPLE, encoding="utf-8")
    transfers = load_transfers(file_path)

    selected_indices = [i for i, chosen in enumerate(vector) if chosen == 1]
    assert is_valid(transfers, selected_indices) is valid
    assert total_weight(transfers, selected_indices) == pytest.approx(expected_weight)
