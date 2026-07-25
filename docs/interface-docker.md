# EcoSort-Search — Interface Flask & Docker

Documentation technique de la branche `validation/interface-docker` (responsabilité Élève C).

> Cette branche couvre uniquement le fonctionnement technique de l'application
> (routes Flask, Docker). L'apparence (templates, CSS) sera gérée séparément
> sur la branche `validation/design`, qui sera créée par l'Élève A dans une
> étape ultérieure du projet.

---

## 1. Prérequis

- Python 3.11
- Docker Desktop (pour le lancement conteneurisé)
- Un environnement virtuel dédié au projet

## 2. Installation en local (sans Docker)

```bash
git clone https://github.com/liadepaul/jumia-waste-classifier.git
cd jumia-waste-classifier
git switch validation/interface-docker

python -m venv venv
source venv/Scripts/activate      # Windows (Git Bash)
# source venv/bin/activate        # macOS / Linux

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 3. Lancer l'application en local

```bash
python app/app.py
```

L'application est alors accessible sur :
```
http://localhost:5000
```
ou sur le port défini par la variable d'environnement `PORT` si elle est fixée
(voir section Docker, où `PORT=8501`).

## 4. Lancer les tests automatisés

```bash
python -m pip install pytest
python -m pytest -q tests
```

Résultat attendu : tous les tests passent (`N passed`).

## 5. Construire et lancer avec Docker

Conformément au contrat du groupe, l'application doit être exécutable avec
uniquement ces commandes, depuis un clone propre du dépôt :

```bash
docker build -t ecosort .
docker run -p 8501:8501 ecosort
```

Ou avec Docker Compose :

```bash
docker-compose up -d --build
```

L'application est alors accessible sur :
```
http://localhost:8501
```

## 6. Vérifier l'état du service

Une fois l'application lancée (en local ou en conteneur), le point de contrôle
`/health` permet de vérifier que Flask répond et que le modèle IA est bien
présent :

```bash
curl http://localhost:8501/health
```

Réponses possibles :
- `{"status": "ok"}` (code 200) — le modèle `.h5` est trouvé, tout fonctionne
- `{"status": "degraded"}` (code 503) — Flask répond mais le modèle est introuvable

Ce point de contrôle est aussi utilisé automatiquement par le `HEALTHCHECK`
défini dans le `Dockerfile` (vérification toutes les 30 secondes).

## 7. Vérifier l'état du conteneur

```bash
docker ps
```

La colonne `STATUS` doit indiquer `Up ... (healthy)` après le délai de
démarrage (`start_period` de 20 secondes).

---

## 8. Contrat entre Flask et le design (à ne pas modifier sans accord du groupe)

| Route | Comportement |
|---|---|
| `/` | Affiche `index.html` |
| `POST /recherche` | Traite `mot_cle`, affiche `resultats.html` |
| `POST /verdict` | Analyse le produit sélectionné, affiche `verdict.html` |
| `/health` | Retourne l'état du service et du modèle |

**Champs de formulaire conservés** : `mot_cle`, `nom`, `image_url`, `categorie_jumia`

**Données d'un produit** : `nom`, `image_url`, `prix`, `categorie_jumia`

**Variables transmises aux templates** :
- `resultats.html` → `produits`, `mot_cle`, `erreur`
- `verdict.html` → `produit`, `affichage`, `confiance`, `source_verdict`

`source_verdict` indique l'origine de la décision : `IA`, `règle texte`, `D3E`
ou `erreur` — pour que l'interface puisse l'afficher clairement à l'utilisateur.

---

## 9. Tests manuels effectués avant la Pull Request

- [x] La page d'accueil s'ouvre
- [x] Une recherche valide affiche des produits
- [x] Une recherche sans résultat affiche un message clair (pas de plantage)
- [x] La sélection d'un produit affiche un verdict avec confiance et source
- [x] `GET /health` répond correctement
- [x] `docker build` se termine sans erreur
- [x] `docker run -p 8501:8501 ecosort` rend l'application accessible
- [x] Les tests automatisés (`pytest`) passent

## 10. Limites connues

- Le serveur utilisé est le serveur de développement Flask, pas un serveur WSGI
  de production (ex. gunicorn). Suffisant pour le cadre de ce projet.
- La confiance du modèle IA reste parfois sous le seuil de 50 %, entraînant
  l'affichage de la catégorie "incertain" — limite documentée côté modèle
  (branche `validation/ia`), pas un bug de l'intégration Flask/Docker.
