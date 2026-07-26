"""
Tests automatises pour scraper/jumia_scraper.py
"""
import sys
import os
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scraper"))

from jumia_scraper import chercher_produits


HTML_AVEC_DOUBLON = """
<html><body>
<article class="prd">
    <div class="img-c"><img src="https://ci.jumia.is/img/produitA.jpg"></div>
    <div class="info"><h3 class="name">Produit A</h3><div class="prc">1,000 FCFA</div></div>
    <a class="core" href="/produit-a-11111.html"></a>
</article>
<article class="prd">
    <div class="img-c"><img src="https://ci.jumia.is/img/produitA.jpg"></div>
    <div class="info"><h3 class="name">Produit A (doublon)</h3><div class="prc">1,000 FCFA</div></div>
    <a class="core" href="/produit-a-11111.html"></a>
</article>
<article class="prd">
    <div class="img-c"><img src="https://ci.jumia.is/img/produitB.jpg"></div>
    <div class="info"><h3 class="name">Produit B</h3><div class="prc">2,000 FCFA</div></div>
    <a class="core" href="/produit-b-22222.html"></a>
</article>
</body></html>
"""


class TestDeduplicationAvantLimite(unittest.TestCase):
    @patch("jumia_scraper.requests.get")
    def test_doublon_en_premiere_position_ne_bloque_pas_les_resultats(self, mock_get):
        """
        Sequence : produit A, doublon de A, produit B, avec max_resultats=2.
        Le resultat doit contenir 2 produits avec des liens uniques (A et B),
        et non pas seulement A comme avant la correction.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = HTML_AVEC_DOUBLON
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        resultats = chercher_produits("test", max_resultats=2)

        self.assertEqual(len(resultats), 2, "Devrait renvoyer exactement 2 produits")

        liens = [r["lien"] for r in resultats]
        self.assertEqual(
            len(set(liens)), 2, "Les 2 liens renvoyes doivent etre uniques"
        )
        self.assertTrue(
            any("produit-a" in lien for lien in liens),
            "Le produit A doit etre present",
        )
        self.assertTrue(
            any("produit-b" in lien for lien in liens),
            "Le produit B doit etre present",
        )


if __name__ == "__main__":
    unittest.main()
