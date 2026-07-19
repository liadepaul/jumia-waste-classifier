"""PDF report generation for EcoSort-Search."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from textwrap import wrap
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from app.dashboard import CONFUSION_MATRIX_PATH, EVALUATION_REPORT_PATH, GRADCAM_PATH, TRAINING_CURVES_PATH, load_json_report
from app.model_metadata import load_model_metadata


PAGE_SIZE = (1240, 1754)
MARGIN = 86
GREEN = "#1F8A4C"
PALE_GREEN = "#E8F3EC"
INK = "#18201B"
MUTED = "#5C6A60"
LINE = "#D7E2DA"


def _font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "arialbd.ttf" if bold else "arial.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _new_page(title: str) -> tuple[Image.Image, ImageDraw.ImageDraw, int]:
    page = Image.new("RGB", PAGE_SIZE, "white")
    draw = ImageDraw.Draw(page)
    draw.rectangle([0, 0, PAGE_SIZE[0], 18], fill=GREEN)
    draw.text((MARGIN, 58), title, fill=INK, font=_font(42, bold=True))
    return page, draw, 132


def _wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    max_chars: int,
    font: ImageFont.ImageFont,
    fill: str = INK,
    spacing: int = 10,
) -> int:
    for paragraph in text.split("\n"):
        lines = wrap(paragraph, width=max_chars) or [""]
        for line in lines:
            draw.text((x, y), line, fill=fill, font=font)
            y += int(font.size * 1.2) + spacing
        y += spacing
    return y


def _metric(value: Any, default: str = "Non disponible") -> str:
    if isinstance(value, int | float):
        return f"{value:.1%}" if 0 <= value <= 1 else f"{value:.2f}"
    return str(value) if value not in (None, "") else default


def _draw_metric_table(draw: ImageDraw.ImageDraw, rows: list[tuple[str, str]], x: int, y: int) -> int:
    label_font = _font(25, bold=True)
    value_font = _font(25)
    row_h = 58
    width = PAGE_SIZE[0] - (2 * MARGIN)
    draw.rounded_rectangle([x, y, x + width, y + row_h * len(rows)], radius=18, fill="#F6FAF7", outline=LINE, width=2)
    for index, (label, value) in enumerate(rows):
        top = y + row_h * index
        if index:
            draw.line([x, top, x + width, top], fill=LINE, width=2)
        draw.rectangle([x, top, x + 310, top + row_h], fill=PALE_GREEN)
        draw.text((x + 24, top + 15), label, fill=INK, font=label_font)
        draw.text((x + 340, top + 15), value, fill=INK, font=value_font)
    return y + row_h * len(rows) + 42


def _paste_artifact(page: Image.Image, draw: ImageDraw.ImageDraw, path: Path, title: str, x: int, y: int) -> int:
    title_font = _font(28, bold=True)
    body_font = _font(22)
    draw.text((x, y), title, fill=INK, font=title_font)
    y += 44

    if not path.exists():
        draw.rounded_rectangle([x, y, PAGE_SIZE[0] - MARGIN, y + 120], radius=16, fill="#FAFAFA", outline=LINE, width=2)
        draw.text((x + 24, y + 42), "Artefact non disponible dans le dossier reports.", fill=MUTED, font=body_font)
        return y + 154

    with Image.open(path) as image:
        image = image.convert("RGB")
        image.thumbnail((PAGE_SIZE[0] - (2 * MARGIN), 390), Image.Resampling.LANCZOS)
        draw.rounded_rectangle([x, y, x + image.width + 28, y + image.height + 28], radius=18, fill="#FAFAFA", outline=LINE, width=2)
        page.paste(image, (x + 14, y + 14))
        return y + image.height + 64


def _build_summary_page(history: list[dict[str, Any]]) -> Image.Image:
    page, draw, y = _new_page("EcoSort-Search - Rapport IA")
    body_font = _font(25)
    heading_font = _font(30, bold=True)

    y = _wrapped(
        draw,
        "Resume du modele, preuves d'entrainement, dernieres analyses utilisateur et recommandations environnementales.",
        MARGIN,
        y,
        70,
        body_font,
        fill=MUTED,
    )

    metadata = load_model_metadata() or {}
    evaluation = load_json_report(EVALUATION_REPORT_PATH) or {}
    report = evaluation.get("classification_report", {})

    accuracy = report.get("accuracy") or metadata.get("final_metrics", {}).get("val_accuracy")
    macro_f1 = report.get("macro avg", {}).get("f1-score")
    weighted_f1 = report.get("weighted avg", {}).get("f1-score")
    total = report.get("weighted avg", {}).get("support")
    class_names = metadata.get("class_names") or ["cardboard", "glass", "metal", "paper", "plastic", "trash"]

    rows = [
        ("Modele", str(metadata.get("model_name", "EcoSort MobileNetV2"))),
        ("Architecture", str(metadata.get("architecture", "MobileNetV2 transfer learning"))),
        ("Classes", ", ".join(class_names)),
        ("Accuracy", _metric(accuracy)),
        ("Macro F1", _metric(macro_f1)),
        ("Weighted F1", _metric(weighted_f1)),
        ("Images test", str(int(total)) if isinstance(total, int | float) else "Non disponible"),
        ("Analyses session", str(len(history))),
    ]
    y = _draw_metric_table(draw, rows, MARGIN, y + 8)

    draw.text((MARGIN, y), "Recommandations environnementales", fill=INK, font=heading_font)
    y += 48
    recommendations = [
        "Reduire les produits a usage unique et privilegier les objets reutilisables.",
        "Separer les D3E des dechets ordinaires pour eviter la pollution toxique.",
        "Garder les emballages propres et secs pour ameliorer leur recyclabilite.",
        "Comparer les alternatives durables avant l'achat quand l'EcoScore est faible.",
    ]
    for item in recommendations:
        draw.ellipse([MARGIN, y + 10, MARGIN + 12, y + 22], fill=GREEN)
        y = _wrapped(draw, item, MARGIN + 34, y, 72, body_font, fill=INK, spacing=5)

    return page


def _build_artifacts_page() -> Image.Image:
    page, draw, y = _new_page("Preuves visuelles du modele")
    artifacts = [
        (CONFUSION_MATRIX_PATH, "Matrice de confusion"),
        (TRAINING_CURVES_PATH, "Courbes d'entrainement"),
        (GRADCAM_PATH, "Exemple Grad-CAM"),
    ]
    for path, title in artifacts:
        y = _paste_artifact(page, draw, Path(path), title, MARGIN, y + 10)
    return page


def _build_history_page(history: list[dict[str, Any]]) -> Image.Image:
    page, draw, y = _new_page("Historique intelligent")
    header_font = _font(21, bold=True)
    body_font = _font(20)
    cols = [MARGIN, 250, 505, 735, 945]
    headers = ["Date", "Element", "Tri", "Confiance", "EcoScore"]

    draw.rounded_rectangle([MARGIN, y, PAGE_SIZE[0] - MARGIN, y + 58], radius=14, fill=GREEN)
    for index, header in enumerate(headers):
        draw.text((cols[index] + 12, y + 17), header, fill="white", font=header_font)
    y += 58

    if not history:
        _wrapped(
            draw,
            "Aucune analyse utilisateur enregistree pendant cette session.",
            MARGIN,
            y + 36,
            70,
            body_font,
            fill=MUTED,
        )
        return page

    for row_index, entry in enumerate(history[:18]):
        row_h = 62
        top = y + row_h * row_index
        fill = "#F6FAF7" if row_index % 2 == 0 else "white"
        draw.rectangle([MARGIN, top, PAGE_SIZE[0] - MARGIN, top + row_h], fill=fill)
        values = [
            str(entry.get("date", ""))[:17],
            str(entry.get("item", ""))[:28],
            str(entry.get("bin_label", ""))[:22],
            str(entry.get("confidence", ""))[:10],
            str(entry.get("ecoscore", "")),
        ]
        for index, value in enumerate(values):
            draw.text((cols[index] + 12, top + 18), value, fill=INK, font=body_font)
        draw.line([MARGIN, top + row_h, PAGE_SIZE[0] - MARGIN, top + row_h], fill=LINE, width=1)

    return page


def generate_pdf_report(history: list[dict[str, Any]]) -> bytes:
    """Build a compact PDF report with model metrics, visuals and recent predictions."""

    pages = [
        _build_summary_page(history),
        _build_artifacts_page(),
        _build_history_page(history),
    ]
    buffer = BytesIO()
    pages[0].save(buffer, format="PDF", resolution=150, save_all=True, append_images=pages[1:])
    return buffer.getvalue()
