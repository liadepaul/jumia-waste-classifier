"""Évalue le CNN EcoSort sur un jeu de test indépendant.

Le script utilise uniquement TensorFlow et NumPy, déjà nécessaires au modèle.
Il produit un rapport JSON et une matrice de confusion CSV reproductibles.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
import tensorflow as tf


TAILLE_IMAGE = (224, 224)
BATCH_SIZE = 32
CLASSES = ["cardboard", "glass", "metal", "paper", "plastic", "trash"]


def calculer_metriques(matrice: np.ndarray) -> dict:
    """Calcule les métriques globales et par classe depuis une matrice."""
    matrice = np.asarray(matrice, dtype=np.int64)
    forme_attendue = (len(CLASSES), len(CLASSES))
    if matrice.shape != forme_attendue:
        raise ValueError(
            f"Matrice de forme {matrice.shape}, attendu {forme_attendue}."
        )
    if np.any(matrice < 0):
        raise ValueError("La matrice de confusion contient une valeur négative.")

    total = int(matrice.sum())
    if total == 0:
        raise ValueError("La matrice de confusion est vide.")

    vrais_positifs = np.diag(matrice).astype(float)
    predits = matrice.sum(axis=0).astype(float)
    reels = matrice.sum(axis=1).astype(float)

    precision = np.divide(
        vrais_positifs,
        predits,
        out=np.zeros_like(vrais_positifs),
        where=predits != 0,
    )
    rappel = np.divide(
        vrais_positifs,
        reels,
        out=np.zeros_like(vrais_positifs),
        where=reels != 0,
    )
    f1 = np.divide(
        2 * precision * rappel,
        precision + rappel,
        out=np.zeros_like(vrais_positifs),
        where=(precision + rappel) != 0,
    )

    par_classe = {}
    for index, classe in enumerate(CLASSES):
        par_classe[classe] = {
            "precision": round(float(precision[index]), 4),
            "rappel": round(float(rappel[index]), 4),
            "f1": round(float(f1[index]), 4),
            "support": int(reels[index]),
        }

    return {
        "nombre_images": total,
        "nombre_correct": int(vrais_positifs.sum()),
        "accuracy": round(float(vrais_positifs.sum() / total), 4),
        "macro_precision": round(float(precision.mean()), 4),
        "macro_rappel": round(float(rappel.mean()), 4),
        "macro_f1": round(float(f1.mean()), 4),
        "par_classe": par_classe,
    }


def construire_matrice(
    y_vrai: np.ndarray,
    y_predit: np.ndarray,
) -> np.ndarray:
    """Construit la matrice sans dépendre de scikit-learn."""
    matrice = np.zeros((len(CLASSES), len(CLASSES)), dtype=np.int64)
    for vraie, predite in zip(y_vrai, y_predit, strict=True):
        matrice[int(vraie), int(predite)] += 1
    return matrice


def sauvegarder_matrice(matrice: np.ndarray, chemin: Path) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with chemin.open("w", encoding="utf-8-sig", newline="") as fichier:
        writer = csv.writer(fichier)
        writer.writerow(["classe_reelle", *CLASSES])
        for classe, ligne in zip(CLASSES, matrice, strict=True):
            writer.writerow([classe, *[int(valeur) for valeur in ligne]])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=Path("data/split/test"),
        help="Dossier test contenant les six sous-dossiers de classes.",
    )
    parser.add_argument(
        "--modele",
        type=Path,
        default=Path("model/modele_eco_sort.h5"),
    )
    parser.add_argument(
        "--rapport",
        type=Path,
        default=Path("diagnostic/evaluation_modele.json"),
    )
    parser.add_argument(
        "--matrice",
        type=Path,
        default=Path("diagnostic/matrice_confusion.csv"),
    )
    args = parser.parse_args()

    if not args.dataset_dir.is_dir():
        parser.error(f"Dataset test introuvable : {args.dataset_dir}")
    if not args.modele.is_file():
        parser.error(f"Modèle introuvable : {args.modele}")

    dataset = tf.keras.utils.image_dataset_from_directory(
        args.dataset_dir,
        labels="inferred",
        label_mode="categorical",
        class_names=CLASSES,
        image_size=TAILLE_IMAGE,
        batch_size=BATCH_SIZE,
        shuffle=False,
    )
    modele = tf.keras.models.load_model(args.modele)

    y_vrai = []
    y_predit = []
    for images, etiquettes in dataset:
        predictions = np.asarray(modele.predict(images, verbose=0))
        y_vrai.extend(np.argmax(etiquettes.numpy(), axis=1))
        y_predit.extend(np.argmax(predictions, axis=1))

    matrice = construire_matrice(
        np.asarray(y_vrai),
        np.asarray(y_predit),
    )
    rapport = calculer_metriques(matrice)
    rapport["classes"] = CLASSES
    rapport["dataset"] = str(args.dataset_dir.resolve())
    rapport["modele"] = str(args.modele.resolve())

    args.rapport.parent.mkdir(parents=True, exist_ok=True)
    args.rapport.write_text(
        json.dumps(rapport, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    sauvegarder_matrice(matrice, args.matrice)

    print(f"Images : {rapport['nombre_images']}")
    print(f"Accuracy : {rapport['accuracy']:.2%}")
    print(f"Macro F1 : {rapport['macro_f1']:.2%}")
    print(f"Macro rappel : {rapport['macro_rappel']:.2%}")
    for classe, valeurs in rapport["par_classe"].items():
        print(
            f"{classe:9s} "
            f"precision={valeurs['precision']:.3f} "
            f"rappel={valeurs['rappel']:.3f} "
            f"f1={valeurs['f1']:.3f} "
            f"support={valeurs['support']}"
        )
    print(f"Rapport : {args.rapport.resolve()}")
    print(f"Matrice : {args.matrice.resolve()}")


if __name__ == "__main__":
    main()
