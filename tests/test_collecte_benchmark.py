from pathlib import Path

import pytest

from diagnostic.collecter_benchmark_jumia import lire_liens_exclus
from diagnostic.constituer_holdout_jumia import normaliser


def test_lire_liens_exclus_agrege_plusieurs_csv(tmp_path: Path):
    premier = tmp_path / "premier.csv"
    premier.write_text(
        "nom,lien\nProduit A,https://example.test/a\n",
        encoding="utf-8",
    )
    second = tmp_path / "second.csv"
    second.write_text(
        "nom,lien\nProduit B,https://example.test/b\n",
        encoding="utf-8",
    )

    assert lire_liens_exclus([premier, second]) == {
        "https://example.test/a",
        "https://example.test/b",
    }


def test_lire_liens_exclus_refuse_un_csv_absent(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        lire_liens_exclus([tmp_path / "absent.csv"])


def test_normaliser_retire_les_accents():
    assert normaliser("Écouteurs connectés") == "ecouteurs connectes"
