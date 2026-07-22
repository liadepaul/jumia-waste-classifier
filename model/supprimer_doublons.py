import os
from nettoyer_donnees import analyser_dataset

def supprimer_doublons():
    corrompues, doublons = analyser_dataset()

    print("\n=== SUPPRESSION DES DOUBLONS INTER-CLASSES ===")
    fichiers_supprimes = 0
    for h, chemins in doublons.items():
        for chemin in chemins:
            if os.path.exists(chemin):
                os.remove(chemin)
                print(f"  Supprime : {chemin}")
                fichiers_supprimes += 1

    print(f"\nTotal supprime : {fichiers_supprimes} fichiers")

if __name__ == "__main__":
    supprimer_doublons()