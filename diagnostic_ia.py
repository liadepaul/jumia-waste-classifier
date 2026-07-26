"""Compare le modèle seul à la logique complète de l'application."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np
import tensorflow as tf

from app.app import determiner_verdict
from model.predict import CLASSES, MAPPING_COULEUR, predire_categorie


EXTENSIONS_IMAGES = {".jpg", ".jpeg", ".png", ".webp"}


def choisir_images_dataset(racine: Path, limite: int) -> list[dict]:
    """Choisit les images à tour de rôle dans les six classes."""
    par_classe = {}
    for classe in MAPPING_COULEUR:
        dossier = racine / classe
        par_classe[classe] = sorted(
            chemin
            for chemin in dossier.glob("*")
            if chemin.suffix.lower() in EXTENSIONS_IMAGES
        )

    lignes = []
    index = 0
    while len(lignes) < limite:
        ajout = False
        for classe, images in par_classe.items():
            if index < len(images):
                lignes.append(
                    {
                        "type_image": "dataset",
                        "fichier": images[index],
                        "nom": "Échantillon de contrôle",
                        "categorie_jumia": "",
                        "attendue": MAPPING_COULEUR[classe],
                    }
                )
                ajout = True
                if len(lignes) == limite:
                    break
        if not ajout:
            break
        index += 1
    return lignes


def lire_images_jumia(fichier_csv: Path, limite: int) -> list[dict]:
    """Lit les images Jumia annotées manuellement."""
    lignes = []
    with fichier_csv.open(encoding="utf-8-sig", newline="") as fichier:
        for ligne in csv.DictReader(fichier):
            chemin = Path(ligne["fichier"])
            if not chemin.is_absolute():
                chemin = fichier_csv.parent / chemin
            lignes.append(
                {
                    "type_image": "jumia",
                    "fichier": chemin,
                    "nom": ligne["nom"],
                    "mot_cle": (
                        ligne.get("mot_cle")
                        or ligne.get("recherche")
                        or ""
                    ),
                    "categorie_jumia": ligne.get("categorie_jumia", ""),
                    "attendue": ligne["poubelle_attendue"].strip().lower(),
                }
            )
            if len(lignes) == limite:
                break
    return lignes


def creer_predicteur(chemin_modele: Path | None):
    """Retourne le prédicteur courant ou celui d'un modèle candidat."""
    if chemin_modele is None:
        return predire_categorie

    modele = tf.keras.models.load_model(chemin_modele)

    def predire(chemin_image: str) -> dict:
        image = tf.keras.utils.load_img(
            chemin_image,
            target_size=(224, 224),
        )
        tableau = tf.keras.utils.img_to_array(image)
        predictions = np.asarray(
            modele.predict(np.expand_dims(tableau, axis=0), verbose=0)
        )[0]
        classe = CLASSES[int(np.argmax(predictions))]
        return {
            "categorie": MAPPING_COULEUR[classe],
            "confiance": round(float(np.max(predictions)), 4),
        }

    return predire


def analyser(ligne: dict, predicteur=predire_categorie) -> dict:
    chemin = Path(ligne["fichier"])
    resultat = {
        "type_image": ligne["type_image"],
        "fichier": str(chemin),
        "nom": ligne["nom"],
        "poubelle_attendue": ligne["attendue"],
        "poubelle_modele_direct": "",
        "confiance_modele_direct": "",
        "poubelle_application": "",
        "source_application": "",
        "confiance_application": "",
        "modele_correct": "",
        "application_correcte": "",
        "erreur": "",
    }

    if not chemin.is_file():
        resultat["erreur"] = "Image introuvable"
        return resultat

    try:
        direct = predicteur(str(chemin))
        resultat["poubelle_modele_direct"] = direct["categorie"]
        resultat["confiance_modele_direct"] = direct["confiance"]
        resultat["modele_correct"] = (
            direct["categorie"] == ligne["attendue"]
        )
    except Exception as erreur:
        resultat["erreur"] = (
            f"Modèle direct — {type(erreur).__name__}: {erreur}"
        )

    produit = {
        "nom": ligne["nom"],
        "mot_cle": ligne.get("mot_cle", ""),
        "categorie_jumia": ligne["categorie_jumia"],
        "image_url": "",
    }
    decision = determiner_verdict(produit, chemin_image=str(chemin))
    resultat["poubelle_application"] = decision["categorie"]
    resultat["source_application"] = decision["source"]
    resultat["confiance_application"] = (
        "" if decision["confiance"] is None else decision["confiance"]
    )
    resultat["application_correcte"] = (
        decision["categorie"] == ligne["attendue"]
    )
    if decision["erreur"]:
        resultat["erreur"] = (
            f"{resultat['erreur']} | " if resultat["erreur"] else ""
        ) + f"Application — {decision['erreur']}"
    return resultat


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        required=True,
        help="Dossier test contenant les six sous-dossiers de classes.",
    )
    parser.add_argument(
        "--jumia-csv",
        type=Path,
        required=True,
        help="CSV des images Jumia annotées.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("diagnostic/resultats.csv"),
    )
    parser.add_argument(
        "--modele-direct",
        type=Path,
        help=(
            "Modèle candidat facultatif pour la colonne modèle direct. "
            "L'application continue d'utiliser le modèle déployé."
        ),
    )
    parser.add_argument("--nombre", type=int, default=10)
    args = parser.parse_args()

    entrees = choisir_images_dataset(args.dataset_dir, args.nombre)
    entrees += lire_images_jumia(args.jumia_csv, args.nombre)
    predicteur = creer_predicteur(args.modele_direct)
    resultats = [
        analyser(entree, predicteur=predicteur)
        for entree in entrees
    ]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as fichier:
        writer = csv.DictWriter(fichier, fieldnames=resultats[0].keys())
        writer.writeheader()
        writer.writerows(resultats)

    print(f"Rapport écrit dans : {args.output.resolve()}")
    for type_image in ("dataset", "jumia"):
        groupe = [
            resultat
            for resultat in resultats
            if resultat["type_image"] == type_image
        ]
        valides = [resultat for resultat in groupe if not resultat["erreur"]]
        modele_ok = sum(
            resultat["modele_correct"] is True for resultat in valides
        )
        app_ok = sum(
            resultat["application_correcte"] is True
            for resultat in valides
        )
        print(
            f"{type_image.capitalize()} — modèle : "
            f"{modele_ok}/{len(valides)} ; application : "
            f"{app_ok}/{len(valides)}"
        )

    erreurs = sum(bool(resultat["erreur"]) for resultat in resultats)
    print(f"Erreurs techniques : {erreurs}")


if __name__ == "__main__":
    main()

