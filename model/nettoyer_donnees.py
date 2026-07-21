import os
import hashlib
from PIL import Image

RACINE = "data/split"
SPLITS = ["train", "validation", "test"]

def calculer_hash(chemin_fichier):
    """Calcule une empreinte unique du contenu du fichier, pour repérer les doublons exacts."""
    with open(chemin_fichier, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def verifier_image(chemin_fichier):
    """Retourne True si l'image s'ouvre et se decode correctement, False sinon."""
    try:
        with Image.open(chemin_fichier) as img:
            img.verify()
        # verify() abime l'objet, on rouvre pour un vrai test de decodage complet
        with Image.open(chemin_fichier) as img:
            img.load()
        return True
    except Exception:
        return False

def analyser_dataset():
    corrompues = []
    hash_vers_chemins = {}  # hash -> liste des chemins ayant ce hash
    total_images = 0

    for split in SPLITS:
        dossier_split = os.path.join(RACINE, split)
        if not os.path.isdir(dossier_split):
            continue
        for classe in os.listdir(dossier_split):
            dossier_classe = os.path.join(dossier_split, classe)
            if not os.path.isdir(dossier_classe):
                continue
            for fichier in os.listdir(dossier_classe):
                if not fichier.lower().endswith((".jpg", ".jpeg", ".png")):
                    continue
                chemin = os.path.join(dossier_classe, fichier)
                total_images += 1

                if not verifier_image(chemin):
                    corrompues.append(chemin)
                    continue

                h = calculer_hash(chemin)
                hash_vers_chemins.setdefault(h, []).append(chemin)

    doublons = {h: chemins for h, chemins in hash_vers_chemins.items() if len(chemins) > 1}

    print(f"\n=== RAPPORT DE NETTOYAGE ===")
    print(f"Total d'images analysees : {total_images}")

    print(f"\n--- Images corrompues : {len(corrompues)} ---")
    for c in corrompues:
        print(f"  {c}")

    print(f"\n--- Groupes de doublons exacts : {len(doublons)} ---")
    fuites_train_test = 0
    for h, chemins in doublons.items():
        splits_presents = set()
        for c in chemins:
            for s in SPLITS:
                if f"{os.sep}{s}{os.sep}" in c:
                    splits_presents.add(s)
        alerte = ""
        if len(splits_presents) > 1:
            alerte = "  <-- ATTENTION : doublon present dans plusieurs splits !"
            fuites_train_test += 1
        print(f"  {chemins}{alerte}")

    print(f"\n--- Resume ---")
    print(f"Images corrompues a supprimer : {len(corrompues)}")
    print(f"Groupes de doublons trouves : {len(doublons)}")
    print(f"Doublons a cheval entre plusieurs splits (risque de fuite) : {fuites_train_test}")

    return corrompues, doublons

if __name__ == "__main__":
    analyser_dataset()
    