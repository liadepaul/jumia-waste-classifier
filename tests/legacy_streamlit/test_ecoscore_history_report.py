from app.ecoscore import compute_ecoscore
from app.history import history_to_csv
from app.mapping import classify_from_text_or_material
from app.reporting import generate_pdf_report


def test_plastic_ecoscore_has_actionable_advice():
    instruction = classify_from_text_or_material("bouteille plastique", "plastic")
    score = compute_ecoscore("bouteille plastique", "plastic", instruction)

    assert score.score < 70
    assert "plastique" in score.recyclability.casefold()
    assert score.alternative


def test_electronic_ecoscore_uses_dedicated_collection():
    instruction = classify_from_text_or_material("smartphone avec chargeur", "plastic")
    score = compute_ecoscore("smartphone avec chargeur", "plastic", instruction)

    assert instruction.code == "electronic"
    assert "D3E" in score.recyclability


def test_history_to_csv_exports_rows():
    data = history_to_csv(
        [
            {
                "date": "2026-07-11 10:00:00",
                "source": "Jumia",
                "item": "Bouteille plastique",
                "material": "plastic",
                "bin_label": "Poubelle jaune",
                "confidence": "88.0%",
                "ecoscore": 58,
                "advice": "Reduire l'usage unique.",
            }
        ]
    )

    assert "Bouteille plastique".encode("utf-8") in data
    assert "ecoscore".encode("utf-8") in data


def test_generate_pdf_report_returns_pdf_bytes():
    pdf = generate_pdf_report([])

    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000
