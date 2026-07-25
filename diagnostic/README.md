# Diagnostic IA / intégration

## 1. Préparer les images

Le dossier test du dataset doit contenir :

```text
data/split/test/
  cardboard/
  glass/
  metal/
  paper/
  plastic/
  trash/
```

Enregistrer ensuite dix images de produits Jumia dans
`diagnostic/images_jumia/` avec les noms `01.jpg` à `10.jpg`.

Pour chaque image, compléter `diagnostic/jumia.csv` :

- `nom` : nom réel du produit ;
- `categorie_jumia` : catégorie si elle est connue ;
- `poubelle_attendue` : `jaune`, `vert`, `bleu`, `gris` ou `marron`.

L'annotation attendue doit être décidée manuellement avant d'exécuter le
modèle.

## 2. Lancer le diagnostic

Depuis la racine du projet :

```bash
python diagnostic_ia.py \
  --dataset-dir data/split/test \
  --jumia-csv diagnostic/jumia.csv \
  --output diagnostic/resultats.csv
```

Pour comparer un checkpoint candidat sans remplacer le modèle de l'application :

```bash
python diagnostic_ia.py \
  --dataset-dir data/split/test \
  --jumia-csv diagnostic/jumia.csv \
  --output diagnostic/resultats_candidat.csv \
  --modele-direct model/candidats/modele_candidat.keras
```

Dans ce cas, la colonne du modèle direct utilise le candidat, tandis que la
colonne de l'application continue d'utiliser le modèle actuellement déployé.

Sous PowerShell, la commande peut être écrite sur une seule ligne.

## 3. Interpréter `resultats.csv`

- `poubelle_modele_direct` mesure uniquement la partie IA ;
- `poubelle_application` mesure la décision intégrée ;
- `source_application` vaut `IA`, `règle texte`, `D3E` ou `erreur` ;
- si le modèle direct est correct mais l'application ne l'est pas, le défaut
  appartient à l'intégration ;
- si les deux sont incorrects, il faut examiner le modèle ou le décalage entre
  le dataset et les images Jumia ;
- si la source est `erreur`, lire la colonne `erreur` avant de conclure.

