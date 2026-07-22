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
# Data augmentation : appliquee uniquement pendant l'entrainement
data_augmentation = tf.keras.Sequential([
    layers.RandomFlip("horizontal"),
    layers.RandomRotation(0.1),
    layers.RandomZoom(0.1),
    layers.RandomContrast(0.1),
], name="augmentation")
x = data_augmentation(inputs)
x = layers.Rescaling(scale=1./127.5, offset=-1, name="preprocessing")(x)
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
# ---------------------------------------------------------
# 5a. Premiere phase : tete gelee (comme la baseline)
# ---------------------------------------------------------
callbacks = [
    tf.keras.callbacks.EarlyStopping(
        monitor="val_accuracy", patience=5, restore_best_weights=True
    ),
    tf.keras.callbacks.ModelCheckpoint(
        "model/modele_eco_sort.h5", monitor="val_accuracy", save_best_only=True
    ),
]

print("\n=== PHASE 1 : entrainement tete gelee ===")
historique_1 = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=EPOCHS,
    class_weight=class_weight,
    callbacks=callbacks,
)

# ---------------------------------------------------------
# 5b. Deuxieme phase : fine-tuning des dernieres couches
# ---------------------------------------------------------
print("\n=== PHASE 2 : fine-tuning des dernieres couches de MobileNetV2 ===")

base_model.trainable = True
# On ne degele que les 30 dernieres couches (les plus "specifiques"),
# les premieres couches (formes/textures generiques) restent gelees
for couche in base_model.layers[:-30]:
    couche.trainable = False

meilleur_val_acc_phase1 = max(historique_1.history["val_accuracy"])
print(f"Meilleure val_accuracy phase 1 : {meilleur_val_acc_phase1:.4f}")

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),  # taux tres faible !
    loss="categorical_crossentropy",
    metrics=["accuracy"],
)

# Nouveaux callbacks : ModelCheckpoint sait desormais qu'il doit battre
# le score de la phase 1 pour ecraser le fichier .h5, pas juste ameliorer
# a partir de zero
callbacks_finetuning = [
    tf.keras.callbacks.EarlyStopping(
        monitor="val_accuracy", patience=5, restore_best_weights=True
    ),
    tf.keras.callbacks.ModelCheckpoint(
        "model/modele_eco_sort.h5", monitor="val_accuracy", save_best_only=True,
        initial_value_threshold=meilleur_val_acc_phase1
    ),
]

EPOCHS_FINETUNING = 15
historique_2 = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=EPOCHS_FINETUNING,
    class_weight=class_weight,
    callbacks=callbacks_finetuning,
)

# Fusionne les historiques des 2 phases pour les graphiques
historique = {
    k: historique_1.history[k] + historique_2.history[k]
    for k in historique_1.history
}

# ---------------------------------------------------------
# 6. Sauvegarde de l'historique (utile pour les graphiques du rapport)
# ---------------------------------------------------------
with open("model/historique_entrainement.json", "w") as f:
    json.dump(historique, f)
print("\nEntrainement termine. Modele sauvegarde dans model/modele_eco_sort.h5")