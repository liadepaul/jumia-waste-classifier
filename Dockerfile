# --- Image de base ---
FROM python:3.11-slim

# --- Dependance systeme requise par TensorFlow (calcul numerique) ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# --- Installation des dependances Python ---
# Copie du requirements.txt seul d'abord (avant le reste du code) :
# Docker met en cache cette etape tant que requirements.txt ne change pas,
# ce qui accelere les reconstructions futures.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Copie du reste du projet ---
COPY . .

# --- Configuration du port ---
# Le contrat du groupe prevoit "docker run -p 8501:8501", donc l'application
# doit ecouter sur le port 8501 a l'interieur du conteneur.
ENV PORT=8501
EXPOSE 8501

# --- Lancement de l'application ---
CMD ["python", "app/app.py"]
