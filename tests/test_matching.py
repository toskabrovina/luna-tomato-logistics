"""Teste per leximin e transfereve dhe vlefshmerine e zgjidhjeve.

Keto teste kontrollojne kodin tone te src/matching.py.
"""

import pytest

from matching import Transfer, is_valid, load_transfers, total_weight
from algorithms import greedy_indices


def test_leximi_i_datasetit(tmp_path):
    sample_file = tmp_path / "shembull.txt"
    sample_file.write_text(
        "# Koment\n\n1 1 1 6.0\n2 2 1 9.0\n3 3 2 8.0\n",
        encoding="utf-8",
    )

    assert load_transfers(sample_file) == [
        Transfer(1, 1, 1, 6.0),
        Transfer(2, 2, 1, 9.0),
        Transfer(3, 3, 2, 8.0),
    ]


@pytest.mark.parametrize("bad_line", ["1 2 3", "1 2 3 4 5", "1 x 3 4.5"])
def test_refuzohen_rreshtat_e_gabuar(tmp_path, bad_line):
    sample_file = tmp_path / "gabim.txt"
    sample_file.write_text(bad_line + "\n", encoding="utf-8")

    with pytest.raises(ValueError):
        load_transfers(sample_file)


def test_zgjidhja_e_vlefshme_dhe_pesha():
    transfers = [
        Transfer(1, 1, 1, 6.0),
        Transfer(2, 2, 1, 9.0),
        Transfer(3, 3, 2, 8.0),
    ]

    assert is_valid(transfers, [1, 2])
    assert total_weight(transfers, [1, 2]) == 17.0

    # Te dy transferet perdorin destinacionin 1.
    assert not is_valid(transfers, [0, 1])
    assert total_weight(transfers, [0, 1]) == 0.0


def test_refuzohen_konfliktet_ne_secili_grup():
    transfers = [
        Transfer(1, 1, 1, 5.0),
        Transfer(1, 2, 2, 6.0),  # e njejta orbite e Tokes
        Transfer(2, 1, 3, 7.0),  # e njejta orbite e Henes
        Transfer(3, 3, 1, 8.0),  # i njejti destinacion
    ]

    assert not is_valid(transfers, [0, 1])
    assert not is_valid(transfers, [0, 2])
    assert not is_valid(transfers, [0, 3])
    assert not is_valid(transfers, [0, 0])


def test_refuzohen_indekset_jashte_kufijve():
    transfers = [Transfer(1, 1, 1, 5.0)]

    assert not is_valid(transfers, [-1])
    assert not is_valid(transfers, [1])


def test_greedy_zgjedh_transfere_pa_konflikt():
    transfers = [
        Transfer(1, 1, 1, 6.0),
        Transfer(2, 2, 1, 9.0),
        Transfer(3, 3, 2, 8.0),
    ]
    chosen = greedy_indices(transfers)

    assert chosen == [1, 2]
    assert is_valid(transfers, chosen)
    assert total_weight(transfers, chosen) == 17.0
