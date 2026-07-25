"""
Outil interactif pour annoter manuellement les produits de
data/echantillon_jumia/echantillon_brut.json.

Pour chaque produit sans annotation, affiche le nom et ouvre l'image
dans le navigateur, puis demande la vraie categorie de tri.

Sauvegarde apres chaque produit : on peut interrompre (Ctrl+C ou 'q')
et reprendre plus tard sans perdre la progression.
"""
import json
import webbrowser

FICHIER = "data/echantillon_jumia/echantillon_brut.json"

CHOIX = {
    "j": "jaune",
    "v": "vert",
    "b": "bleu",
    "g": "gris",
    "m": "marron",
    "x": "aucune",  # produit non pertinent / pas un objet a trier
}


def charger():
    with open(FICHIER, "r", encoding="utf-8") as f:
        return json.load(f)


def sauvegarder(donnees):
    with open(FICHIER, "w", encoding="utf-8") as f:
        json.dump(donnees, f, ensure_ascii=False, indent=2)


def annoter():
    donnees = charger()
    a_faire = [p for p in donnees if p.get("categorie_validee_manuellement") is None]
    total = len(donnees)
    deja_fait = total - len(a_faire)

    print(f"{deja_fait}/{total} deja annotes. {len(a_faire)} restants.\n")

    if not a_faire:
        print("Tout est deja annote !")
        return

    print("Options a chaque produit :")
    print("  j = jaune   v = vert   b = bleu   g = gris   m = marron")
    print("  x = non pertinent (pas un objet a trier)")
    print("  s = passer (laisser vide pour l'instant)")
    print("  q = arreter et sauvegarder\n")

    for i, produit in enumerate(a_faire, start=1):
        print(f"--- Produit {i}/{len(a_faire)} ---")
        print("Nom  :", produit["nom"])
        print("Prix :", produit["prix"])
        print("Mot-cle de recherche:", produit["mot_cle_recherche"])
        print("Categorie provisoire (deduite du mot-cle):", produit["categorie_attendue_provisoire"])

        if produit.get("image_url"):
            webbrowser.open(produit["image_url"])

        reponse = input("Ta reponse (j/v/b/g/m/x/s/q) : ").strip().lower()

        if reponse == "q":
            sauvegarder(donnees)
            print("\nArret demande. Progression sauvegardee.")
            return
        elif reponse == "s":
            print("Passe.\n")
            continue
        elif reponse in CHOIX:
            produit["categorie_validee_manuellement"] = CHOIX[reponse]
            sauvegarder(donnees)
            print(f"Enregistre : {CHOIX[reponse]}\n")
        else:
            print("Reponse non reconnue, produit passe.\n")

    print("Annotation terminee pour tous les produits restants !")


if __name__ == "__main__":
    annoter()
