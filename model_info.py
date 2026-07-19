"""Model documentation page."""

from __future__ import annotations

import streamlit as st

from app.config import CLASS_NAMES, REPORTS_DIR
from app.dashboard import load_json_report
from app.model_metadata import load_model_metadata


def render_model_info_page() -> None:
    metadata = load_model_metadata() or {}
    dataset = load_json_report(REPORTS_DIR / "dataset_manifest.json") or {}

    st.markdown(
        """
        <div class="ecosort-kicker">A propos du modele</div>
        <h1 class="dashboard-title">Maturite scientifique</h1>
        <p class="dashboard-subtitle">
            Origine des donnees, architecture, limites connues et pistes d'amelioration.
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Dataset utilise")
    st.write(f"Repertoire : `{dataset.get('dataset_dir', metadata.get('dataset_dir', 'non documente'))}`")
    st.write(f"Nombre total d'images : **{dataset.get('total_images', 'non disponible')}**")
    counts = dataset.get("class_counts", {})
    if counts:
        st.dataframe(
            [{"Classe": class_name, "Images": count} for class_name, count in counts.items()],
            use_container_width=True,
            hide_index=True,
        )

    st.subheader("Architecture")
    st.write(f"Modele : **{metadata.get('model_name', 'EcoSort MobileNetV2')}**")
    st.write(f"Architecture : **{metadata.get('architecture', 'MobileNetV2 transfer learning')}**")
    st.write(f"Taille d'image : **{metadata.get('image_size', [224, 224])}**")
    st.write(f"Classes : `{', '.join(metadata.get('class_names', CLASS_NAMES))}`")

    st.subheader("Limites du modele")
    st.write(
        "- Le modele reconnait des matieres visuelles, pas toutes les filieres locales de collecte.\n"
        "- Les produits multi-matieres peuvent etre difficiles a classer avec une seule image.\n"
        "- Les D3E sont detectes par regles metier sur le nom produit, car le dataset ne contient pas de classe electronique.\n"
        "- Une photo floue, sombre ou trop rapprochee peut reduire la confiance IA."
    )

    st.subheader("Pistes d'amelioration")
    st.write(
        "- Ajouter des images locales de dechets en Cote d'Ivoire.\n"
        "- Ajouter une classe dediee aux dechets electroniques et piles.\n"
        "- Entrainer un modele multi-label pour les objets composes de plusieurs matieres.\n"
        "- Connecter une base de points de collecte et des consignes municipales."
    )
