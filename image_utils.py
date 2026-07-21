"""Image download and preprocessing helpers."""

from __future__ import annotations

from io import BytesIO

import numpy as np
import requests
from PIL import Image

from app.config import IMAGE_SIZE, REQUEST_TIMEOUT_SECONDS


def download_image(image_url: str) -> Image.Image:
    """Download an image URL and return a RGB PIL image."""

    response = requests.get(image_url, timeout=REQUEST_TIMEOUT_SECONDS, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    return Image.open(BytesIO(response.content)).convert("RGB")


def preprocess_image(image: Image.Image, image_size: tuple[int, int] = IMAGE_SIZE) -> np.ndarray:
    """Resize and batch an image for Keras transfer-learning models."""

    resized = image.resize(image_size)
    array = np.asarray(resized, dtype=np.float32)
    array = np.expand_dims(array, axis=0)
    return array

