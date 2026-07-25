from pathlib import Path

import numpy as np
import pytest
from PIL import Image

import model.predict as prediction
from model.evaluer import calculer_metriques, construire_matrice


class FauxModele:
    def __init__(self, sortie):
        self.sortie = sortie

    def predict(self, image, verbose=0):
        return self.sortie


def _image_test(tmp_path: Path) -> Path:
    chemin = tmp_path / "produit.png"
    Image.new("RGB", (20, 20), "white").save(chemin)
    return chemin


def test_prediction_mappe_plastique_vers_bac_jaune(monkeypatch, tmp_path):
    scores = np.array([[0.01, 0.02, 0.03, 0.04, 0.88, 0.02]])
    monkeypatch.setattr(prediction, "get_modele", lambda: FauxModele(scores))

    resultat = prediction.predire_categorie(str(_image_test(tmp_path)))

    assert resultat == {"categorie": "jaune", "confiance": 0.88}


def test_prediction_refuse_une_sortie_de_mauvaise_taille(monkeypatch, tmp_path):
    monkeypatch.setattr(
        prediction,
        "get_modele",
        lambda: FauxModele(np.array([[0.5, 0.5]])),
    )

    with pytest.raises(ValueError, match="forme"):
        prediction.predire_categorie(str(_image_test(tmp_path)))


def test_metriques_reproduisent_evaluation_historique():
    matrice = np.array(
        [
            [52, 0, 1, 5, 1, 2],
            [0, 52, 15, 0, 8, 0],
            [0, 3, 58, 0, 0, 1],
            [6, 0, 4, 77, 0, 3],
            [0, 9, 2, 0, 56, 6],
            [1, 0, 2, 2, 1, 16],
        ]
    )

    rapport = calculer_metriques(matrice)

    assert rapport["nombre_images"] == 383
    assert rapport["nombre_correct"] == 311
    assert rapport["accuracy"] == 0.812
    assert rapport["macro_f1"] == 0.7919
    assert rapport["par_classe"]["trash"]["f1"] == 0.64


def test_construction_matrice():
    matrice = construire_matrice(
        np.array([0, 0, 1, 5]),
        np.array([0, 1, 1, 5]),
    )

    assert matrice[0, 0] == 1
    assert matrice[0, 1] == 1
    assert matrice[1, 1] == 1
    assert matrice[5, 5] == 1
