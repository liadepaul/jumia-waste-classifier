import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, classification_report
import os

TAILLE_IMAGE = (224, 224)
BATCH_SIZE = 32
RACINE = "data/split"
CLASSES = ["cardboard", "glass", "metal", "paper", "plastic", "trash"]

# ---------------------------------------------------------
# 1. Charger le modele entraine et les donnees de test
# ---------------------------------------------------------
model = tf.keras.models.load_model("model/modele_eco_sort.h5")

test_ds = tf.keras.utils.image_dataset_from_directory(
    os.path.join(RACINE, "test"),
    labels="inferred",
    label_mode="categorical",
    class_names=CLASSES,
    image_size=TAILLE_IMAGE,
    batch_size=BATCH_SIZE,
    shuffle=False,   # important : on garde l'ordre pour associer predictions et vraies etiquettes
)

# ---------------------------------------------------------
# 2. Evaluation globale
# ---------------------------------------------------------
loss, accuracy = model.evaluate(test_ds)
print(f"\n=== RESULTAT SUR LE TEST (jamais vu pendant l'entrainement) ===")
print(f"Accuracy test : {accuracy:.4f} ({accuracy*100:.2f}%)")
print(f"Loss test : {loss:.4f}")

# ---------------------------------------------------------
# 3. Predictions detaillees pour la matrice de confusion
# ---------------------------------------------------------
y_vrai = []
y_pred = []

for images, labels in test_ds:
    predictions = model.predict(images, verbose=0)
    y_vrai.extend(np.argmax(labels.numpy(), axis=1))
    y_pred.extend(np.argmax(predictions, axis=1))

y_vrai = np.array(y_vrai)
y_pred = np.array(y_pred)

# ---------------------------------------------------------
# 4. Rapport de precision par classe
# ---------------------------------------------------------
print("\n=== PRECISION PAR CLASSE ===")
print(classification_report(y_vrai, y_pred, target_names=CLASSES, digits=3))

# ---------------------------------------------------------
# 5. Matrice de confusion (image sauvegardee pour le rapport)
# ---------------------------------------------------------
cm = confusion_matrix(y_vrai, y_pred)

fig, ax = plt.subplots(figsize=(8, 7))
im = ax.imshow(cm, cmap="Blues")

ax.set_xticks(range(len(CLASSES)))
ax.set_yticks(range(len(CLASSES)))
ax.set_xticklabels(CLASSES, rotation=45, ha="right")
ax.set_yticklabels(CLASSES)
ax.set_xlabel("Categorie predite")
ax.set_ylabel("Categorie reelle")
ax.set_title("Matrice de confusion - modele EcoSort")

for i in range(len(CLASSES)):
    for j in range(len(CLASSES)):
        couleur = "white" if cm[i, j] > cm.max() / 2 else "black"
        ax.text(j, i, str(cm[i, j]), ha="center", va="center", color=couleur)

fig.colorbar(im)
plt.tight_layout()
plt.savefig("model/matrice_confusion.png", dpi=150)
print("\nMatrice de confusion sauvegardee : model/matrice_confusion.png")

# ---------------------------------------------------------
# 6. Focus sur les confusions les plus frequentes (hors diagonale)
# ---------------------------------------------------------
print("\n=== TOP CONFUSIONS (vraie classe -> classe predite) ===")
confusions = []
for i in range(len(CLASSES)):
    for j in range(len(CLASSES)):
        if i != j and cm[i, j] > 0:
            confusions.append((cm[i, j], CLASSES[i], CLASSES[j]))

confusions.sort(reverse=True)
for nombre, vraie, predite in confusions[:8]:
    print(f"  {vraie} confondu avec {predite} : {nombre} fois")