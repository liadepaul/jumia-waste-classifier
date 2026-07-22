FROM python:3.11-slim

# Empeche Python de generer des .pyc et force les logs a s'afficher immediatement
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code

# Installer les dependances d'abord (profite du cache Docker si le code change
# mais pas requirements.txt)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du projet (app/, model/, scraper/, etc.)
COPY . .

EXPOSE 5000

# gunicorn en production plutot que le serveur de developpement Flask.
# "app.app:app" = fichier app/app.py, variable Flask nommee "app".
# --timeout 120 : laisse le temps au modele de Deep Learning de charger/predire.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "120", "app.app:app"]
