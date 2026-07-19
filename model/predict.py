import tensorflow as tf
import numpy as np

# Chemin vers le modele entraine (charge une seule fois a l'import du module,
# pas a chaque appel de la fonction, pour rester performant)
CHEMIN_MODELE = "model/modele_eco_sort.h5"
TAILLE_IMAGE = (224, 224)

CLASSES = ["cardboard", "glass", "metal", "paper", "plastic", "trash"]

# Mapping classe Kaggle -> categorie couleur du contrat d'interface
MAPPING_COULEUR = {
    "cardboard": "jaune",
    "metal": "jaune",
    "plastic": "jaune",
    "glass": "vert",
    "paper": "bleu",
    "trash": "marron",
}

_modele = None  # charge une seule fois, en cache (voir get_modele())


def get_modele():
    """Charge le modele en memoire une seule fois (paresseux),
    pour eviter de le recharger a chaque appel de predire_categorie()."""
    global _modele
    if _modele is None:
        _modele = tf.keras.models.load_model(CHEMIN_MODELE)
    return _modele


def predire_categorie(chemin_image: str) -> dict:
    """
    Prend le chemin d'une image produit et renvoie
    la categorie de tri predite.

    Retour :
    {
        "categorie": "jaune",   # jaune / vert / bleu / marron
        "confiance": 0.87       # score entre 0 et 1
    }
    """
    modele = get_modele()

    # Charge et prepare l'image exactement comme a l'entrainement
    img = tf.keras.utils.load_img(chemin_image, target_size=TAILLE_IMAGE)
    img_array = tf.keras.utils.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)  # ajoute la dimension "batch"

    # Note : pas besoin d'appliquer preprocess_input ici, la couche
    # Rescaling est deja integree dans le modele (voir train.py)
    predictions = modele.predict(img_array, verbose=0)[0]

    indice_classe = int(np.argmax(predictions))
    classe_kaggle = CLASSES[indice_classe]
    confiance = float(predictions[indice_classe])

    return {
        "categorie": MAPPING_COULEUR[classe_kaggle],
        "confiance": round(confiance, 4),
    }


if __name__ == "__main__":
    # Petit test manuel : lance "python model/predict.py chemin/vers/image.jpg"
    import sys
    if len(sys.argv) > 1:
        resultat = predire_categorie(sys.argv[1])
        print(resultat)
    else:
        print("Usage : python model/predict.py chemin/vers/image.jpg")