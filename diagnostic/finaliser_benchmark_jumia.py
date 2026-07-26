"""Finalise les annotations contrôlées du benchmark Jumia."""

from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

import requests

RACINE_PROJET = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE_PROJET))

from scraper.jumia_scraper import HEADERS


CSV_BENCHMARK = Path("diagnostic/benchmark_jumia.csv")
IMAGES_DIR = Path("diagnostic/images_benchmark_jumia")

JUSTIFICATIONS = {
    "jaune": "Emballage léger en plastique ou en métal.",
    "vert": "Bouteille ou bocal d'emballage en verre.",
    "bleu": "Cahier, carnet ou enveloppe en papier propre.",
    "gris": "Équipement électrique ou électronique.",
    "marron": "Vaisselle ou objet hors des filières de recyclage indiquées.",
}

REMPLACEMENTS = [
    {
        "poubelle": "jaune",
        "recherche": "shampooing",
        "nom": "Garnier Shampoing Ultra Doux Avocat Karité 300Ml",
        "image_url": "https://ci.jumia.is/unsafe/fit-in/300x300/filters:fill(white)/product/75/173913/1.jpg?4862",
        "lien": "https://www.jumia.ci/garnier-shampoing-ultra-doux-avocat-karite-300ml-31937157.html",
    },
    {
        "poubelle": "jaune",
        "recherche": "shampooing",
        "nom": "Garnier Après-Shampooing Reconstituant Trésors de Miel 250 ML",
        "image_url": "https://ci.jumia.is/unsafe/fit-in/300x300/filters:fill(white)/product/16/173913/1.jpg?1199",
        "lien": "https://www.jumia.ci/garnier-apres-shampooing-reconstituant-tresors-de-miel-250-ml-31937161.html",
    },
    {
        "poubelle": "jaune",
        "recherche": "shampooing",
        "nom": "Garnier Shampoing Ultra Doux Abricot Disney 300Ml",
        "image_url": "https://ci.jumia.is/unsafe/fit-in/300x300/filters:fill(white)/product/85/173913/1.jpg?5587",
        "lien": "https://www.jumia.ci/garnier-shampoing-ultra-doux-abricot-disney-300ml-31937158.html",
    },
    {
        "poubelle": "jaune",
        "recherche": "shampooing",
        "nom": "Shampoing colorant noircissant à l’huile argan 400ML",
        "image_url": "https://ci.jumia.is/unsafe/fit-in/300x300/filters:fill(white)/product/21/695903/1.jpg?6398",
        "lien": "https://www.jumia.ci/generic-shampoing-colorant-noircissant-a-lhuile-argan-400ml-de-noiressence-30959612.html",
    },
    {
        "poubelle": "jaune",
        "recherche": "shampooing",
        "nom": "Garnier Shampooing Ultra Doux 250Ml Charbon",
        "image_url": "https://ci.jumia.is/unsafe/fit-in/300x300/filters:fill(white)/product/99/803913/1.jpg?8243",
        "lien": "https://www.jumia.ci/garnier-shampooing-ultra-doux-250ml-charbon-31930899.html",
    },
    {
        "poubelle": "vert",
        "recherche": "bocal conserve verre",
        "nom": "Boîte à Café Hermétique, Bocal de Stockage en Verre 500ml",
        "image_url": "https://ci.jumia.is/unsafe/fit-in/300x300/filters:fill(white)/product/61/103123/1.jpg?9584",
        "lien": "https://www.jumia.ci/generic-boite-a-cafe-hermetique-500ml-bocaux-de-stockage-en-verre-bocal-a-cafe-sous-vide-resistant-lhumidite-et-loxydation-32130116.html",
    },
    {
        "poubelle": "vert",
        "recherche": "bocal conserve verre",
        "nom": "Ensemble de 4 Bocaux en Verre Texturé Syder",
        "image_url": "https://ci.jumia.is/unsafe/fit-in/300x300/filters:fill(white)/product/96/428323/1.jpg?0461",
        "lien": "https://www.jumia.ci/generic-ensemble-de-4-bocaux-en-verre-texture-syder-lalliance-parfaite-du-charme-et-de-lorganisation-32382469.html",
    },
    {
        "poubelle": "bleu",
        "recherche": "cahier scolaire",
        "nom": "Carnet d'école et bureau, paquet de 10",
        "image_url": "https://ci.jumia.is/unsafe/fit-in/300x300/filters:fill(white)/product/14/878813/1.jpg?3172",
        "lien": "https://www.jumia.ci/generic-carnet-decole-et-bureau-paquet-de-10-31887841.html",
    },
    {
        "poubelle": "bleu",
        "recherche": "cahier scolaire",
        "nom": "Carnet secret Miraculous",
        "image_url": "https://ci.jumia.is/unsafe/fit-in/300x300/filters:fill(white)/product/22/210423/1.jpg?8602",
        "lien": "https://www.jumia.ci/generic-carnet-secret-miraculous-32401222.html",
    },
    {
        "poubelle": "bleu",
        "recherche": "papier A4",
        "nom": "Bloc-notes A4, 4 pièces, Budget Planner",
        "image_url": "https://ci.jumia.is/unsafe/fit-in/300x300/filters:fill(white)/product/43/800792/1.jpg?4449",
        "lien": "https://www.jumia.ci/generic-bloc-notes-a4-4-piecesbudget-planner-29700834.html",
    },
    {
        "poubelle": "bleu",
        "recherche": "enveloppe blanche",
        "nom": "25 Enveloppes A6 Auto-Adhésives Blanches",
        "image_url": "https://ci.jumia.is/unsafe/fit-in/300x300/filters:fill(white)/product/55/896813/1.jpg?8954",
        "lien": "https://www.jumia.ci/generic-25-enveloppes-a6-auto-adhesives-blanches-paquet-de-25-31869855.html",
    },
    {
        "poubelle": "bleu",
        "recherche": "cahier",
        "nom": "Bloc-notes Papier Kraft, Mini Cahier à Spirale",
        "image_url": "https://ci.jumia.is/unsafe/fit-in/300x300/filters:fill(white)/product/63/903403/1.jpg?2119",
        "lien": "https://www.jumia.ci/generic-bloc-notes-papier-kraft-inspirant-mini-cahier-a-spirale-et-stylo-a-bille-30430936.html",
    },
    {
        "poubelle": "marron",
        "recherche": "assiette céramique",
        "nom": "Lot de 10 Assiettes en Céramique",
        "image_url": "https://ci.jumia.is/unsafe/fit-in/300x300/filters:fill(white)/product/54/822202/1.jpg?4742",
        "lien": "https://www.jumia.ci/assiette-lot-de-10-assiettes-en-ceramique-20222845.html",
    },
]


def telecharger(url: str, destination: Path) -> None:
    reponse = requests.get(url, headers=HEADERS, timeout=20)
    reponse.raise_for_status()
    if not reponse.headers.get("Content-Type", "").lower().startswith("image/"):
        raise ValueError(f"Réponse non image pour {url}")
    destination.write_bytes(reponse.content)


def main() -> None:
    with CSV_BENCHMARK.open(encoding="utf-8-sig", newline="") as fichier:
        lignes = [
            ligne
            for ligne in csv.DictReader(fichier)
            if "_remplacement_" not in Path(ligne["fichier"]).name
            if (IMAGES_DIR / Path(ligne["fichier"]).name).is_file()
        ]

    for chemin in IMAGES_DIR.glob("*_remplacement_*.jpg"):
        chemin.unlink()

    compteurs = Counter(ligne["poubelle_attendue"] for ligne in lignes)
    for index, remplacement in enumerate(REMPLACEMENTS, 1):
        poubelle = remplacement["poubelle"]
        compteurs[poubelle] += 1
        nom_fichier = f"{poubelle}_remplacement_{index:02d}.jpg"
        chemin = IMAGES_DIR / nom_fichier
        telecharger(remplacement["image_url"], chemin)
        lignes.append(
            {
                "fichier": str(Path(IMAGES_DIR.name) / nom_fichier),
                "nom": remplacement["nom"],
                "recherche": remplacement["recherche"],
                "poubelle_attendue": poubelle,
                "categorie_jumia": "",
                "lien": remplacement["lien"],
                "image_url": remplacement["image_url"],
                "statut_annotation": "validee",
                "justification": JUSTIFICATIONS[poubelle],
            }
        )

    for ligne in lignes:
        ligne["statut_annotation"] = "validee"
        ligne["justification"] = JUSTIFICATIONS[ligne["poubelle_attendue"]]

    comptes = Counter(ligne["poubelle_attendue"] for ligne in lignes)
    if set(comptes.values()) != {10} or len(comptes) != 5:
        raise ValueError(f"Benchmark déséquilibré : {dict(comptes)}")
    if len({ligne["lien"] for ligne in lignes}) != len(lignes):
        raise ValueError("Le benchmark contient un lien produit dupliqué.")

    with CSV_BENCHMARK.open("w", encoding="utf-8-sig", newline="") as fichier:
        writer = csv.DictWriter(fichier, fieldnames=lignes[0].keys())
        writer.writeheader()
        writer.writerows(lignes)

    print(f"Benchmark final : {len(lignes)} produits")
    print(dict(sorted(comptes.items())))


if __name__ == "__main__":
    main()
