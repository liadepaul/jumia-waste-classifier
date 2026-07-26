"""Constitue les 25 candidats du holdout final avant contrôle visuel."""

from __future__ import annotations

import argparse
import csv
import sys
import unicodedata
from collections import Counter
from pathlib import Path

RACINE_PROJET = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE_PROJET))

from diagnostic.collecter_benchmark_jumia import (
    lire_liens_exclus,
    telecharger,
)
from scraper.jumia_scraper import chercher_produits


CIBLES = [
    ("jaune", "shampoing 300ml", "shampooing"),
    ("jaune", "shampoing 300ml", "shampooing"),
    ("jaune", "gel douche flacon", "flacon"),
    ("jaune", "gel douche flacon", "flacon"),
    ("jaune", "thon boite conserve", "thon"),
    ("vert", "miel bocal verre", "bocal en verre cassable"),
    ("vert", "parfum flacon verre", "flacons de parfum en verre"),
    ("vert", "cafe bocal verre", "syder bocal de conservation en verre"),
    ("vert", "jus bouteille en verre", "bouteille en verre transparent"),
    ("vert", "huile olive bouteille verre", "bouteille en verre"),
    ("bleu", "livre roman", "roman"),
    ("bleu", "livre roman", "roman"),
    ("bleu", "ramette papier A4", "papier"),
    ("bleu", "ramette papier A4", "papier"),
    ("bleu", "cahier 200 pages", "05 cahiers etudiant"),
    ("gris", "telephone tecno", "tecno"),
    ("gris", "chargeur telephone", "chargeur"),
    ("gris", "ecouteurs filaires", "ecouteur"),
    ("gris", "mixeur electrique", "mixeur"),
    ("gris", "montre connectee", "montre connectee"),
    ("marron", "assiette ceramique", "assiette"),
    ("marron", "assiette ceramique", "assiette"),
    ("marron", "tasse ceramique", "tasse"),
    ("marron", "tasse ceramique", "tasse"),
    ("marron", "peigne bois naturel", "peigne de massage cranien"),
]


def normaliser(texte: str) -> str:
    decompose = unicodedata.normalize("NFKD", texte.lower())
    return "".join(
        caractere
        for caractere in decompose
        if not unicodedata.combining(caractere)
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--images-dir",
        type=Path,
        default=Path("diagnostic/images_holdout_jumia"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("diagnostic/holdout_jumia.csv"),
    )
    parser.add_argument(
        "--exclure-csv",
        action="append",
        type=Path,
        default=[],
    )
    parser.add_argument("--timeout", type=int, default=20)
    args = parser.parse_args()

    args.images_dir.mkdir(parents=True, exist_ok=True)
    liens_vus = lire_liens_exclus(args.exclure_csv)
    resultats_recherche = {}
    lignes = []
    compteurs = Counter()

    for poubelle, recherche, fragment in CIBLES:
        if recherche not in resultats_recherche:
            resultats_recherche[recherche] = chercher_produits(
                recherche,
                max_resultats=10,
                timeout=args.timeout,
            )

        fragment_normalise = normaliser(fragment)
        produit = next(
            (
                candidat
                for candidat in resultats_recherche[recherche]
                if candidat["lien"] not in liens_vus
                if fragment_normalise in normaliser(candidat["nom"])
            ),
            None,
        )
        if produit is None:
            raise RuntimeError(
                f"Aucun candidat inédit pour {recherche!r} / {fragment!r}"
            )

        liens_vus.add(produit["lien"])
        compteurs[poubelle] += 1
        nom_fichier = f"{poubelle}_{compteurs[poubelle]:02d}.jpg"
        chemin_image = args.images_dir / nom_fichier
        telecharger(produit["image_url"], chemin_image, args.timeout)
        lignes.append(
            {
                "fichier": str(Path(args.images_dir.name) / nom_fichier),
                "nom": produit["nom"],
                "recherche": recherche,
                "poubelle_attendue": poubelle,
                "categorie_jumia": "",
                "lien": produit["lien"],
                "image_url": produit["image_url"],
                "statut_annotation": "a_verifier",
                "justification": "",
            }
        )

    if set(compteurs.values()) != {5} or len(compteurs) != 5:
        raise RuntimeError(f"Holdout déséquilibré : {dict(compteurs)}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as fichier:
        writer = csv.DictWriter(fichier, fieldnames=lignes[0].keys())
        writer.writeheader()
        writer.writerows(lignes)

    print(f"Holdout candidat : {len(lignes)} produits")
    print(dict(sorted(compteurs.items())))
    print(f"Fichier : {args.output.resolve()}")


if __name__ == "__main__":
    main()
