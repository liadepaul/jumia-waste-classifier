from flask import Flask, render_template, request, redirect, url_for
import os
import sys
import uuid
import urllib.request

# Permet d'importer les modules du dossier model/ et scraper/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.predict import predire_categorie
from scraper.jumia_scraper import chercher_produits, ScrapingError

app = Flask(__name__)

# ---------------------------------------------------------
# Detection D3E (contrat, section 2.4)
# ---------------------------------------------------------
CATEGORIES_D3E_JUMIA = ["telephones-tablettes", "electromenager", "high-tech", "informatique"]

MOTS_CLES_D3E = [
    "smartphone", "telephone", "téléphone", "portable", "chargeur", "batterie",
    "ecouteur", "écouteur", "casque", "enceinte", "bluetooth", "mixeur",
    "montre connectee", "montre connectée", "cable usb", "câble usb", "power bank",
    "ordinateur", "laptop", "souris", "clavier", "imprimante", "tablette",
    "television", "télévision", "radio", "console", "ventilateur", "refrigerateur",
    "réfrigérateur", "climatiseur", "aspirateur",
]


def est_electronique(produit: dict) -> bool:
    if produit.get("categorie_jumia") in CATEGORIES_D3E_JUMIA:
        return True
    nom = produit["nom"].lower()
    return any(mot in nom for mot in MOTS_CLES_D3E)


# ---------------------------------------------------------
# Mapping couleur (contrat, section 2.5)
# Chaque entree contient :
#   hex             : couleur de fond du panneau verdict
#   bac_court       : gros label affiche (police Amatic SC)
#   explication     : phrase courte sous le label
#   texte_hex       : couleur du texte secondaire (nom produit, explication)
#   texte_fort_hex  : couleur du texte fort (label, badge confiance)
# ---------------------------------------------------------
MAPPING_AFFICHAGE = {
    "jaune": {
        "hex": "#FFD500",
        "bac_court": "Bac jaune",
        "explication": "Emballages recyclables : plastique, metal, carton",
        "texte_hex": "#5C4A00",
        "texte_fort_hex": "#3D3000",
    },
    "vert": {
        "hex": "#2E7D32",
        "bac_court": "Bac vert",
        "explication": "Verre uniquement (bouteilles, pots, bocaux)",
        "texte_hex": "#DCEFD1",
        "texte_fort_hex": "#F8F9F4",
    },
    "bleu": {
        "hex": "#1565C0",
        "bac_court": "Bac bleu",
        "explication": "Papier et cartons fins",
        "texte_hex": "#DCE9F7",
        "texte_fort_hex": "#F8F9F4",
    },
    "gris": {
        "hex": "#616161",
        "bac_court": "Bac D3E",
        "explication": "Appareil electronique : point de collecte specialise",
        "texte_hex": "#E4E4E4",
        "texte_fort_hex": "#F8F9F4",
    },
    "marron": {
        "hex": "#4E342E",
        "bac_court": "Bac marron",
        "explication": "Dechet non recyclable",
        "texte_hex": "#E9DED9",
        "texte_fort_hex": "#F8F9F4",
    },
    "incertain": {
        "hex": "#9E9E9E",
        "bac_court": "Incertain",
        "explication": "Confiance insuffisante, verifier manuellement",
        "texte_hex": "#2B2B2B",
        "texte_fort_hex": "#1B2420",
    },
}


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def telecharger_image(url: str) -> str:
    """Telecharge une image produit dans un dossier temporaire et renvoie son chemin local."""
    dossier_tmp = os.path.join(BASE_DIR, "static", "tmp")
    os.makedirs(dossier_tmp, exist_ok=True)
    nom_fichier = f"produit_{uuid.uuid4().hex}.jpg"
    chemin_local = os.path.join(dossier_tmp, nom_fichier)
    urllib.request.urlretrieve(url, chemin_local)
    return chemin_local


# ---------------------------------------------------------
# Routes
# ---------------------------------------------------------
@app.route("/")
def accueil():
    return render_template("index.html")


@app.route("/recherche", methods=["POST"])
def recherche():
    mot_cle = request.form.get("mot_cle", "").strip()
    if not mot_cle:
        return redirect(url_for("accueil"))

    try:
        produits = chercher_produits(mot_cle)
    except ScrapingError:
        return render_template("resultats.html", produits=[], mot_cle=mot_cle,
                                erreur="Le site est momentanement indisponible. Reessaie plus tard.")

    if not produits:
        return render_template("resultats.html", produits=[], mot_cle=mot_cle,
                                erreur="Aucun resultat trouve pour ce mot-cle.")

    return render_template("resultats.html", produits=produits, mot_cle=mot_cle, erreur=None)


@app.route("/verdict", methods=["POST"])
def verdict():
    nom = request.form.get("nom")
    image_url = request.form.get("image_url")
    categorie_jumia = request.form.get("categorie_jumia", "")

    produit = {"nom": nom, "image_url": image_url, "categorie_jumia": categorie_jumia}

    if est_electronique(produit):
        categorie = "gris"
        confiance = None
    else:
        try:
            chemin_image = telecharger_image(image_url)
            resultat = predire_categorie(chemin_image)
            if resultat["confiance"] < 0.5:
                categorie = "incertain"
            else:
                categorie = resultat["categorie"]
            confiance = resultat["confiance"]
        except Exception:
            categorie = "incertain"
            confiance = None

    affichage = MAPPING_AFFICHAGE[categorie]
    return render_template("verdict.html", produit=produit, affichage=affichage, confiance=confiance)


if __name__ == "__main__":
    # host="0.0.0.0" est indispensable pour que l'app soit accessible
    # depuis l'exterieur du conteneur Docker. debug=False en livraison.
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
