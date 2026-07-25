# Évaluation complémentaire sur l'échantillon Jumia annoté du groupe (83 produits)

Cette évaluation complémentaire ne remplace ni le test Kaggle, ni le
benchmark de développement de 50 produits, ni le holdout indépendant de
25 produits.

## 1. Objectif

Évaluer le CNN et l'application hybride sur l'échantillon de 83 produits
Jumia annotés manuellement par B (branche `validation/scraper`), en
identifiant précisément les recoupements avec les jeux d'évaluation
précédents pour ne pas surestimer l'indépendance de ce nouveau jeu.

## 2. Chronologie

- Benchmark de développement de 50 produits : terminé avant le fichier de B.
- Holdout indépendant de 25 produits : terminé avant le fichier de B.
- Échantillon de 83 produits de B (`data/echantillon_jumia/echantillon_brut.json`) :
  finalisé ensuite, via la PR nº 9 (`validation/scraper` →
  `release/stabilisation-finale`, commit de fusion `b905f0e`).

## 3. Origine des données

Fichier source : `data/echantillon_jumia/echantillon_brut.json`, produit
par le scraper du groupe et annoté manuellement (champ
`categorie_validee_manuellement`). Ce fichier n'a pas été modifié par
cette évaluation.

## 4. Distribution des 83 annotations

| Catégorie | Nombre |
|---|---:|
| marron | 22 |
| gris | 20 |
| jaune | 17 |
| bleu | 10 |
| aucune | 8 |
| vert | 6 |
| **Total** | **83** |

## 5. Traitement des huit "aucune"

Les 8 produits annotés `aucune` (produits que B a jugés non classables
dans une des cinq poubelles) sont exclus de toutes les métriques
chiffrées ci-dessous. Ils ne sont ni comptés comme corrects, ni comme
incorrects.

## 6. Chevauchements avec les jeux précédents

Vérifiés par comparaison exacte du champ `lien` avec
`diagnostic/benchmark_jumia.csv` et `diagnostic/holdout_jumia.csv`
(script `diagnostic/evaluer_echantillon_groupe.py`, fonction `repartir`) :

- 83 produits au total ;
- 8 annotés "aucune" (exclus) ;
- 75 produits classables ;
- parmi eux, 13 liens déjà présents dans les jeux précédents (recoupement
  avec le benchmark de 50 et/ou le holdout de 25) ;
- 62 produits classables réellement nouveaux.

Ces chiffres ont été recalculés automatiquement à partir des liens, pas
recopiés depuis une estimation externe.

## 7. Résultats hybrides sur les 75 produits classables

| Catégorie | Application correcte |
|---|---:|
| Jaune | 12/17 |
| Vert | 5/6 |
| Bleue | 8/10 |
| Grise (D3E) | 20/20 |
| Marron | 0/22 |
| **Total** | **45/75 (60,00 %)** |

Macro F1 : 60,13 %.

## 8. Résultats hybrides sur les 62 produits classables nouveaux

| Catégorie | Application correcte |
|---|---:|
| Jaune | 10/15 |
| Vert | 4/5 |
| Bleue | 5/7 |
| Grise (D3E) | 13/13 |
| Marron | 0/22 |
| **Total** | **32/62 (51,61 %)** |

Macro F1 : 55,91 %.

Les 22 produits marron n'ont aucun recoupement avec les jeux précédents ;
leur nombre est donc identique dans les deux évaluations (75 et 62).

## 9. Résultats CNN direct (hors D3E, hors "aucune")

Le CNN n'a pas de sortie D3E : ses 20 produits gris sont exclus, comme les
8 "aucune". Base théorique : 75 − 20 = 55 produits, confirmée à
l'exécution (55 tentés, 55 évalués, 0 erreur technique).

| Catégorie | CNN correct |
|---|---:|
| Jaune | 11/17 |
| Vert | 2/6 |
| Bleue | 7/10 |
| Marron | 0/22 |
| **Total** | **20/55 (36,36 %)** |

Macro F1 : 31,43 %.

Le score du CNN direct ne doit jamais être présenté comme celui de
l'application : ce sont deux mesures distinctes (cf. section 12).

## 10. Sources des verdicts (application, n=75)

- règle texte : 36 ;
- D3E : 22 ;
- IA : 17 ;
- erreur : 0.

## 11. Erreurs techniques

Aucune erreur de téléchargement d'image rencontrée, ni côté application
hybride ni côté CNN direct (75/75 et 55/55 images traitées avec succès).
Le dénominateur annoncé correspond donc au nombre de produits réellement
évalués dans les deux cas.

## 12. Matrice de confusion (application, 75 produits classables)

| Attendu \ Prédit | jaune | vert | bleu | gris | marron | incertain |
|---|---:|---:|---:|---:|---:|---:|
| jaune | 12 | 1 | 0 | 0 | 0 | 4 |
| vert | 0 | 5 | 0 | 0 | 0 | 1 |
| bleu | 0 | 0 | 8 | 0 | 0 | 2 |
| gris | 0 | 0 | 0 | 20 | 0 | 0 |
| marron | 1 | 1 | 14 | 0 | 0 | 6 |

Lecture : sur les 22 produits marron, 14 sont classés en bleu (via la
règle texte "papier"), 6 sont jugés incertains par l'IA, 1 en jaune et
1 en vert. Aucun ne correspond à l'annotation marron attendue.

## 13. Limites méthodologiques

- **Écart observé sur le marron (0/22)** : une majorité des produits
  annotés marron dans cet échantillon sont des emballages ou fournitures
  d'expédition — sachets kraft, papier kraft en lot, ruban adhésif,
  scotch, cartons scellés. Ces produits déclenchent la règle texte du bac
  bleu (mot-clé `papier`), alors que le groupe les a annotés manuellement
  en marron. Il s'agit d'un écart entre l'annotation manuelle et la règle
  textuelle "papier" sur des cas ambigus (kraft, adhésifs, objets
  multimatières) qui mériterait une clarification collective plutôt que
  d'un jugement sur la qualité de la règle elle-même. **Aucune règle n'a
  été modifiée dans le cadre de cette évaluation**, conformément à la
  consigne de ne pas ajuster avant d'avoir enregistré les résultats
  initiaux.
- Les 13 chevauchements avec les jeux précédents signifient que les 75 et
  62 produits ne sont pas deux échantillons totalement indépendants l'un
  de l'autre ; les 62 nouveaux restent la mesure la plus proche d'un test
  non vu.
- Échantillon non stratifié à parts égales par catégorie (22 marron contre
  6 vert) : la macro F1 est donc plus représentative que l'accuracy brute
  pour comparer aux évaluations précédentes.
- Le CNN direct ne traite pas les D3E : son accuracy sur 55 produits ne
  peut pas être comparée directement à l'accuracy de l'application sur 75
  ou 62 produits (dénominateurs et catégories différents).

## 14. Comparaison prudente avec les évaluations de 50 et 25

| Évaluation | Application hybride | CNN direct (hors D3E) |
|---|---:|---:|
| Benchmark de développement (50) | 50/50 (100 %) | 20/50 (40 %) |
| Holdout indépendant (25) | 25/25 (100 %) | 11/25 (44 %) |
| Échantillon groupe — 75 classables | 45/75 (60,00 %) | 20/55 (36,36 %) |
| Échantillon groupe — 62 nouveaux | 32/62 (51,61 %) | — |

Le CNN direct reste dans un ordre de grandeur comparable (36–44 %) sur les
trois jeux. L'application hybride, elle, chute nettement (100 % →
60 %/52 %) ; l'écart se concentre sur la catégorie marron de ce nouvel
échantillon (section 13). Ce résultat ne remet pas en cause le CNN ni les
métriques Kaggle : il met en évidence un point précis à clarifier
collectivement sur la frontière entre "papier" et "marron" pour certains
produits, à traiter dans une itération ultérieure, hors du périmètre de
cette évaluation.

## 15. Commande exacte de reproduction

Depuis la racine du dépôt (`jumia-waste-classifier`, branche
`validation/ia`) :

```bash
python diagnostic/evaluer_echantillon_groupe.py
```

Options disponibles : `--echantillon`, `--benchmark-csv`,
`--holdout-csv`, `--sortie-dir` (voir `--help`). Les fichiers de détail
(`diagnostic/resultats_echantillon_groupe_hybride.csv` et
`diagnostic/resultats_echantillon_groupe_cnn.csv`) sont générés
localement et ignorés par Git.
