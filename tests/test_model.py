from pathlib import Path

import numpy as np
import pytest
from PIL import Image

import model.predict as prediction


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
