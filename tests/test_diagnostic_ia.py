from pathlib import Path

from diagnostic_ia import lire_images_jumia


def test_benchmark_transmet_le_mot_cle_de_recherche(tmp_path: Path):
    csv_benchmark = tmp_path / "benchmark.csv"
    csv_benchmark.write_text(
        "fichier,nom,recherche,categorie_jumia,poubelle_attendue\n"
        "image.jpg,Téléphone de test,smartphone,,gris\n",
        encoding="utf-8",
    )

    lignes = lire_images_jumia(csv_benchmark, limite=10)

    assert lignes[0]["mot_cle"] == "smartphone"


def test_ancien_csv_sans_recherche_reste_compatible(tmp_path: Path):
    csv_benchmark = tmp_path / "ancien.csv"
    csv_benchmark.write_text(
        "fichier,nom,categorie_jumia,poubelle_attendue\n"
        "image.jpg,Cahier,,bleu\n",
        encoding="utf-8",
    )

    lignes = lire_images_jumia(csv_benchmark, limite=10)

    assert lignes[0]["mot_cle"] == ""
