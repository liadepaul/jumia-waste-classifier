import tensorflow as tf
from tensorflow.keras import layers, models
import numpy as np
import os
import json

# ---------------------------------------------------------
# 1. Configuration
# ---------------------------------------------------------
TAILLE_IMAGE = (224, 224)   # taille attendue par MobileNetV2
BATCH_SIZE = 32
EPOCHS = 30                  # EarlyStopping arretera avant si besoin
RACINE = "data/split"

CLASSES = ["cardboard", "glass", "metal", "paper", "plastic", "trash"]

# Mapping classe Kaggle -> categorie couleur du contrat
MAPPING_COULEUR = {
    "cardboard": "jaune",
    "metal": "jaune",
    "plastic": "jaune",
    "glass": "vert",
    "paper": "bleu",
    "trash": "marron",
}

# ---------------------------------------------------------
# 2. Chargement des donnees
# ---------------------------------------------------------
train_ds = tf.keras.utils.image_dataset_from_directory(
    os.path.join(RACINE, "train"),
    labels="inferred",
    label_mode="categorical",
    class_names=CLASSES,
    image_size=TAILLE_IMAGE,
    batch_size=BATCH_SIZE,
    shuffle=True,
    seed=42,
)

val_ds = tf.keras.utils.image_dataset_from_directory(
    os.path.join(RACINE, "validation"),
    labels="inferred",
    label_mode="categorical",
    class_names=CLASSES,
    image_size=TAILLE_IMAGE,
    batch_size=BATCH_SIZE,
    shuffle=False,
)

# Optimisation : garde les images en memoire cache et precharge le batch suivant
# pendant que le GPU/CPU traite le batch actuel (accelere l'entrainement)
AUTOTUNE = tf.data.AUTOTUNE
train_ds = train_ds.cache().prefetch(buffer_size=AUTOTUNE)
val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)

# ---------------------------------------------------------
# 3. Poids des classes (compense le desequilibre de "trash")
# ---------------------------------------------------------
# Compte les images par classe dans le dossier train
comptes = {}
for classe in CLASSES:
    dossier = os.path.join(RACINE, "train", classe)
    comptes[classe] = len(os.listdir(dossier))

total = sum(comptes.values())
n_classes = len(CLASSES)

# Formule standard : poids inversement proportionnel a la frequence de la classe
class_weight = {
    i: total / (n_classes * comptes[classe])
    for i, classe in enumerate(CLASSES)
}
print("Poids par classe :", {CLASSES[i]: round(w, 2) for i, w in class_weight.items()})

# ---------------------------------------------------------
# 4. Construction du modele (Transfer Learning MobileNetV2)
# ---------------------------------------------------------
base_model = tf.keras.applications.MobileNetV2(
    input_shape=TAILLE_IMAGE + (3,),
    include_top=False,       # on retire la derniere couche (adaptee a ImageNet, pas a nous)
    weights="imagenet",
)
base_model.trainable = False  # on gele le reseau pre-entraine pour cette baseline

inputs = tf.keras.Input(shape=TAILLE_IMAGE + (3,))
x = tf.keras.applications.mobilenet_v2.preprocess_input(inputs)  # normalisation attendue par MobileNetV2
x = base_model(x, training=False)
x = layers.GlobalAveragePooling2D()(x)
x = layers.Dropout(0.3)(x)   # limite le sur-apprentissage
outputs = layers.Dense(n_classes, activation="softmax")(x)

model = models.Model(inputs, outputs)

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
    loss="categorical_crossentropy",
    metrics=["accuracy"],
)

model.summary()

# ---------------------------------------------------------
# 5. Entrainement
# ---------------------------------------------------------
callbacks = [
    tf.keras.callbacks.EarlyStopping(
        monitor="val_accuracy", patience=5, restore_best_weights=True
    ),
    tf.keras.callbacks.ModelCheckpoint(
        "model/modele_eco_sort.h5", monitor="val_accuracy", save_best_only=True
    ),
]

historique = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=EPOCHS,
    class_weight=class_weight,
    callbacks=callbacks,
)

# ---------------------------------------------------------
# 6. Sauvegarde de l'historique (utile pour les graphiques du rapport)
# ---------------------------------------------------------
with open("model/historique_entrainement.json", "w") as f:
    json.dump(historique.history, f)

print("\nEntrainement termine. Modele sauvegarde dans model/modele_eco_sort.h5")