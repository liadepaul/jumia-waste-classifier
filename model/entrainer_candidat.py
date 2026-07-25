"""Entraîne un modèle candidat sans écraser le modèle EcoSort actuel."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models


CLASSES = ["cardboard", "glass", "metal", "paper", "plastic", "trash"]
TAILLE_IMAGE = (224, 224)


def compter_images(racine: Path) -> dict[str, int]:
    """Compte les images de chaque classe et vérifie la structure."""
    extensions = {".jpg", ".jpeg", ".png", ".webp"}
    comptes = {}
    for classe in CLASSES:
        dossier = racine / classe
        if not dossier.is_dir():
            raise FileNotFoundError(f"Classe absente : {dossier}")
        comptes[classe] = sum(
            fichier.is_file() and fichier.suffix.lower() in extensions
            for fichier in dossier.iterdir()
        )
        if comptes[classe] == 0:
            raise ValueError(f"Classe vide : {dossier}")
    return comptes


def calculer_poids_classes(comptes: dict[str, int]) -> dict[int, float]:
    """Compense le déséquilibre sans changer artificiellement le dataset."""
    total = sum(comptes.values())
    return {
        index: total / (len(CLASSES) * comptes[classe])
        for index, classe in enumerate(CLASSES)
    }


def creer_modele() -> tuple[tf.keras.Model, tf.keras.Model]:
    """Construit le MobileNetV2 candidat."""
    base = tf.keras.applications.MobileNetV2(
        input_shape=TAILLE_IMAGE + (3,),
        include_top=False,
        weights="imagenet",
    )
    base.trainable = False

    augmentation = tf.keras.Sequential(
        [
            layers.RandomFlip("horizontal"),
            layers.RandomRotation(0.12),
            layers.RandomZoom(0.15),
            layers.RandomContrast(0.15),
        ],
        name="augmentation",
    )

    entrees = tf.keras.Input(shape=TAILLE_IMAGE + (3,))
    x = augmentation(entrees)
    x = layers.Rescaling(
        scale=1.0 / 127.5,
        offset=-1,
        name="preprocessing",
    )(x)
    x = base(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.35)(x)
    sorties = layers.Dense(len(CLASSES), activation="softmax")(x)
    return models.Model(entrees, sorties), base


def compiler(modele: tf.keras.Model, taux: float) -> None:
    modele.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=taux),
        loss=tf.keras.losses.CategoricalCrossentropy(label_smoothing=0.05),
        metrics=["accuracy"],
    )


def callbacks(
    chemin_modele: Path,
    chemin_journal: Path,
    seuil_initial: float | None = None,
) -> list[tf.keras.callbacks.Callback]:
    return [
        tf.keras.callbacks.CSVLogger(
            chemin_journal,
            append=False,
        ),
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=5,
            restore_best_weights=True,
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.3,
            patience=2,
            min_lr=1e-7,
        ),
        tf.keras.callbacks.ModelCheckpoint(
            chemin_modele,
            monitor="val_loss",
            save_best_only=True,
            initial_value_threshold=seuil_initial,
        ),
    ]


def fusionner_historiques(*historiques) -> dict[str, list[float]]:
    cles = historiques[0].history.keys()
    return {
        cle: [
            float(valeur)
            for historique in historiques
            for valeur in historique.history[cle]
        ]
        for cle in cles
    }


def sauvegarder_historique(
    chemin: Path,
    historique: dict[str, list[float]],
) -> None:
    """Écrit les métriques immédiatement après chaque phase."""
    chemin.write_text(
        json.dumps(historique, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-dir",
        type=Path,
        required=True,
        help="Dossier contenant train/ et validation/.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("model/candidats"),
    )
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--epochs-tete", type=int, default=25)
    parser.add_argument("--epochs-finetuning", type=int, default=15)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if args.batch_size <= 0:
        parser.error("--batch-size doit être positif.")
    if args.epochs_tete <= 0 or args.epochs_finetuning <= 0:
        parser.error("Le nombre d’époques doit être positif.")

    train_dir = args.data_dir / "train"
    validation_dir = args.data_dir / "validation"
    comptes_train = compter_images(train_dir)
    comptes_validation = compter_images(validation_dir)
    poids = calculer_poids_classes(comptes_train)

    random.seed(args.seed)
    np.random.seed(args.seed)
    tf.random.set_seed(args.seed)

    train = tf.keras.utils.image_dataset_from_directory(
        train_dir,
        labels="inferred",
        label_mode="categorical",
        class_names=CLASSES,
        image_size=TAILLE_IMAGE,
        batch_size=args.batch_size,
        shuffle=True,
        seed=args.seed,
    )
    validation = tf.keras.utils.image_dataset_from_directory(
        validation_dir,
        labels="inferred",
        label_mode="categorical",
        class_names=CLASSES,
        image_size=TAILLE_IMAGE,
        batch_size=args.batch_size,
        shuffle=False,
    )
    train = train.prefetch(tf.data.AUTOTUNE)
    validation = validation.prefetch(tf.data.AUTOTUNE)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    chemin_modele = args.output_dir / "modele_candidat.keras"

    modele, base = creer_modele()
    compiler(modele, 1e-3)
    historique_tete = modele.fit(
        train,
        validation_data=validation,
        epochs=args.epochs_tete,
        class_weight=poids,
        callbacks=callbacks(
            chemin_modele,
            args.output_dir / "journal_tete.csv",
        ),
        verbose=2,
    )

    sauvegarder_historique(
        args.output_dir / "historique_tete.json",
        fusionner_historiques(historique_tete),
    )
    meilleure_val_loss_tete = min(historique_tete.history["val_loss"])
    base.trainable = True
    for couche in base.layers[:-30]:
        couche.trainable = False
    compiler(modele, 1e-5)
    historique_finetuning = modele.fit(
        train,
        validation_data=validation,
        epochs=args.epochs_finetuning,
        class_weight=poids,
        callbacks=callbacks(
            chemin_modele,
            args.output_dir / "journal_finetuning.csv",
            meilleure_val_loss_tete,
        ),
        verbose=2,
    )

    historique = fusionner_historiques(
        historique_tete,
        historique_finetuning,
    )
    resume = {
        "classes": CLASSES,
        "seed": args.seed,
        "batch_size": args.batch_size,
        "comptes_train": comptes_train,
        "comptes_validation": comptes_validation,
        "poids_classes": {
            CLASSES[index]: round(float(valeur), 4)
            for index, valeur in poids.items()
        },
        "historique": historique,
    }
    (args.output_dir / "historique_candidat.json").write_text(
        json.dumps(resume, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Modèle candidat : {chemin_modele.resolve()}")


if __name__ == "__main__":
    main()
