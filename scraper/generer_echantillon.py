"""
Genere un echantillon de produits Jumia a annoter manuellement,
utilise par l'IA pour evaluer le modele sur des donnees reelles
(en complement du dataset Kaggle).
"""
import json
import time

from jumia_scraper import chercher_produits, ScrapingError

MOTS_CLES_PAR_CATEGORIE = {
    "jaune": ["bouteille plastique", "canette boisson", "boite de conserve", "carton emballage"],
    "vert": ["bouteille verre", "pot de confiture", "bocal verre"],
    "bleu": ["journal", "cahier papier", "magazine", "enveloppe papier"],
    "gris": ["smartphone", "chargeur telephone", "ecouteurs", "mixeur electrique"],
    "marron": ["sachet plastique", "produit hygiene", "film plastique"],
}


def generer_echantillon(sortie="data/echantillon_jumia/echantillon_brut.json"):
    echantillon = []

    for categorie_attendue, mots_cles in MOTS_CLES_PAR_CATEGORIE.items():
        for mot_cle in mots_cles:
            print(f"Recherche: {mot_cle} (categorie attendue: {categorie_attendue})")
            try:
                produits = chercher_produits(mot_cle)
            except ScrapingError as e:
                print(f"  Erreur ignoree pour '{mot_cle}': {e}")
                continue

            for produit in produits:
                echantillon.append({
                    **produit,
                    "mot_cle_recherche": mot_cle,
                    "categorie_attendue_provisoire": categorie_attendue,
                    "categorie_validee_manuellement": None,
                })

            time.sleep(1)  # pause polie entre les requetes

    with open(sortie, "w", encoding="utf-8") as f:
        json.dump(echantillon, f, ensure_ascii=False, indent=2)

    print(f"\n{len(echantillon)} produits enregistres dans {sortie}")


if __name__ == "__main__":
    generer_echantillon()
