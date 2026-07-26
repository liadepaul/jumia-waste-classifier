"""Evalue le CNN et l'application hybride sur l'echantillon Jumia annote
du groupe (83 produits, data/echantillon_jumia/echantillon_brut.json).

Cette evaluation est complementaire : elle ne remplace ni le test Kaggle
(383 images), ni le benchmark de developpement (50 produits), ni le
holdout independant (25 produits). Plusieurs produits de l'echantillon de
83 recoupent ces jeux precedents ; ce script les identifie par comparaison
exacte des liens, il ne les recopie pas depuis une source externe.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from app.app import determiner_verdict, telecharger_image  # noqa: E402
from model.predict import predire_categorie  # noqa: E402

CATEGORIES_CINQ = ["jaune", "vert", "bleu", "gris", "marron"]
CATEGORIES_CNN = ["jaune", "vert", "bleu", "marron"]


def charger_echantillon(chemin: Path) -> list[dict]:
    with chemin.open(encoding="utf-8") as fichier:
        return json.load(fichier)


def charger_liens_csv(chemin_csv: Path) -> set[str]:
    if not chemin_csv.is_file():
        return set()
    with chemin_csv.open(encoding="utf-8-sig", newline="") as fichier:
        return {
            ligne["lien"].strip()
            for ligne in csv.DictReader(fichier)
            if ligne.get("lien")
        }


def repartir(
    echantillon: list[dict],
    liens_benchmark: set[str],
    liens_holdout: set[str],
) -> dict[str, list[dict]]:
    """Separe l'echantillon en categories exclusion/inclusion, sans jamais
    modifier les entrees d'origine."""
    aucune = [
        p for p in echantillon
        if p.get("categorie_validee_manuellement") == "aucune"
    ]
    classables = [
        p for p in echantillon
        if p.get("categorie_validee_manuellement") != "aucune"
    ]
    deja_vus = [
        p for p in classables
        if (p.get("lien") or "").strip() in liens_benchmark
        or (p.get("lien") or "").strip() in liens_holdout
    ]
    liens_deja_vus = {(p.get("lien") or "").strip() for p in deja_vus}
    nouveaux = [
        p for p in classables
        if (p.get("lien") or "").strip() not in liens_deja_vus
    ]
    return {
        "aucune": aucune,
        "classables": classables,
        "deja_vus": deja_vus,
        "nouveaux": nouveaux,
    }


def produit_pour_application(entree: dict) -> dict:
    """Convertit une entree du JSON de B au format attendu par
    determiner_verdict(), sans jamais modifier l'entree d'origine."""
    return {
        "nom": entree.get("nom") or "",
        "mot_cle": entree.get("mot_cle_recherche") or "",
        "categorie_jumia": entree.get("categorie_jumia") or "",
        "image_url": entree.get("image_url") or "",
    }


def evaluer_hybride(entrees: list[dict], deja_vus_liens: set[str]) -> list[dict]:
    """Fait passer chaque produit par la logique complete de l'application
    (determiner_verdict), qui telecharge et supprime elle-meme l'image."""
    resultats = []
    for entree in entrees:
        attendue = entree.get("categorie_validee_manuellement")
        lien = (entree.get("lien") or "").strip()
        decision = determiner_verdict(produit_pour_application(entree))
        resultats.append(
            {
                "nom": entree.get("nom"),
                "lien": lien,
                "categorie_attendue": attendue,
                "verdict_application": decision["categorie"],
                "source_verdict": decision["source"],
                "confiance_ia": decision["confiance"],
                "erreur_technique": decision["erreur"] or "",
                "application_correcte": decision["categorie"] == attendue,
                "statut": "deja_vu" if lien in deja_vus_liens else "nouveau",
            }
        )
    return resultats


def evaluer_cnn_direct(entrees: list[dict]) -> list[dict]:
    """Evalue uniquement le CNN, image par image, sur les produits qui ne
    sont pas des D3E (le CNN n'a pas de sortie D3E)."""
    resultats = []
    for entree in entrees:
        attendue = entree.get("categorie_validee_manuellement")
        if attendue == "gris":
            continue

        ligne = {
            "nom": entree.get("nom"),
            "lien": (entree.get("lien") or "").strip(),
            "categorie_attendue": attendue,
            "verdict_cnn": None,
            "confiance_cnn": None,
            "erreur_technique": "",
        }
        chemin_local: str | None = None
        try:
            chemin_local = telecharger_image(entree.get("image_url") or "")
            direct = predire_categorie(chemin_local)
            ligne["verdict_cnn"] = direct["categorie"]
            ligne["confiance_cnn"] = direct["confiance"]
        except Exception as erreur:
            ligne["erreur_technique"] = f"{type(erreur).__name__}: {erreur}"
        finally:
            if chemin_local:
                Path(chemin_local).unlink(missing_ok=True)

        ligne["cnn_correct"] = (
            ligne["verdict_cnn"] == attendue
            if not ligne["erreur_technique"]
            else None
        )
        resultats.append(ligne)
    return resultats


def matrice_confusion(paires: list[tuple[str, str]], classes: list[str]) -> dict:
    matrice = {attendue: {predite: 0 for predite in classes} for attendue in classes}
    for attendue, predite in paires:
        if attendue in matrice and predite in matrice[attendue]:
            matrice[attendue][predite] += 1
    return matrice


def calculer_metriques(paires: list[tuple[str, str]], classes: list[str]) -> dict:
    """paires : liste de (categorie_attendue, categorie_predite), deja
    filtree des erreurs techniques. Ne fait jamais dependre la prediction
    de la valeur attendue : c'est une fonction pure de comparaison."""
    total = len(paires)
    corrects = sum(1 for attendue, predite in paires if attendue == predite)
    accuracy = corrects / total if total else 0.0

    par_classe = {}
    for classe in classes:
        vrai_positif = sum(
            1 for attendue, predite in paires
            if attendue == classe and predite == classe
        )
        faux_positif = sum(
            1 for attendue, predite in paires
            if attendue != classe and predite == classe
        )
        faux_negatif = sum(
            1 for attendue, predite in paires
            if attendue == classe and predite != classe
        )
        support = sum(1 for attendue, _ in paires if attendue == classe)
        precision = (
            vrai_positif / (vrai_positif + faux_positif)
            if (vrai_positif + faux_positif) else 0.0
        )
        rappel = (
            vrai_positif / (vrai_positif + faux_negatif)
            if (vrai_positif + faux_negatif) else 0.0
        )
        f1 = (
            2 * precision * rappel / (precision + rappel)
            if (precision + rappel) else 0.0
        )
        par_classe[classe] = {
            "precision": precision,
            "rappel": rappel,
            "f1": f1,
            "support": support,
        }

    classes_presentes = [c for c in classes if par_classe[c]["support"] > 0]
    macro_f1 = (
        sum(par_classe[c]["f1"] for c in classes_presentes) / len(classes_presentes)
        if classes_presentes else 0.0
    )

    return {
        "total": total,
        "corrects": corrects,
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "par_classe": par_classe,
        "matrice_confusion": matrice_confusion(paires, classes),
    }


def paires_hybride(resultats: list[dict]) -> list[tuple[str, str]]:
    return [
        (r["categorie_attendue"], r["verdict_application"])
        for r in resultats
        if not r["erreur_technique"]
    ]


def paires_cnn(resultats: list[dict]) -> list[tuple[str, str]]:
    return [
        (r["categorie_attendue"], r["verdict_cnn"])
        for r in resultats
        if not r["erreur_technique"] and r["verdict_cnn"] is not None
    ]


def ecrire_csv_details(chemin: Path, lignes: list[dict]) -> None:
    if not lignes:
        return
    chemin.parent.mkdir(parents=True, exist_ok=True)
    champs = sorted({cle for ligne in lignes for cle in ligne})
    with chemin.open("w", encoding="utf-8-sig", newline="") as fichier:
        writer = csv.DictWriter(fichier, fieldnames=champs)
        writer.writeheader()
        writer.writerows(lignes)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--echantillon",
        type=Path,
        default=RACINE / "data" / "echantillon_jumia" / "echantillon_brut.json",
    )
    parser.add_argument(
        "--benchmark-csv",
        type=Path,
        default=RACINE / "diagnostic" / "benchmark_jumia.csv",
    )
    parser.add_argument(
        "--holdout-csv",
        type=Path,
        default=RACINE / "diagnostic" / "holdout_jumia.csv",
    )
    parser.add_argument(
        "--sortie-dir",
        type=Path,
        default=RACINE / "diagnostic",
        help="Dossier de sortie pour les CSV de details (ignores par Git).",
    )
    args = parser.parse_args()

    echantillon = charger_echantillon(args.echantillon)
    liens_benchmark = charger_liens_csv(args.benchmark_csv)
    liens_holdout = charger_liens_csv(args.holdout_csv)

    groupes = repartir(echantillon, liens_benchmark, liens_holdout)
    liens_deja_vus = {
        (p.get("lien") or "").strip() for p in groupes["deja_vus"]
    }

    print(f"Total echantillon              : {len(echantillon)}")
    print(f"Annotes 'aucune' (exclus)       : {len(groupes['aucune'])}")
    print(f"Classables (5 poubelles)        : {len(groupes['classables'])}")
    print(f"  dont deja vus (benchmark/holdout) : {len(groupes['deja_vus'])}")
    print(f"  dont nouveaux                     : {len(groupes['nouveaux'])}")

    print("\n--- Evaluation A : application hybride sur les classables ---")
    resultats_75 = evaluer_hybride(groupes["classables"], liens_deja_vus)
    metriques_75 = calculer_metriques(paires_hybride(resultats_75), CATEGORIES_CINQ)
    print(
        f"Application (n={metriques_75['total']}) : "
        f"{metriques_75['corrects']}/{metriques_75['total']} "
        f"({metriques_75['accuracy'] * 100:.2f} %), "
        f"macro F1 {metriques_75['macro_f1'] * 100:.2f} %"
    )

    print("\n--- Evaluation B : application hybride sur les nouveaux ---")
    resultats_nouveaux = [
        r for r in resultats_75 if r["statut"] == "nouveau"
    ]
    metriques_62 = calculer_metriques(
        paires_hybride(resultats_nouveaux), CATEGORIES_CINQ
    )
    print(
        f"Application (n={metriques_62['total']}) : "
        f"{metriques_62['corrects']}/{metriques_62['total']} "
        f"({metriques_62['accuracy'] * 100:.2f} %), "
        f"macro F1 {metriques_62['macro_f1'] * 100:.2f} %"
    )

    print("\n--- Evaluation C : CNN direct (hors D3E, hors 'aucune') ---")
    resultats_cnn = evaluer_cnn_direct(groupes["classables"])
    metriques_cnn = calculer_metriques(paires_cnn(resultats_cnn), CATEGORIES_CNN)
    erreurs_cnn = sum(1 for r in resultats_cnn if r["erreur_technique"])
    print(
        f"CNN direct (tentes={len(resultats_cnn)}, "
        f"evalues={metriques_cnn['total']}, erreurs={erreurs_cnn}) : "
        f"{metriques_cnn['corrects']}/{metriques_cnn['total']} "
        f"({metriques_cnn['accuracy'] * 100:.2f} %), "
        f"macro F1 {metriques_cnn['macro_f1'] * 100:.2f} %"
    )

    sources = {}
    for resultat in resultats_75:
        sources[resultat["source_verdict"]] = sources.get(resultat["source_verdict"], 0) + 1
    print(f"\nSources des verdicts (n={len(resultats_75)}) : {sources}")

    args.sortie_dir.mkdir(parents=True, exist_ok=True)
    ecrire_csv_details(
        args.sortie_dir / "resultats_echantillon_groupe_hybride.csv",
        resultats_75,
    )
    ecrire_csv_details(
        args.sortie_dir / "resultats_echantillon_groupe_cnn.csv",
        resultats_cnn,
    )
    print(
        f"\nDetails ecrits dans {args.sortie_dir} "
        "(fichiers ignores par Git)."
    )


if __name__ == "__main__":
    main()
