"""
Repasse en revue, un par un, tous les produits deja annotes dans
data/echantillon_jumia/echantillon_brut.json.

Pour chaque produit : ouvre l'image, affiche l'annotation actuelle,
et permet de la garder ou de la changer.
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
    "x": "aucune",
}


def charger():
    with open(FICHIER, "r", encoding="utf-8") as f:
        return json.load(f)


def sauvegarder(donnees):
    with open(FICHIER, "w", encoding="utf-8") as f:
        json.dump(donnees, f, ensure_ascii=False, indent=2)


def reviser():
    donnees = charger()
    annotes = [p for p in donnees if p.get("categorie_validee_manuellement") is not None]

    print(f"{len(annotes)} produits deja annotes a revoir.\n")
    print("Options a chaque produit :")
    print("  Entree (rien taper) = garder l'annotation actuelle")
    print("  j = jaune   v = vert   b = bleu   g = gris   m = marron   x = non pertinent")
    print("  q = arreter la revision\n")

    for i, produit in enumerate(annotes, start=1):
        print(f"--- Produit {i}/{len(annotes)} ---")
        print("Nom  :", produit["nom"])
        print("Prix :", produit["prix"])
        print("Annotation actuelle :", produit["categorie_validee_manuellement"])

        if produit.get("image_url"):
            webbrowser.open(produit["image_url"])

        reponse = input("Nouvelle annotation (Entree = garder, q = quitter) : ").strip().lower()

        if reponse == "q":
            sauvegarder(donnees)
            print("\nRevision arretee. Progression sauvegardee.")
            return
        elif reponse == "":
            print("Conserve tel quel.\n")
            continue
        elif reponse in CHOIX:
            ancienne = produit["categorie_validee_manuellement"]
            produit["categorie_validee_manuellement"] = CHOIX[reponse]
            sauvegarder(donnees)
            print(f"Modifie : {ancienne} -> {CHOIX[reponse]}\n")
        else:
            print("Reponse non reconnue, conserve tel quel.\n")

    print("Revision terminee pour tous les produits !")


if __name__ == "__main__":
    reviser()
