# Expérience IA 01 - modèle candidat

## Objectif

Vérifier si une augmentation légèrement renforcée, un lissage des étiquettes
et une sélection du checkpoint par perte de validation améliorent le CNN
MobileNetV2 existant.

Le modèle de production `modele_eco_sort.h5` n'a pas été modifié.

## Données

- 1 762 images d'entraînement ;
- 376 images de validation ;
- 383 images de test indépendant ;
- classes : `cardboard`, `glass`, `metal`, `paper`, `plastic`, `trash` ;
- aucun doublon détecté dans les 2 521 images, y compris entre les splits.

## Déroulement

La phase avec MobileNetV2 gelé s'est arrêtée pendant l'époque 23 à cause de
l'exécution TensorFlow locale. Le fine-tuning n'a donc pas été exécuté.
Le meilleur checkpoint déjà sauvegardé a été évalué sur le jeu de test.

## Comparaison sur le test Kaggle

| Indicateur | Modèle actuel | Candidat | Écart |
|---|---:|---:|---:|
| Accuracy | 81,20 % | 82,77 % | +1,57 point |
| Macro précision | 78,96 % | 80,33 % | +1,37 point |
| Macro rappel | 80,52 % | 80,99 % | +0,47 point |
| Macro F1 | 79,19 % | 80,42 % | +1,23 point |
| Images correctes | 311/383 | 317/383 | +6 |

## F1 par classe

| Classe | Modèle actuel | Candidat | Écart |
|---|---:|---:|---:|
| cardboard | 86,67 % | 87,93 % | +1,26 point |
| glass | 74,82 % | 79,45 % | +4,63 points |
| metal | 80,56 % | 82,09 % | +1,53 point |
| paper | 88,51 % | 88,52 % | +0,01 point |
| plastic | 80,58 % | 82,01 % | +1,43 point |
| trash | 64,00 % | 62,50 % | -1,50 point |

## Test sur les images Jumia

- modèle actuel seul : 1/10 ;
- candidat seul : 1/10 ;
- application hybride avec règles texte et D3E : 10/10 sur cet échantillon.

Le candidat améliore la reconnaissance des matières du dataset, notamment le
verre, mais ne résout pas le décalage avec les photographies commerciales.

## Décision

Le candidat n'est pas déployé pour le moment :

1. le fine-tuning n'est pas terminé ;
2. la classe `trash` régresse ;
3. le résultat direct sur Jumia ne progresse pas ;
4. dix images Jumia ne suffisent pas pour conclure à une généralisation.

Le modèle actuel reste la référence tant qu'un candidat complet ne dépasse pas
ses résultats sans dégrader `trash`.
