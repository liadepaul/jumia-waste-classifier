# Expérience IA 02 — amélioration retenue

## Objectif et conformité

Améliorer le CNN sans ajouter de données externes au dataset imposé par le
sujet. L'expérience utilise exclusivement le dataset Kaggle Garbage
Classification et conserve les mêmes six classes :
`cardboard`, `glass`, `metal`, `paper`, `plastic` et `trash`.

Le modèle de production a été conservé pendant tout l'entraînement. Il n'a été
remplacé qu'après l'évaluation du candidat sur le jeu de test indépendant.

## Données

- entraînement : 1 762 images ;
- validation : 376 images ;
- test indépendant : 383 images ;
- aucun doublon détecté entre les différents ensembles ;
- graine utilisée : 42.

## Méthode

- MobileNetV2 préentraîné sur ImageNet ;
- augmentation Kaggle : retournement horizontal, rotation, zoom et contraste ;
- pondération des classes ;
- lissage des étiquettes à 0,05 ;
- sélection du checkpoint par la perte de validation ;
- 25 époques pour la tête de classification ;
- 6 époques de fine-tuning avant arrêt anticipé.

Le fine-tuning n'a pas dépassé le meilleur checkpoint de la première phase.
Le mécanisme de sauvegarde a donc correctement conservé ce dernier.

## Résultats sur les 383 images de test Kaggle

| Indicateur | Ancien modèle | Nouveau modèle | Écart |
|---|---:|---:|---:|
| Accuracy | 81,20 % | 83,03 % | +1,83 point |
| Macro précision | 78,96 % | 80,59 % | +1,63 point |
| Macro rappel | 80,52 % | 81,21 % | +0,69 point |
| Macro F1 | 79,19 % | 80,67 % | +1,48 point |
| Images correctes | 311/383 | 318/383 | +7 |

### F1 par classe

| Classe | Ancien modèle | Nouveau modèle | Écart |
|---|---:|---:|---:|
| cardboard | 86,67 % | 87,93 % | +1,26 point |
| glass | 74,82 % | 80,82 % | +6,00 points |
| metal | 80,56 % | 82,71 % | +2,15 points |
| paper | 88,51 % | 88,04 % | -0,47 point |
| plastic | 80,58 % | 82,01 % | +1,43 point |
| trash | 64,00 % | 62,50 % | -1,50 point |

La classe `trash` reste la plus fragile. Sa baisse de 1,50 point est limitée,
alors que les indicateurs globaux, le verre et le métal progressent.

## Résultats directs sur 50 produits Jumia

| Poubelle attendue | Ancien CNN | Nouveau CNN |
|---|---:|---:|
| Jaune | 8/10 | 8/10 |
| Verte | 1/10 | 4/10 |
| Bleue | 7/10 | 7/10 |
| Grise (D3E) | 0/10 | 0/10 |
| Marron | 0/10 | 1/10 |
| **Total** | **16/50 (32 %)** | **20/50 (40 %)** |

Le CNN ne possède pas de sortie D3E. En retirant uniquement les dix D3E, le
nouveau modèle obtient 20/40, contre 16/40 auparavant.

L'application hybride conserve 50/50 sur ce jeu de développement grâce aux
règles textuelles et à la détection D3E.

## Seuil de confiance de l'application

Sur l'échantillon déterministe de 50 images Kaggle utilisé par le diagnostic :

- le CNN classe correctement 45 images ;
- l'application valide 43 verdicts ;
- six prédictions sont remplacées par `incertain` car leur confiance est
  inférieure à 50 % ;
- parmi elles, deux étaient correctes et quatre étaient incorrectes.

Ce mécanisme réduit la couverture mais évite d'afficher certaines erreurs comme
des verdicts certains.

## Déploiement

Le meilleur checkpoint Keras contient les couches d'augmentation nécessaires
à l'entraînement. Pour l'application, elles sont retirées car elles sont
inactives pendant l'inférence. Le modèle d'inférence `.h5` :

- reproduit exactement 83,03 % d'accuracy et 80,67 % de macro F1 ;
- reste compatible avec `model/predict.py` ;
- pèse environ 9,4 Mo contre 21,7 Mo pour l'ancien fichier.

## Décision

Le nouveau modèle est retenu parce qu'il :

1. améliore l'accuracy et le macro F1 sur le test Kaggle indépendant ;
2. améliore le verre de six points de F1 ;
3. progresse sur les images Jumia sans avoir été entraîné avec celles-ci ;
4. respecte le dataset imposé par le sujet ;
5. réduit la taille du modèle déployé.

Les règles textuelles et D3E restent nécessaires : le CNN demeure un
classifieur de matières, pas un classifieur universel de produits.
