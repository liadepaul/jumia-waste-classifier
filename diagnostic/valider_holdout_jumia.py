"""Fige les annotations du holdout après le contrôle visuel."""

from __future__ import annotations

import argparse
import csv
import hashlib
from collections import Counter
from pathlib import Path


JUSTIFICATIONS = {
    "jaune": "Emballage léger en plastique ou en métal.",
    "vert": "Bouteille, pot ou flacon explicitement en verre.",
    "bleu": "Livre, cahier ou papier graphique propre.",
    "gris": "Équipement électrique ou électronique.",
    "marron": "Vaisselle ou objet hors des filières indiquées.",
}


def empreinte(chemin: Path) -> str:
    hachage = hashlib.sha256()
    with chemin.open("rb") as fichier:
        for bloc in iter(lambda: fichier.read(64 * 1024), b""):
            hachage.update(bloc)
    return hachage.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_holdout", type=Path)
    parser.add_argument(
        "--exclure-csv",
        action="append",
        type=Path,
        default=[],
    )
    args = parser.parse_args()

    with args.csv_holdout.open(encoding="utf-8-sig", newline="") as fichier:
        lignes = list(csv.DictReader(fichier))

    comptes = Counter(ligne["poubelle_attendue"] for ligne in lignes)
    if set(comptes.values()) != {5} or len(comptes) != 5:
        raise ValueError(f"Holdout déséquilibré : {dict(comptes)}")

    liens = [ligne["lien"] for ligne in lignes]
    if len(set(liens)) != len(liens):
        raise ValueError("Le holdout contient un lien dupliqué.")

    liens_exclus = set()
    for chemin_csv in args.exclure_csv:
        with chemin_csv.open(encoding="utf-8-sig", newline="") as fichier:
            liens_exclus.update(
                ligne["lien"]
                for ligne in csv.DictReader(fichier)
                if ligne.get("lien")
            )
    chevauchements = set(liens) & liens_exclus
    if chevauchements:
        raise ValueError(
            f"{len(chevauchements)} lien(s) déjà utilisé(s)."
        )

    empreintes = []
    for ligne in lignes:
        chemin_image = Path(ligne["fichier"])
        if not chemin_image.is_absolute():
            chemin_image = args.csv_holdout.parent / chemin_image
        if not chemin_image.is_file():
            raise FileNotFoundError(f"Image absente : {chemin_image}")
        empreintes.append(empreinte(chemin_image))
        ligne["statut_annotation"] = "validee"
        ligne["justification"] = JUSTIFICATIONS[ligne["poubelle_attendue"]]

    if len(set(empreintes)) != len(empreintes):
        raise ValueError("Le holdout contient une image dupliquée.")

    with args.csv_holdout.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as fichier:
        writer = csv.DictWriter(fichier, fieldnames=lignes[0].keys())
        writer.writeheader()
        writer.writerows(lignes)

    print(f"Holdout figé : {len(lignes)} produits")
    print(dict(sorted(comptes.items())))
    print("Chevauchements : 0")
    print("Doublons exacts : 0")


if __name__ == "__main__":
    main()
