import os
import shutil
import random

random.seed(42)  # reproductibilité : même découpage à chaque exécution

SOURCE = "data/raw/Garbage classification/Garbage classification"
DEST = "data/split"
RATIOS = {"train": 0.70, "validation": 0.15, "test": 0.15}

for classe in os.listdir(SOURCE):
    dossier_classe = os.path.join(SOURCE, classe)
    if not os.path.isdir(dossier_classe):
        continue

    images = [f for f in os.listdir(dossier_classe)
              if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    random.shuffle(images)

    n = len(images)
    n_train = int(n * RATIOS["train"])
    n_val = int(n * RATIOS["validation"])

    decoupage = {
        "train": images[:n_train],
        "validation": images[n_train:n_train + n_val],
        "test": images[n_train + n_val:],
    }

    for split, fichiers in decoupage.items():
        dest_dir = os.path.join(DEST, split, classe)
        os.makedirs(dest_dir, exist_ok=True)
        for f in fichiers:
            shutil.copy(os.path.join(dossier_classe, f),
                        os.path.join(dest_dir, f))

    print(f"{classe}: {n} images -> "
          f"{n_train} train / {n_val} val / {n - n_train - n_val} test")