"""Central configuration for EcoSort-Search."""

from __future__ import annotations

import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = Path(os.getenv("ECOSORT_MODEL_PATH", ROOT_DIR / "models" / "modele_eco_sort.h5"))
REPORTS_DIR = ROOT_DIR / "reports"
JUMIA_BASE_URL = os.getenv("JUMIA_BASE_URL", "https://www.jumia.ci")
COINAFRIQUE_BASE_URL = os.getenv("COINAFRIQUE_BASE_URL", "https://ci.coinafrique.com")

IMAGE_SIZE = (224, 224)
CLASS_NAMES = ["cardboard", "glass", "metal", "paper", "plastic", "trash"]

REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "8"))
DEFAULT_PRODUCT_LIMIT = 5
