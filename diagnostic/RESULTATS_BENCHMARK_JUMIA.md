# Benchmark Jumia élargi

## Objectif

Mesurer séparément :

1. la prédiction du CNN à partir de l'image uniquement ;
2. le verdict réellement affiché par l'application, qui combine le CNN,
   les règles textuelles et la détection D3E.

Le benchmark contient 50 produits Jumia, soit 10 produits pour chacune des
cinq poubelles : jaune, verte, bleue, grise et marron.

## Constitution du benchmark

- Les produits ont été collectés avec le scraper du projet.
- Chaque image et chaque libellé attendu ont été contrôlés avant l'évaluation.
- Les 50 annotations ont le statut `validee`.
- Aucun lien produit ni fichier image n'est dupliqué.
- Le nom du produit et le terme de recherche sont transmis à l'application,
  comme lors d'une véritable recherche Jumia.
- Les images téléchargées ne sont pas versionnées. Le CSV conserve les URL
  sources et les annotations nécessaires à la traçabilité.

## Résultats avant l'ajustement des règles

Après correction du diagnostic pour transmettre le terme de recherche :

| Poubelle | CNN seul | Application |
|---|---:|---:|
| Jaune | 8/10 | 8/10 |
| Verte | 1/10 | 8/10 |
| Bleue | 7/10 | 10/10 |
| Grise (D3E) | 0/10 | 10/10 |
| Marron | 0/10 | 10/10 |
| **Total** | **16/50 (32 %)** | **46/50 (92 %)** |

Les quatre erreurs restantes concernaient deux bouteilles ou flacons destinés
au bac jaune et deux bocaux en verre destinés au bac vert.

## Ajustement réalisé

Des règles générales ont été ajoutées pour reconnaître :

- un bocal, un pot ou une bouteille explicitement décrit comme étant en verre ;
- une bouteille d'eau ou de boisson sans mention de verre ;
- un shampoing ou après-shampoing conditionné en flacon.

La priorité donnée à la vaisselle et aux objets non recyclables reste inchangée.
Par exemple, un verre à boire reste classé dans la poubelle marron et une
bouteille d'eau en verre dans la poubelle verte.

## Résultats après l'ajustement

| Poubelle | CNN seul | Application |
|---|---:|---:|
| Jaune | 8/10 | 10/10 |
| Verte | 1/10 | 10/10 |
| Bleue | 7/10 | 10/10 |
| Grise (D3E) | 0/10 | 10/10 |
| Marron | 0/10 | 10/10 |
| **Total** | **16/50 (32 %)** | **50/50 (100 %)** |

Sources des 50 décisions de l'application :

- règles textuelles : 40 ;
- règle D3E : 10 ;
- CNN seul : 0.

Le CNN n'a pas été remplacé ni modifié. Son score direct reste donc 16/50.

## Contrôle sur le dataset

Dans la même exécution, un échantillon déterministe et réparti entre les six
classes du dataset donne 46/50 au CNN et 46/50 à l'application. L'évaluation
complète déjà réalisée sur les 383 images de test reste la mesure de référence :
311/383, soit 81,20 % d'accuracy, avec un macro F1 de 79,19 %.

## Interprétation correcte

Le 50/50 mesure la logique hybride sur un **jeu de développement** : les quatre
erreurs observées ont servi à améliorer les règles. Ce résultat ne doit donc pas
être présenté comme une validation indépendante ou comme une accuracy de 100 %
du CNN.

La conclusion est la suivante :

- le CNN est convenable pour les images proches de son dataset ;
- il généralise encore mal aux photographies commerciales Jumia ;
- les règles textuelles et D3E sont indispensables dans l'application actuelle ;
- un nouveau lot Jumia, jamais consulté pendant le développement, doit servir
  de test final avant la présentation.

## Reproduction

Depuis la racine du projet :

```powershell
python diagnostic_ia.py `
  --dataset-dir "CHEMIN_VERS_DATA\split\test" `
  --jumia-csv diagnostic\benchmark_jumia.csv `
  --output diagnostic\resultats.csv `
  --nombre 50
```

Le fichier `diagnostic/resultats.csv` est volontairement ignoré par Git, car il
contient les résultats locaux reproductibles et des chemins propres à la
machine.
