"""AI dashboard page for training and evaluation artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st

from app.config import REPORTS_DIR
from app.model_metadata import load_model_metadata


EVALUATION_REPORT_PATH = REPORTS_DIR / "evaluation_report.json"
CLASSIFICATION_REPORT_PATH = REPORTS_DIR / "classification_report.txt"
CONFUSION_MATRIX_PATH = REPORTS_DIR / "confusion_matrix.png"
TRAINING_CURVES_PATH = REPORTS_DIR / "training_curves.png"
GRADCAM_PATH = REPORTS_DIR / "gradcam_plastic.png"


def load_json_report(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None

    return json.loads(path.read_text(encoding="utf-8"))


def format_percent(value: Any) -> str:
    if isinstance(value, int | float):
        return f"{value:.1%}"
    return "non disponible"


def classification_rows(evaluation_report: dict[str, Any] | None) -> list[dict[str, str]]:
    if not evaluation_report:
        return []

    report = evaluation_report.get("classification_report", {})
    rows: list[dict[str, str]] = []
    for class_name, metrics in report.items():
        if not isinstance(metrics, dict) or class_name in {"macro avg", "weighted avg"}:
            continue

        rows.append(
            {
                "Classe": class_name,
                "Precision": format_percent(metrics.get("precision")),
                "Recall": format_percent(metrics.get("recall")),
                "F1-score": format_percent(metrics.get("f1-score")),
                "Support": str(int(metrics.get("support", 0))),
            }
        )

    return rows


def render_missing_report(path: Path) -> None:
    st.warning(f"Artefact absent : `{path.as_posix()}`")


def render_metric_strip(evaluation_report: dict[str, Any] | None, metadata: dict[str, Any] | None) -> None:
    report = (evaluation_report or {}).get("classification_report", {})
    final_metrics = (metadata or {}).get("final_metrics", {})
    macro_avg = report.get("macro avg", {})
    weighted_avg = report.get("weighted avg", {})

    kpi_cols = st.columns(4)
    kpi_cols[0].metric("Accuracy validation", format_percent(report.get("accuracy") or final_metrics.get("val_accuracy")))
    kpi_cols[1].metric("Macro F1", format_percent(macro_avg.get("f1-score")))
    kpi_cols[2].metric("Weighted F1", format_percent(weighted_avg.get("f1-score")))
    kpi_cols[3].metric("Images test", str(int(weighted_avg.get("support", 0))) if weighted_avg else "non disponible")


def render_dashboard_page() -> None:
    metadata = load_model_metadata()
    evaluation_report = load_json_report(EVALUATION_REPORT_PATH)

    model_name = (metadata or {}).get("model_name", "Modele IA")
    architecture = (metadata or {}).get("architecture", "architecture non documentee")

    st.markdown(
        f"""
        <div class="ecosort-kicker">Dashboard IA</div>
        <h1 class="dashboard-title">{model_name}</h1>
        <p class="dashboard-subtitle">
            Suivi des performances du modele, artefacts d'entrainement et preuve visuelle Grad-CAM.
        </p>
        <div class="status-line">Architecture : {architecture}</div>
        """,
        unsafe_allow_html=True,
    )

    render_metric_strip(evaluation_report, metadata)

    st.divider()

    st.subheader("Diagnostic par classe")
    rows = classification_rows(evaluation_report)
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    elif CLASSIFICATION_REPORT_PATH.exists():
        st.code(CLASSIFICATION_REPORT_PATH.read_text(encoding="utf-8"), language="text")
    else:
        render_missing_report(CLASSIFICATION_REPORT_PATH)

    st.divider()

    matrix_col, curves_col = st.columns(2)
    with matrix_col:
        st.subheader("Matrice de confusion")
        if CONFUSION_MATRIX_PATH.exists():
            st.image(str(CONFUSION_MATRIX_PATH), use_column_width=True)
        else:
            render_missing_report(CONFUSION_MATRIX_PATH)

    with curves_col:
        st.subheader("Courbes d'entrainement")
        if TRAINING_CURVES_PATH.exists():
            st.image(str(TRAINING_CURVES_PATH), use_column_width=True)
        else:
            render_missing_report(TRAINING_CURVES_PATH)

    st.divider()

    st.subheader("Exemple Grad-CAM")
    gradcam_col, note_col = st.columns([1.4, 1])
    with gradcam_col:
        if GRADCAM_PATH.exists():
            st.image(str(GRADCAM_PATH), use_column_width=True)
        else:
            render_missing_report(GRADCAM_PATH)

    with note_col:
        st.markdown(
            """
            **Lecture rapide**

            Grad-CAM met en evidence les zones de l'image qui influencent le plus la prediction.
            Ici, l'objectif est de montrer que le modele ne se limite pas a un score : il fournit
            aussi une trace visuelle exploitable pour expliquer son choix.
            """
        )
