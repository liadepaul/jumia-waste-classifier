# EcoSort-Search

Application web d’aide au tri sélectif combinant le scraping de produits Jumia et un modèle de classification d’images par Deep Learning.

L’utilisateur recherche un produit, sélectionne l’un des résultats proposés, puis l’application indique la catégorie de tri correspondante :

- bac jaune : plastique, métal et carton ;
- bac vert : verre ;
- bac bleu : papier ;
- bac gris : déchets électroniques (D3E) ;
- bac marron : déchets résiduels non recyclables.

## Architecture

```text
app/
  app.py                 Application Flask et intégration des modules
  templates/             Pages HTML
  static/                CSS et images de l’interface

model/
  predict.py             Fonction de prédiction
  modele_eco_sort.h5     Modèle entraîné

scraper/
  jumia_scraper.py       Recherche de produits sur Jumia

Dockerfile
docker-compose.yml
requirements.txt
```

## Contrat entre les modules

Le scraper doit exposer :

```python
chercher_produits(mot_cle: str) -> list[dict]
```

Chaque produit doit contenir :

```python
{
    "nom": "...",
    "image_url": "...",
    "prix": "...",
    "lien": "...",
    "categorie_jumia": "..."
}
```

Le module IA expose :

```python
predire_categorie(chemin_image: str) -> dict
```

Il renvoie une catégorie de tri et un score de confiance. Si la confiance est inférieure à `0.5`, le résultat est considéré comme incertain.

## Installation locale

Prérequis :

- Python 3.11 ;
- connexion Internet ;
- environnement virtuel recommandé.

Sous Windows avec Git Bash :

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
```

Lancement :

```bash
python app/app.py
```

Ouvrir ensuite :

```text
http://127.0.0.1:5000
```

## Lancement avec Docker

Construction de l’image :

```bash
docker build -t ecosort .
```

Lancement du conteneur :

```bash
docker run --rm -p 8501:8501 ecosort
```

L’application est alors accessible à l’adresse :

```text
http://localhost:8501
```

Avec Docker Compose :

```bash
docker compose up -d --build
```

Arrêt :

```bash
docker compose down
```

## Détection des déchets électroniques

Le dataset ne contient pas de classe électronique. Les produits D3E sont détectés en amont du modèle à partir de leur catégorie Jumia et de mots-clés présents dans leur nom.

## Limites connues

- La structure HTML de Jumia peut évoluer.
- Jumia peut limiter les requêtes automatisées.
- Une connexion Internet est nécessaire pour la recherche et certaines ressources graphiques.
- Un produit électronique absent des critères D3E peut être mal classé.
- La prédiction dépend de la qualité de l’image du produit.
