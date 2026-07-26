from unittest.mock import Mock

import pytest
import requests

from scraper.jumia_scraper import ScrapingError, chercher_produits


HTML_PRODUITS = """
<html><body>
  <article class="prd">
    <a class="core" href="/bouteille-verre.html">
      <img data-src="https://ke.jumia.is/unsafe/fit-in/300x300/product.jpg">
      <h3 class="name">Bouteille en verre</h3>
      <div class="prc">2 500 FCFA</div>
    </a>
  </article>
  <article class="prd"><div class="sponsorise">Publicite incomplete</div></article>
</body></html>
"""


def _response(html=HTML_PRODUITS):
    response = Mock()
    response.text = html
    response.raise_for_status.return_value = None
    return response


def test_recherche_retourne_uniquement_des_produits_complets(monkeypatch):
    monkeypatch.setattr("scraper.jumia_scraper.requests.get", lambda *a, **k: _response())

    produits = chercher_produits("bouteille", max_resultats=5)

    assert produits == [
        {
            "nom": "Bouteille en verre",
            "image_url": "https://ke.jumia.is/unsafe/fit-in/300x300/product.jpg",
            "prix": "2 500 FCFA",
            "lien": "https://www.jumia.ci/bouteille-verre.html",
            "categorie_jumia": None,
        }
    ]


def test_recherche_vide_ne_contacte_pas_jumia(monkeypatch):
    get = Mock()
    monkeypatch.setattr("scraper.jumia_scraper.requests.get", get)
    assert chercher_produits("   ") == []
    get.assert_not_called()


def test_timeout_devient_une_erreur_metier(monkeypatch):
    def timeout(*args, **kwargs):
        raise requests.Timeout()

    monkeypatch.setattr("scraper.jumia_scraper.requests.get", timeout)
    with pytest.raises(ScrapingError):
        chercher_produits("cahier")
