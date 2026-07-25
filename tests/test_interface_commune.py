from unittest.mock import patch

import pytest

from app.app import app


@pytest.fixture()
def client():
    app.config.update(TESTING=True)
    with app.test_client() as client_test:
        yield client_test


def test_accueil_charge_la_navigation_commune(client):
    reponse = client.get("/")

    assert reponse.status_code == 200
    assert b'class="site-header"' in reponse.data
    assert b'class="marque-ecosort"' in reponse.data
    assert b'id="contenu-principal"' in reponse.data
    assert b'id="recherche"' in reponse.data


def test_resultats_reutilisent_le_gabarit_commun(client):
    produits = [
        {
            "nom": "Cahier recycle",
            "image_url": "https://ke.jumia.is/cahier.jpg",
            "prix": "2 500 FCFA",
            "lien": "https://www.jumia.ci/cahier.html",
            "categorie_jumia": "",
        }
    ]

    with patch("app.app.chercher_produits", return_value=produits):
        reponse = client.post("/recherche", data={"mot_cle": "cahier"})

    assert reponse.status_code == 200
    assert b'class="site-header"' in reponse.data
    assert "Résultats".encode() in reponse.data
    assert b"Cahier recycle" in reponse.data


def test_poppins_est_servie_localement_sans_police_de_secours(client):
    feuille_style = client.get("/static/style.css")

    assert feuille_style.status_code == 200
    assert b"fonts.googleapis.com" not in feuille_style.data
    assert b"Amatic" not in feuille_style.data
    assert b"sans-serif" not in feuille_style.data

    for graisse in (400, 500, 600, 700):
        police = client.get(f"/static/fonts/poppins-{graisse}.woff2")
        assert police.status_code == 200
        assert police.data.startswith(b"wOF2")
