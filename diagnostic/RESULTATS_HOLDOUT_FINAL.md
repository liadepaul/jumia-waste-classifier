# Validation finale sur un holdout Jumia

## Objectif

Vérifier le CNN amélioré et l'application hybride sur des produits Jumia
jamais utilisés pour entraîner le modèle, développer les règles ou constituer
le benchmark précédent.

## Constitution et gel

- 25 produits : 5 par poubelle ;
- plusieurs recherches différentes dans chaque catégorie ;
- aucun lien commun avec les 50 produits du benchmark de développement ;
- 25 liens uniques et 25 images uniques par SHA-256 ;
- contrôle des titres et inspection visuelle des images avant la prédiction ;
- annotations marquées `validee` avant l'exécution du diagnostic.

Deux candidats ont été rejetés pendant le contrôle préalable :

- un coffret comprenant un carnet, un stylo et un sac, trop multimatière pour
  représenter proprement la poubelle bleue ;
- une brosse à batterie présentée par un titre trompeur comme un peigne manuel.

Ils ont été remplacés respectivement par un cahier seul et un peigne manuel en
bois. Aucun résultat du CNN ou de l'application n'avait encore été consulté.

Empreinte SHA-256 du CSV au moment du gel :

`0960152BB60EB1B07C687CCA0C33B9B33CE1105B681789E6BC4C943BE5FE77FF`

Après le gel, aucune annotation, règle textuelle ni poids du modèle n'a été
modifié.

## Résultats

| Poubelle | CNN seul | Application | Total |
|---|---:|---:|---:|
| Jaune | 3 | 5 | 5 |
| Verte | 4 | 5 | 5 |
| Bleue | 4 | 5 | 5 |
| Grise (D3E) | 0 | 5 | 5 |
| Marron | 0 | 5 | 5 |
| **Total** | **11/25 (44 %)** | **25/25 (100 %)** | **25** |

Le CNN ne possède pas de sortie D3E. Sur les 20 produits qui ne sont pas D3E,
son score direct est donc de 11/20, soit 55 %.

Sources des décisions finales :

- règles textuelles : 16 ;
- CNN : 4 ;
- détection D3E : 5.

Aucune erreur technique n'a été rencontrée.

Dans la même exécution, l'échantillon déterministe de 25 images Kaggle donne
22/25 au CNN et 22/25 à l'application.

## Interprétation

Le résultat confirme sur un jeu indépendant que l'application complète est
plus fiable que le CNN utilisé seul. Le CNN reste un classifieur de matières :
il ne peut pas reconnaître directement les D3E et distingue encore mal la
vaisselle et certains objets manufacturés.

Le 25/25 concerne ce holdout limité et équilibré. Il ne signifie ni que le CNN
possède une accuracy de 100 %, ni que l'application réussira tous les produits
possibles. Il constitue cependant une validation indépendante positive de la
logique hybride.

## Reproduction

```powershell
python diagnostic_ia.py `
  --dataset-dir "CHEMIN_VERS_DATA\split\test" `
  --jumia-csv diagnostic\holdout_jumia.csv `
  --output diagnostic\resultats_holdout.csv `
  --nombre 25
```

Le fichier local de résultats est ignoré par Git car ses lignes Kaggle
contiennent le chemin absolu du dataset sur la machine d'évaluation.
