"""Collecte un benchmark Jumia équilibré à vérifier manuellement."""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

import requests

RACINE_PROJET = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE_PROJET))

from scraper.jumia_scraper import HEADERS, ScrapingError, chercher_produits


PLAN_RECHERCHE = {
    "jaune": [
        "shampooing flacon",
        "boisson canette",
        "bouteille eau minérale",
        "flacon gel douche",
        "bouteille huile cuisine",
        "boîte de conserve",
    ],
    "vert": [
        "bocal en verre",
        "bouteille en verre",
        "pot confiture verre",
        "bocal verre cuisine",
        "pot verre hermétique",
        "bouteille vin verre",
    ],
    "bleu": [
        "cahier",
        "livre papier",
        "enveloppe papier",
    ],
    "gris": [
        "smartphone",
        "chargeur usb",
        "écouteurs bluetooth",
        "ordinateur portable",
        "montre connectée",
        "mixeur électrique",
        "casque audio",
    ],
    "marron": [
        "verre à boire",
        "brosse cheveux",
        "assiette céramique",
        "tasse céramique",
        "peigne cheveux",
        "jouet plastique",
        "miroir",
    ],
}


def telecharger(url: str, destination: Path, timeout: int) -> None:
    reponse = requests.get(
        url,
        headers=HEADERS,
        timeout=timeout,
    )
    reponse.raise_for_status()
    type_contenu = reponse.headers.get("Content-Type", "").lower()
    if not type_contenu.startswith("image/"):
        raise ValueError(f"Contenu inattendu : {type_contenu or 'inconnu'}")
    destination.write_bytes(reponse.content)


def lire_liens_exclus(chemins_csv: list[Path]) -> set[str]:
    """Charge les liens déjà utilisés dans de précédents benchmarks."""
    liens = set()
    for chemin_csv in chemins_csv:
        if not chemin_csv.is_file():
            raise FileNotFoundError(f"CSV à exclure introuvable : {chemin_csv}")
        with chemin_csv.open(encoding="utf-8-sig", newline="") as fichier:
            for ligne in csv.DictReader(fichier):
                if ligne.get("lien"):
                    liens.add(ligne["lien"])
    return liens


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--images-dir",
        type=Path,
        default=Path("diagnostic/images_benchmark_jumia"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("diagnostic/benchmark_jumia.csv"),
    )
    parser.add_argument("--par-categorie", type=int, default=10)
    parser.add_argument(
        "--max-par-recherche",
        type=int,
        default=5,
        help="Limite la concentration de produits issus du même mot-clé.",
    )
    parser.add_argument(
        "--exclure-csv",
        action="append",
        type=Path,
        default=[],
        help="CSV dont les liens produits ne doivent pas être réutilisés.",
    )
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--pause", type=float, default=0.4)
    args = parser.parse_args()

    if args.par_categorie <= 0:
        parser.error("--par-categorie doit être positif.")
    if args.max_par_recherche <= 0:
        parser.error("--max-par-recherche doit être positif.")

    args.images_dir.mkdir(parents=True, exist_ok=True)
    lignes = []
    liens_vus = lire_liens_exclus(args.exclure_csv)

    for poubelle, recherches in PLAN_RECHERCHE.items():
        compteur = 0
        for recherche in recherches:
            if compteur >= args.par_categorie:
                break
            compteur_recherche = 0
            try:
                produits = chercher_produits(
                    recherche,
                    max_resultats=max(5, args.max_par_recherche),
                    timeout=args.timeout,
                )
            except ScrapingError as erreur:
                print(f"{poubelle}/{recherche} : {erreur}")
                continue

            for produit in produits:
                if (
                    compteur >= args.par_categorie
                    or compteur_recherche >= args.max_par_recherche
                ):
                    break
                lien = produit["lien"]
                if lien in liens_vus:
                    continue

                numero = compteur + 1
                nom_fichier = f"{poubelle}_{numero:02d}.jpg"
                chemin_image = args.images_dir / nom_fichier
                try:
                    telecharger(
                        produit["image_url"],
                        chemin_image,
                        args.timeout,
                    )
                except (requests.RequestException, ValueError) as erreur:
                    print(f"Image ignorée pour {produit['nom']!r} : {erreur}")
                    continue

                liens_vus.add(lien)
                compteur += 1
                compteur_recherche += 1
                lignes.append(
                    {
                        "fichier": str(
                            Path(args.images_dir.name) / nom_fichier
                        ),
                        "nom": produit["nom"],
                        "recherche": recherche,
                        "poubelle_attendue": poubelle,
                        "categorie_jumia": "",
                        "lien": lien,
                        "image_url": produit["image_url"],
                        "statut_annotation": "a_verifier",
                        "justification": "",
                    }
                )
                time.sleep(args.pause)

        print(f"{poubelle} : {compteur}/{args.par_categorie} images")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    if not lignes:
        raise SystemExit("Aucun produit n'a pu être collecté.")
    with args.output.open("w", encoding="utf-8-sig", newline="") as fichier:
        writer = csv.DictWriter(fichier, fieldnames=lignes[0].keys())
        writer.writeheader()
        writer.writerows(lignes)

    attendues = args.par_categorie * len(PLAN_RECHERCHE)
    print(f"Benchmark candidat : {len(lignes)}/{attendues}")
    print(f"Fichier : {args.output.resolve()}")
    if len(lignes) != attendues:
        raise SystemExit(
            "Benchmark incomplet : ajouter des recherches ou relancer plus tard."
        )


if __name__ == "__main__":
    main()
