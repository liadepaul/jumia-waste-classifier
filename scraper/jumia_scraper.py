from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.jumia.ci/catalog/?q="
DOMAINE_JUMIA = "https://www.jumia.ci"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}

MARQUEURS_BLOCAGE = (
    "captcha",
    "access denied",
    "attention required",
    "cloudflare",
    "are you a robot",
    "verify you are human",
    "vérifiez que vous êtes humain",
    "verifiez que vous etes humain",
)

MARQUEURS_AUCUN_RESULTAT = (
    "aucun résultat",
    "aucun resultat",
    "aucun produit",
    "0 résultat",
    "0 resultat",
    "no results",
    "no product found",
    "we couldn't find",
    "nous n'avons trouvé aucun",
    "nous n'avons trouve aucun",
)


class ScrapingError(Exception):
    """
    Erreur contrôlée produite pendant l'interrogation ou
    l'analyse d'une page Jumia.
    """


def _verifier_page_sans_produits(
    html_brut: str,
    soup: BeautifulSoup,
) -> None:
    """
    Analyse une page dans laquelle aucun bloc produit n'a été trouvé.

    La fonction :
    - lève ScrapingError en cas de blocage ou CAPTCHA ;
    - ne lève rien lorsqu'un message d'absence de résultats est détecté ;
    - lève ScrapingError si la structure de la page n'est plus reconnue.
    """
    html_minuscule = html_brut.lower()
    texte_visible = soup.get_text(" ", strip=True).lower()

    for marqueur in MARQUEURS_BLOCAGE:
        if marqueur in html_minuscule:
            raise ScrapingError(
                "Jumia semble bloquer la requête automatisée "
                f"(marqueur détecté : {marqueur!r})."
            )

    for marqueur in MARQUEURS_AUCUN_RESULTAT:
        if marqueur in texte_visible:
            return

    raise ScrapingError(
        "Aucun bloc produit n'a été détecté et aucun message "
        "d'absence de résultats n'a été reconnu. La structure HTML "
        "de Jumia a peut-être changé."
    )


def chercher_produits(
    mot_cle: str,
    max_resultats: int = 5,
    timeout: int = 10,
) -> list[dict]:
    """
    Recherche des produits sur Jumia Côte d'Ivoire.

    Paramètres
    ----------
    mot_cle:
        Mot ou expression à rechercher.
    max_resultats:
        Nombre maximal de produits à renvoyer. La valeur est limitée à 5.
    timeout:
        Délai maximal de la requête HTTP, en secondes.

    Retour
    ------
    Une liste de dictionnaires respectant le contrat :

    {
        "nom": "...",
        "image_url": "https://...",
        "prix": "...",
        "lien": "https://...",
        "categorie_jumia": None,
    }

    Une recherche vide ou une véritable absence de résultats renvoie [].
    Une erreur réseau, HTTP, un blocage ou une structure HTML non reconnue
    lève ScrapingError.
    """
    if not isinstance(mot_cle, str) or not mot_cle.strip():
        return []

    try:
        limite = int(max_resultats)
    except (TypeError, ValueError):
        limite = 5

    limite = max(1, min(limite, 5))

    mot_cle_encode = quote(mot_cle.strip())
    url = f"{BASE_URL}{mot_cle_encode}"

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=timeout,
        )
        response.raise_for_status()

    except requests.exceptions.Timeout as erreur:
        raise ScrapingError(
            "Le site Jumia met trop de temps à répondre."
        ) from erreur

    except requests.exceptions.ConnectionError as erreur:
        raise ScrapingError(
            "Impossible de se connecter à Jumia."
        ) from erreur

    except requests.exceptions.HTTPError as erreur:
        raise ScrapingError(
            f"Jumia a renvoyé une erreur HTTP : {erreur}"
        ) from erreur

    except requests.exceptions.RequestException as erreur:
        raise ScrapingError(
            f"Erreur pendant la requête Jumia : {erreur}"
        ) from erreur

    try:
        soup = BeautifulSoup(response.text, "lxml")
    except Exception as erreur:
        raise ScrapingError(
            f"Impossible d'analyser la page Jumia : {erreur}"
        ) from erreur

    produits_html = soup.select("article.prd")

    if not produits_html:
        _verifier_page_sans_produits(response.text, soup)
        return []

    resultats = []

    for produit in produits_html[:limite]:
        nom_tag = produit.select_one("h3.name")
        prix_tag = produit.select_one("div.prc")
        image_tag = produit.select_one("img")
        lien_tag = produit.select_one("a.core")

        nom = (
            nom_tag.get_text(" ", strip=True)
            if nom_tag
            else "Nom inconnu"
        )

        prix = (
            prix_tag.get_text(" ", strip=True)
            if prix_tag
            else "Prix non disponible"
        )

        image_url = None
        if image_tag:
            image_url = (
                image_tag.get("data-src")
                or image_tag.get("data-lazy-src")
                or image_tag.get("src")
            )

            if image_url:
                image_url = urljoin(DOMAINE_JUMIA, image_url)

        lien = lien_tag.get("href") if lien_tag else None
        if lien:
            lien = urljoin(DOMAINE_JUMIA, lien)

        resultats.append(
            {
                "nom": nom,
                "image_url": image_url,
                "prix": prix,
                "lien": lien,
                "categorie_jumia": None,
            }
        )

    return resultats


if __name__ == "__main__":
    mots_cles_test = [
        "bouteille",
        "smartphone",
        "cahier",
        "carton",
        "azertyproduitinexistant123456",
    ]

    for mot_cle_test in mots_cles_test:
        print(f"\n=== Recherche : {mot_cle_test} ===")

        try:
            produits = chercher_produits(mot_cle_test)

            if not produits:
                print("Aucun résultat.")
                continue

            for produit in produits:
                print(produit)

        except ScrapingError as erreur:
            print(f"ScrapingError : {erreur}")
