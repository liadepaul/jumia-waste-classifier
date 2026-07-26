from flask import Flask, render_template, request, redirect, url_for
import os
import sys
import uuid
from pathlib import Path
from urllib.parse import urlparse

import requests


# Permet d'importer les modules des dossiers model/ et scraper/
sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    ),
)

from model.predict import predire_categorie
from scraper.jumia_scraper import chercher_produits, ScrapingError


app = Flask(__name__)


# ---------------------------------------------------------
# Détection D3E
# ---------------------------------------------------------
CATEGORIES_D3E_JUMIA = [
    "telephones-tablettes",
    "electromenager",
    "high-tech",
    "informatique",
]

MOTS_CLES_D3E = [
    "smartphone",
    "telephone",
    "téléphone",
    "chargeur",
    "batterie",
    "ecouteur",
    "écouteur",
    "casque",
    "enceinte bluetooth",
    "mixeur",
    "montre connectee",
    "montre connectée",
    "cable usb",
    "câble usb",
    "power bank",
    "ordinateur",
    "laptop",
    "souris informatique",
    "clavier",
    "imprimante",
    "tablette",
    "television",
    "télévision",
    "console de jeu",
    "ventilateur",
    "refrigerateur",
    "réfrigérateur",
    "climatiseur",
    "aspirateur",
]


# ---------------------------------------------------------
# Règles textuelles complémentaires
# ---------------------------------------------------------
MOTS_CLES_BLEU = [
    "papier",
    "cahier",
    "journal",
    "magazine",
    "livre",
    "enveloppe",
    "bloc-notes",
    "bloc notes",
    "carnet",
]

MOTS_CLES_VERT = [
    "bouteille en verre",
    "gourde en verre",
    "verre borosilicate",
    "bocal en verre",
    "pot en verre",
    "bocal de conserve",
    "pot de confiture",
]

MOTS_CLES_MARRON = [
    "verre à boire",
    "verre a boire",
    "vaisselle",
    "assiette",
    "tasse",
    "miroir",
    "vitre",
    "gourde réutilisable",
    "gourdes réutilisables",
    "gourde reutilisable",
    "gourdes reutilisables",
    "kit de coiffure",
    "brosse",
    "peigne",
    "coffre",
    "jouet",
    "multicouche",
    "multi-matière",
    "multi-matiere",
    "acier et plastique",
    "papier acier et plastique",
]

MOTS_CLES_JAUNE = [
    "bouteille plastique",
    "bouteille en plastique",
    "flacon plastique",
    "flacon en plastique",
    "carton d'emballage",
    "carton de colis",
    "canette",
    "boite de conserve",
    "boîte de conserve",
    "barquette aluminium",
]


def est_electronique(produit: dict) -> bool:
    """
    Détecte les produits électroniques à partir de la catégorie
    Jumia, du nom du produit et du mot-clé recherché.
    """
    categorie_jumia = produit.get("categorie_jumia", "")

    if categorie_jumia in CATEGORIES_D3E_JUMIA:
        return True

    nom = produit.get("nom", "")
    mot_cle = produit.get("mot_cle", "")
    texte = f"{nom} {mot_cle}".lower()

    return any(mot in texte for mot in MOTS_CLES_D3E)


def categorie_depuis_texte(produit: dict) -> str | None:
    """
    Détermine une catégorie lorsque le nom du produit ou le
    mot-clé recherché indique explicitement sa matière ou son type.
    """
    nom = produit.get("nom", "")
    mot_cle = produit.get("mot_cle", "")
    texte = f"{nom} {mot_cle}".lower()

    if any(mot in texte for mot in MOTS_CLES_MARRON):
        return "marron"

    contenant_en_verre = (
        "verre" in texte
        and any(
            contenant in texte
            for contenant in ("bocal", "bocaux", "bouteille", "pot")
        )
    )
    if contenant_en_verre or any(mot in texte for mot in MOTS_CLES_VERT):
        return "vert"

    if any(mot in texte for mot in MOTS_CLES_BLEU):
        return "bleu"

    bouteille_de_boisson = (
        "bouteille" in texte
        and "verre" not in texte
        and any(
            boisson in texte
            for boisson in ("eau", "boisson", "soda", "jus")
        )
    )
    produit_en_flacon = any(
        mot in texte
        for mot in ("shampoing", "shampooing", "après-shampooing")
    )
    if (
        bouteille_de_boisson
        or produit_en_flacon
        or any(mot in texte for mot in MOTS_CLES_JAUNE)
    ):
        return "jaune"

    return None


# ---------------------------------------------------------
# Mapping des catégories vers l'affichage
# ---------------------------------------------------------
MAPPING_AFFICHAGE = {
    "jaune": {
        "hex": "#FFD500",
        "bac_court": "Bac jaune",
        "explication": (
            "Emballages recyclables : plastique, métal, carton"
        ),
        "texte_hex": "#5C4A00",
        "texte_fort_hex": "#3D3000",
    },
    "vert": {
        "hex": "#2E7D32",
        "bac_court": "Bac vert",
        "explication": (
            "Verre uniquement : bouteilles, pots et bocaux"
        ),
        "texte_hex": "#DCEFD1",
        "texte_fort_hex": "#F8F9F4",
    },
    "bleu": {
        "hex": "#1565C0",
        "bac_court": "Bac bleu",
        "explication": "Papiers graphiques propres",
        "texte_hex": "#DCE9F7",
        "texte_fort_hex": "#F8F9F4",
    },
    "gris": {
        "hex": "#616161",
        "bac_court": "Bac D3E",
        "explication": (
            "Appareil électronique : point de collecte spécialisé"
        ),
        "texte_hex": "#E4E4E4",
        "texte_fort_hex": "#F8F9F4",
    },
    "marron": {
        "hex": "#4E342E",
        "bac_court": "Bac marron",
        "explication": "Déchet résiduel non recyclable",
        "texte_hex": "#E9DED9",
        "texte_fort_hex": "#F8F9F4",
    },
    "incertain": {
        "hex": "#9E9E9E",
        "bac_court": "Incertain",
        "explication": (
            "Confiance insuffisante, vérifier manuellement"
        ),
        "texte_hex": "#2B2B2B",
        "texte_fort_hex": "#1B2420",
    },
}


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HOTES_IMAGES_AUTORISES = ("jumia.ci", "jumia.is")


def _url_image_autorisee(url: str) -> bool:
    """N'autorise que les images HTTPS servies par Jumia ou son CDN."""
    try:
        parsed = urlparse(url)
        hote = (parsed.hostname or "").lower().rstrip(".")
    except (TypeError, ValueError):
        return False

    return (
        parsed.scheme == "https"
        and bool(parsed.path)
        and any(
            hote == domaine or hote.endswith(f".{domaine}")
            for domaine in HOTES_IMAGES_AUTORISES
        )
    )


def telecharger_image(url: str) -> str:
    """
    Télécharge une image Jumia avec des en-têtes de navigateur
    et renvoie son chemin local.
    """
    if not url:
        raise ValueError("Aucune URL d'image fournie.")
    if not _url_image_autorisee(url):
        raise ValueError("L'URL de l'image ne provient pas d'un domaine Jumia autorisé.")

    dossier_tmp = os.path.join(
        BASE_DIR,
        "static",
        "tmp",
    )
    os.makedirs(dossier_tmp, exist_ok=True)

    nom_fichier = f"produit_{uuid.uuid4().hex}.jpg"
    chemin_local = os.path.join(
        dossier_tmp,
        nom_fichier,
    )

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        ),
        "Referer": "https://www.jumia.ci/",
        "Accept": (
            "image/avif,image/webp,image/apng,"
            "image/*,*/*;q=0.8"
        ),
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=15,
        allow_redirects=True,
    )
    response.raise_for_status()
    if not _url_image_autorisee(response.url):
        raise ValueError("La redirection de l'image quitte les domaines Jumia autorisés.")

    type_contenu = response.headers.get(
        "Content-Type",
        "",
    ).lower()

    if not type_contenu.startswith("image/"):
        raise ValueError(
            "Le contenu téléchargé n'est pas une image : "
            f"{type_contenu}"
        )

    taille_maximale = 10 * 1024 * 1024

    if len(response.content) > taille_maximale:
        raise ValueError(
            "L'image téléchargée dépasse la limite de 10 Mo."
        )

    with open(chemin_local, "wb") as fichier:
        fichier.write(response.content)

    return chemin_local


def determiner_verdict(produit: dict, chemin_image: str | None = None) -> dict:
    """Applique la logique de décision et indique l'origine du verdict."""
    if est_electronique(produit):
        return {
            "categorie": "gris",
            "confiance": None,
            "source": "D3E",
            "erreur": None,
        }

    categorie_texte = categorie_depuis_texte(produit)
    if categorie_texte is not None:
        return {
            "categorie": categorie_texte,
            "confiance": None,
            "source": "règle texte",
            "erreur": None,
        }

    image_telechargee = chemin_image is None
    chemin_a_analyser = chemin_image

    try:
        if chemin_a_analyser is None:
            chemin_a_analyser = telecharger_image(
                produit.get("image_url", "")
            )

        resultat = predire_categorie(chemin_a_analyser)
        categorie_predite = resultat.get("categorie")
        confiance = float(resultat.get("confiance"))

        if categorie_predite not in {"jaune", "vert", "bleu", "marron"}:
            raise ValueError(
                f"Catégorie du modèle invalide : {categorie_predite!r}"
            )
        if not 0 <= confiance <= 1:
            raise ValueError(
                "La confiance du modèle doit être comprise entre 0 et 1."
            )

        return {
            "categorie": (
                "incertain" if confiance < 0.5 else categorie_predite
            ),
            "confiance": confiance,
            "source": "IA",
            "erreur": None,
        }
    except Exception as erreur:
        return {
            "categorie": "incertain",
            "confiance": None,
            "source": "erreur",
            "erreur": f"{type(erreur).__name__}: {erreur}",
        }
    finally:
        if image_telechargee and chemin_a_analyser:
            Path(chemin_a_analyser).unlink(missing_ok=True)


# ---------------------------------------------------------
# Routes Flask
# ---------------------------------------------------------
@app.route("/")
def accueil():
    return render_template("index.html")


@app.route("/health")
def health():
    """Point de contrôle léger pour Docker et les plateformes d'hébergement."""
    modele_present = Path(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "model",
        "modele_eco_sort.h5",
    ).is_file()
    return {"status": "ok" if modele_present else "degraded"}, (
        200 if modele_present else 503
    )


@app.route("/recherche", methods=["POST"])
def recherche():
    mot_cle = request.form.get(
        "mot_cle",
        "",
    ).strip()

    if not mot_cle:
        return redirect(url_for("accueil"))

    try:
        produits = chercher_produits(mot_cle)

    except ScrapingError as erreur:
        app.logger.warning(
            "Erreur du scraper pour %r : %s",
            mot_cle,
            erreur,
        )

        return render_template(
            "resultats.html",
            produits=[],
            mot_cle=mot_cle,
            erreur=(
                "Le site Jumia est momentanément indisponible. "
                "Réessaie plus tard."
            ),
        )

    if not produits:
        return render_template(
            "resultats.html",
            produits=[],
            mot_cle=mot_cle,
            erreur="Aucun résultat trouvé pour ce mot-clé.",
        )

    return render_template(
        "resultats.html",
        produits=produits,
        mot_cle=mot_cle,
        erreur=None,
    )


@app.route("/verdict", methods=["POST"])
def verdict():
    nom = request.form.get("nom", "")
    image_url = request.form.get("image_url", "")
    categorie_jumia = request.form.get(
        "categorie_jumia",
        "",
    )
    mot_cle = request.form.get("mot_cle", "")

    produit = {
        "nom": nom,
        "image_url": image_url,
        "categorie_jumia": categorie_jumia,
        "mot_cle": mot_cle,
    }

    decision = determiner_verdict(produit)
    categorie = decision["categorie"]
    confiance = decision["confiance"]

    if decision["erreur"]:
        app.logger.error(
            "Erreur pendant la classification de %r : %s",
            nom,
            decision["erreur"],
        )

    affichage = MAPPING_AFFICHAGE[categorie]

    return render_template(
        "verdict.html",
        produit=produit,
        affichage=affichage,
        confiance=confiance,
        source_verdict=decision["source"],
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
    )
