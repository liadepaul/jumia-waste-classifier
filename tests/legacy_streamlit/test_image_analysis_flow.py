from io import BytesIO

from PIL import Image

from app.ecoscore import compute_ecoscore
from app.gradcam import generate_gradcam
from app.predictor import classify_uploaded_image
from app.ui import _read_uploaded_image


class FakeUpload:
    def __init__(self, data: bytes):
        self._data = data

    def getvalue(self) -> bytes:
        return self._data


def test_uploaded_or_camera_image_runs_full_analysis_flow():
    image = Image.open("reports/gradcam_plastic.png").convert("RGB")
    buffer = BytesIO()
    image.save(buffer, format="PNG")

    uploaded_image = _read_uploaded_image(FakeUpload(buffer.getvalue()))
    result = classify_uploaded_image(uploaded_image)
    ecoscore = compute_ecoscore("Image importee", result.material, result.instruction)
    gradcam = generate_gradcam(uploaded_image)

    assert uploaded_image.mode == "RGB"
    assert result.material == "plastic"
    assert result.confidence is not None
    assert result.instruction.label == "Poubelle jaune"
    assert ecoscore.score == 58
    assert gradcam is not None
