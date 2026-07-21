import requests
from bs4 import BeautifulSoup
from urllib.parse import quote


class ScrapingError(Exception):
    """Levée en cas d'erreur réseau ou de scraping sur Jumia."""
    pass

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

BASE_URL = "https://www.jumia.ci/catalog/?q="


def chercher_produits(mot_cle, max_results=5, timeout=10):
    """
    Recherche un mot-clé sur Jumia et retourne une liste de produits.

    Retourne toujours une liste (vide en cas d'échec ou d'absence de résultat),
    ni exception non gérée (sauf ScrapingError volontairement levée).

    LIMITE CONNUE : la clé "categorie_jumia" vaut toujours None. Jumia génère
    cette information via JavaScript (Google Tag Manager), donc invisible
    pour un scraping HTML brut (requests+BeautifulSoup). Vérifié le : aucune
    trace ni dans les attributs data-ga4-*, ni dans le JSON-LD de la page.
    La détection D3E doit donc reposer uniquement sur MOTS_CLES_D3E (nom du
    produit), comme prévu en filet de sécurité dans le contrat d'interface.
    """
    if not mot_cle or not mot_cle.strip():
        print("Erreur: mot-clé vide.")
        return []

    encoded_mot_cle = quote(mot_cle.strip())
    url = f"{BASE_URL}{encoded_mot_cle}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        response.raise_for_status()  # lève une erreur si status >= 400
    except requests.exceptions.Timeout:
        print("Erreur: le site Jumia met trop de temps à répondre.")
        return []
    except requests.exceptions.ConnectionError:
        print("Erreur: impossible de se connecter à Jumia (vérifie ta connexion internet).")
        return []
    except requests.exceptions.HTTPError as e:
        print(f"Erreur HTTP: {e}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Erreur inattendue lors de la requête: {e}")
        return []

    soup = BeautifulSoup(response.text, "lxml")
    products = soup.select("article.prd")

    if not products:
        print(f"Aucun produit trouvé pour '{mot_cle}'.")
        return []

    results = []
    for product in products[:max_results]:
        name_tag = product.select_one("h3.name")
        price_tag = product.select_one("div.prc")
        img_tag = product.select_one("img")
        link_tag = product.select_one("a.core")
        category_tag = link_tag.get("data-ga4-item-category") if link_tag else None

        name = name_tag.get_text(strip=True) if name_tag else "Nom inconnu"
        price = price_tag.get_text(strip=True) if price_tag else "Prix non disponible"

        image = None
        if img_tag:
            image = img_tag.get("data-src") or img_tag.get("src")

        link = link_tag.get("href") if link_tag else None
        if link and link.startswith("/"):
            link = "https://www.jumia.ci" + link

        results.append({
            "nom": name,
            "prix": price,
            "image_url": image,
            "lien": link,
            "categorie_jumia": category_tag,
        })

    return results


if __name__ == "__main__":
    # Quelques tests rapides
    for mot_cle in ["bouteille plastique", "bouteille verre", "carton", "pile", "smartphone", "journal", "boite de conserve", "pot de confiture"]:
        print(f"\n=== Recherche: {mot_cle} ===")
        results = chercher_produits(mot_cle)
        for r in results:
            print(r)
