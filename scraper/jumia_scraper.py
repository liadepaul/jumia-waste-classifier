import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

BASE_URL = "https://www.jumia.ci/catalog/?q="


class ScrapingError(Exception):
    """
    Levee en cas d'erreur reseau (timeout, connexion impossible, HTTP >= 400)
    ou si la structure HTML de Jumia a change au point de ne plus pouvoir
    parser la page. Le module app.py doit intercepter cette exception et
    afficher un message d'erreur propre a l'utilisateur, sans planter.
    """
    pass


MARQUEURS_BLOCAGE = [
    "captcha", "access denied", "attention required",
    "cloudflare", "are you a robot", "verifiez que vous",
]


def _verifier_page_valide(html_brut: str, soup: BeautifulSoup) -> None:
    """
    Appelee uniquement quand aucun article.prd n'est trouve.
    Distingue une vraie absence de resultats d'un blocage ou d'un
    changement de structure HTML, en levant ScrapingError si la page
    ne ressemble pas a une page Jumia normale.
    """
    texte_minuscule = html_brut.lower()

    for marqueur in MARQUEURS_BLOCAGE:
        if marqueur in texte_minuscule:
            raise ScrapingError(
                f"Jumia semble bloquer la requete (marqueur detecte : '{marqueur}')."
            )

    # Un element stable de la page catalogue, present que la recherche
    # ait des resultats ou non. S'il manque aussi, la structure a change
    # ou la page recue n'est pas une page de resultats valide.
    page_reconnue = (
        soup.select_one("div.catalog") is not None
        or soup.select_one("#jm-content") is not None
        or "jumia" in texte_minuscule
    )

    if not page_reconnue:
        raise ScrapingError(
            "Page Jumia non reconnue : ni produits, ni conteneur catalogue "
            "attendu. La structure du site a peut-etre change."
        )


def chercher_produits(mot_cle: str, max_resultats: int = 5, timeout: int = 10) -> list[dict]:
    """
    Interroge Jumia avec le mot-cle fourni et renvoie 3 a 5 resultats.

    Retour :
    [
        {
            "nom": "Shampooing Head & Shoulders 400ml",
            "image_url": "https://...",
            "prix": "2500 FCFA",
            "lien": "https://www.jumia.ci/...",
            "categorie_jumia": None  # non extrait de la page de resultats, voir note ci-dessous
        },
        ...
    ]

    Si aucun resultat : renvoie une liste vide [].
    En cas d'erreur reseau/scraping : leve ScrapingError plutot que de planter.

    Note sur "categorie_jumia" : ce champ n'est pas directement disponible
    dans le HTML de la page de resultats de recherche Jumia (contrairement
    au nom/prix/image/lien). Il reste a None ici ; la detection D3E cote
    interface (est_electronique) se base alors uniquement sur les mots-cles
    presents dans le nom du produit, ce qui a ete valide comme suffisant.
    """
    if not mot_cle or not mot_cle.strip():
        return []

    mot_cle_encode = quote(mot_cle.strip())
    url = f"{BASE_URL}{mot_cle_encode}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        response.raise_for_status()  # leve une erreur si status >= 400
    except requests.exceptions.Timeout:
        raise ScrapingError("Le site Jumia met trop de temps a repondre (timeout).")
    except requests.exceptions.ConnectionError:
        raise ScrapingError("Impossible de se connecter a Jumia (verifie la connexion internet).")
    except requests.exceptions.HTTPError as e:
        raise ScrapingError(f"Erreur HTTP lors de la requete Jumia : {e}")
    except requests.exceptions.RequestException as e:
        raise ScrapingError(f"Erreur inattendue lors de la requete Jumia : {e}")

    try:
        soup = BeautifulSoup(response.text, "lxml")
        produits_html = soup.select("article.prd")
    except Exception as e:
        raise ScrapingError(f"Erreur lors du parsing de la page Jumia (structure HTML modifiee ?) : {e}")

    if not produits_html:
        _verifier_page_valide(response.text, soup)
        return []

    resultats = []
    for produit in produits_html[:max_resultats]:
        name_tag = produit.select_one("h3.name")
        price_tag = produit.select_one("div.prc")
        img_tag = produit.select_one("img")
        link_tag = produit.select_one("a.core")

        nom = name_tag.get_text(strip=True) if name_tag else "Nom inconnu"
        prix = price_tag.get_text(strip=True) if price_tag else "Prix non disponible"

        image_url = None
        if img_tag:
            image_url = img_tag.get("data-src") or img_tag.get("src")

        lien = link_tag.get("href") if link_tag else None
        if lien and lien.startswith("/"):
            lien = "https://www.jumia.ci" + lien

        resultats.append({
            "nom": nom,
            "prix": prix,
            "image_url": image_url,
            "lien": lien,
            "categorie_jumia": None,
        })

    return resultats


if __name__ == "__main__":
    # Quelques tests manuels rapides
    mots_cles_test = [
        "bouteille plastique", "bouteille verre", "carton", "pile",
        "smartphone", "journal", "boite de conserve", "pot de confiture",
    ]
    for mot_cle in mots_cles_test:
        print(f"\n=== Recherche : {mot_cle} ===")
        try:
            resultats = chercher_produits(mot_cle)
            if not resultats:
                print("  Aucun resultat.")
            for r in resultats:
                print(" ", r)
        except ScrapingError as e:
            print(f"  ScrapingError : {e}")
