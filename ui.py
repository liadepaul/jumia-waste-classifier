"""Streamlit interface for EcoSort-Search."""

from __future__ import annotations

import html
from io import BytesIO
import sys
from pathlib import Path

from PIL import Image
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import DEFAULT_PRODUCT_LIMIT
from app.chatbot import answer_chatbot_question
from app.dashboard import render_dashboard_page
from app.ecoscore import EcoScore, compute_ecoscore
from app.fallback_data import fallback_products
from app.gradcam import generate_gradcam
from app.history import add_history_entry, get_history, history_to_csv
from app.mapping import SORT_INSTRUCTIONS
from app.model_metadata import model_status_label
from app.model_info import render_model_info_page
from app.predictor import PredictionResult, classify_product, classify_uploaded_image
from app.reporting import generate_pdf_report
from app.scraper import Product, available_marketplaces, get_marketplace, search_marketplace_products


NAVIGATION_OPTIONS = [
    "Recherche produit",
    "Analyse image",
    "Assistant IA",
    "Dashboard IA",
    "Historique",
    "A propos du modele",
]


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ink: #18201b;
            --muted: #65736a;
            --line: #dfe7df;
            --surface: #f7f8f4;
            --accent: #1f8a4c;
        }

        .stApp {
            background: var(--surface);
            color: var(--ink);
        }

        [data-testid="stHeader"] {
            background: rgba(247, 248, 244, 0.88);
            backdrop-filter: blur(10px);
        }

        .block-container {
            padding-top: 2.2rem;
            max-width: 1180px;
        }

        .ecosort-kicker {
            color: var(--accent);
            font-size: 0.82rem;
            font-weight: 760;
            letter-spacing: 0;
            text-transform: uppercase;
        }

        .ecosort-title {
            color: var(--ink);
            font-size: clamp(2.2rem, 5vw, 4.8rem);
            line-height: 0.96;
            font-weight: 840;
            letter-spacing: 0;
            margin: 0.2rem 0 1rem;
        }

        .ecosort-subtitle {
            color: var(--muted);
            font-size: 1.05rem;
            line-height: 1.55;
            max-width: 760px;
            margin-bottom: 1.4rem;
        }

        .dashboard-title {
            color: var(--ink);
            font-size: clamp(2rem, 4vw, 3.6rem);
            line-height: 1;
            font-weight: 830;
            letter-spacing: 0;
            margin: 0.2rem 0 0.8rem;
        }

        .dashboard-subtitle {
            color: var(--muted);
            font-size: 1.03rem;
            line-height: 1.55;
            max-width: 760px;
            margin-bottom: 1.2rem;
        }

        .status-line {
            border-top: 1px solid var(--line);
            border-bottom: 1px solid var(--line);
            padding: 0.8rem 0;
            color: var(--muted);
            font-size: 0.94rem;
            margin: 0.8rem 0 1.2rem;
        }

        div[data-testid="stButton"] > button,
        div[data-testid="stFormSubmitButton"] > button,
        div[data-testid="stDownloadButton"] > button {
            border-radius: 8px;
            border: 1px solid #1d6f43;
            background: #1f8a4c;
            color: white;
            font-weight: 720;
            min-height: 2.85rem;
        }

        div[data-testid="stButton"] > button:hover,
        div[data-testid="stFormSubmitButton"] > button:hover,
        div[data-testid="stDownloadButton"] > button:hover {
            border-color: #145f38;
            background: #176d3c;
            color: white;
        }

        .product-row {
            border-top: 1px solid var(--line);
            padding: 1rem 0;
        }

        .product-name {
            font-size: 1.04rem;
            font-weight: 730;
            color: var(--ink);
            margin-bottom: 0.2rem;
        }

        .product-price {
            color: var(--muted);
            font-weight: 650;
        }

        .result-panel {
            border-radius: 8px;
            padding: 1.4rem;
            margin-top: 1rem;
        }

        .result-label {
            font-size: clamp(1.7rem, 3vw, 3.2rem);
            line-height: 1;
            font-weight: 850;
            letter-spacing: 0;
            margin-bottom: 0.75rem;
        }

        .result-meta {
            font-size: 1rem;
            line-height: 1.5;
            max-width: 760px;
        }

        .ecoscore-line {
            color: var(--muted);
            font-size: 0.92rem;
            margin-top: 0.35rem;
        }

        .source-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            border: 1px solid var(--line);
            border-radius: 999px;
            color: var(--muted);
            font-size: 0.78rem;
            font-weight: 720;
            padding: 0.16rem 0.55rem;
            margin-bottom: 0.45rem;
            background: rgba(255, 255, 255, 0.58);
        }

        .source-dot {
            width: 0.48rem;
            height: 0.48rem;
            border-radius: 50%;
            background: var(--accent);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_navigation() -> str:
    if st.session_state.get("navigation_page") not in NAVIGATION_OPTIONS:
        st.session_state["navigation_page"] = NAVIGATION_OPTIONS[0]

    return st.radio(
        "Navigation",
        options=NAVIGATION_OPTIONS,
        horizontal=True,
        key="navigation_page",
        label_visibility="collapsed",
    )


def render_header() -> None:
    model_status = model_status_label()
    st.markdown(
        f"""
        <div class="ecosort-kicker">EcoSort-Search</div>
        <h1 class="ecosort-title">Recherche produit. Consigne de tri.</h1>
        <p class="ecosort-subtitle">
            Saisis un produit, choisis une source, puis l'application determine la filiere
            de tri avec le modele IA et les regles metier D3E.
        </p>
        <div class="status-line">Etat systeme : {model_status}</div>
        """,
        unsafe_allow_html=True,
    )
    render_source_strip()


def render_source_strip() -> None:
    logo_path = PROJECT_ROOT / "assets" / "jumia-logo.png"
    jumia_col, coin_col, note_col = st.columns([1, 1.2, 3.2], vertical_alignment="center")
    with jumia_col:
        if logo_path.exists():
            st.image(str(logo_path), width=112)
        st.caption("Jumia")
    with coin_col:
        st.markdown(
            """
            <div class="source-badge"><span class="source-dot"></span>CoinAfrique</div>
            """,
            unsafe_allow_html=True,
        )
    with note_col:
        st.caption("Recherche live avec cache rapide, retries HTTP et fallback de demonstration si une source bloque.")


@st.cache_data(ttl=300, show_spinner=False)
def search_products(query: str, source_key: str) -> list[Product]:
    return search_marketplace_products(query, source_key=source_key, limit=DEFAULT_PRODUCT_LIMIT)


def search_products_with_fallback(query: str, source_key: str) -> list[Product]:
    marketplace = get_marketplace(source_key)
    label = "les sites selectionnes" if source_key == "all" else marketplace.label
    try:
        with st.spinner(f"Recherche sur {label}..."):
            products = search_products(query, source_key)
    except Exception:
        st.info(f"{label} est indisponible pour le moment. Mode demo active pour continuer la demonstration.")
        return fallback_products(query, limit=DEFAULT_PRODUCT_LIMIT, source_key=source_key)

    if products:
        return products

    st.info(f"Aucun resultat exploitable sur {label}. Mode demo active pour continuer la demonstration.")
    return fallback_products(query, limit=DEFAULT_PRODUCT_LIMIT, source_key=source_key)


def render_product(product: Product) -> None:
    text_result = classify_product(product.name, "")
    ecoscore = compute_ecoscore(product.name, text_result.material, text_result.instruction)
    left, middle, right = st.columns([1.1, 4.2, 1.2], vertical_alignment="center")
    with left:
        if product.image_url:
            st.image(product.image_url, use_column_width=True)
    with middle:
        safe_name = html.escape(product.name)
        safe_price = html.escape(product.price)
        safe_source = html.escape(product.source)
        safe_risk = html.escape(ecoscore.risk_level)
        st.markdown(
            f"""
            <div class="product-row">
                <div class="source-badge"><span class="source-dot"></span>{safe_source}</div>
                <div class="product-name">{safe_name}</div>
                <div class="product-price">{safe_price}</div>
                <div class="ecoscore-line">EcoScore : <strong>{ecoscore.score}/100</strong> - {safe_risk}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.link_button(f"Voir sur {product.source}", product.product_url)
    with right:
        st.caption(f"{text_result.instruction.label}")


def render_ecoscore(ecoscore: EcoScore) -> None:
    st.subheader("EcoScore")
    score_col, detail_col = st.columns([1, 3], vertical_alignment="center")
    with score_col:
        st.metric("Score", f"{ecoscore.score}/100")
        st.progress(ecoscore.score / 100)
    with detail_col:
        st.write(f"**Recyclabilite :** {ecoscore.recyclability}")
        st.write(f"**Risque :** {ecoscore.risk_level}")
        st.write(f"**Conseil :** {ecoscore.advice}")
        st.write(f"**Alternative :** {ecoscore.alternative}")


def render_explanation(
    item_name: str,
    result: PredictionResult,
    ecoscore: EcoScore,
    image: Image.Image | None = None,
    source_label: str | None = None,
) -> None:
    confidence = f"{result.confidence:.1%}" if result.confidence is not None else "non disponible"
    st.subheader("Explication IA")
    st.write(f"**Classe predite :** {result.material or 'non determinee'}")
    st.write(f"**Confiance :** {confidence}")
    st.write(f"**Consigne :** {result.instruction.label} - {result.instruction.bin_name}")
    st.write(f"**Pourquoi :** {result.instruction.explanation}")
    st.write(f"**Conseil durable :** {ecoscore.advice}")

    if image is not None:
        gradcam = generate_gradcam(image)
        if gradcam is not None:
            st.image(gradcam, caption="Grad-CAM genere pour cette image", use_column_width=True)
        else:
            st.info("Grad-CAM dynamique indisponible pour cette image. Exemple de reference disponible dans le Dashboard IA.")

    add_history_entry(
        source=source_label or ("Image" if image is not None else "Produit"),
        item=item_name,
        material=result.material,
        bin_label=result.instruction.label,
        confidence=result.confidence,
        ecoscore=ecoscore.score,
        advice=ecoscore.advice,
    )


def render_result(product: Product) -> None:
    result = classify_product(product.name, product.image_url)
    instruction = result.instruction
    ecoscore = compute_ecoscore(product.name, result.material, instruction)
    confidence_label = ""
    if result.confidence is not None:
        confidence_label = f" - confiance IA : {result.confidence:.1%}"

    st.markdown(
        f"""
        <div class="result-panel" style="background:{instruction.hex_color}; color:{instruction.text_color};">
            <div class="result-label">{instruction.label}</div>
            <div class="result-meta">
                <strong>{instruction.bin_name}</strong><br>
                {instruction.explanation}<br>
                Matiere detectee : {result.material or "non determinee"} - source : {result.source}{confidence_label}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    image = None
    if product.image_url:
        try:
            from app.image_utils import download_image

            image = download_image(product.image_url)
        except Exception:
            image = None
    render_ecoscore(ecoscore)
    render_explanation(product.name, result, ecoscore, image, source_label=product.source)


def render_search_controls() -> tuple[bool, str, str]:
    with st.form("product_search_form", clear_on_submit=False):
        source_col, search_col, action_col = st.columns([1.5, 3.5, 1], vertical_alignment="bottom")
        with source_col:
            source_key = st.selectbox(
                "Site",
                options=[key for key, _ in available_marketplaces(include_all=True)],
                format_func=lambda key: "Tous les sites" if key == "all" else get_marketplace(key).label,
                key="source_key",
            )
        with search_col:
            query = st.text_input(
                "Produit a rechercher",
                key="search_query",
                placeholder="Exemple : bouteille plastique, smartphone, cahier...",
            )
        with action_col:
            submitted = st.form_submit_button("Rechercher", use_container_width=True, type="primary")

    return submitted, query, source_key


def render_search_page() -> None:
    render_header()

    submitted, raw_query, source_key = render_search_controls()
    query = raw_query.strip()

    if submitted:
        st.session_state.pop("selected_product", None)
        st.session_state.pop("selected_product_index", None)

        if not query:
            st.session_state["products"] = []
            st.warning("Saisis d'abord un nom de produit.")
        else:
            st.session_state["products"] = search_products_with_fallback(query, source_key)
            st.session_state["last_query"] = query
            st.session_state["last_source_key"] = source_key

    products = st.session_state.get("products", [])
    if products:
        last_source = st.session_state.get("last_source_key", source_key)
        marketplace = get_marketplace(last_source)
        logo_path = PROJECT_ROOT / marketplace.logo_path if marketplace.logo_path else None
        title_col, logo_col = st.columns([4, 1], vertical_alignment="center")
        with title_col:
            st.subheader("Produits trouves")
        with logo_col:
            if last_source != "all" and logo_path and logo_path.exists():
                st.image(str(logo_path), width=118)
            else:
                st.caption("Sources multiples" if last_source == "all" else marketplace.label)
        selected_index = st.selectbox(
            "Choisir un produit a analyser",
            options=list(range(len(products))),
            format_func=lambda index: products[index].name,
            key="selected_product_index",
        )

        selected_product = products[selected_index]
        st.session_state["selected_product"] = selected_product

        st.subheader("Consigne de tri")
        render_result(selected_product)

        for product in products:
            render_product(product)
    elif submitted and query:
        st.warning("Aucun produit trouve. Essaie un mot-cle plus simple.")

    with st.expander("Categories officielles du projet"):
        for instruction in SORT_INSTRUCTIONS.values():
            st.write(f"**{instruction.label}** - {instruction.explanation}")


def _read_uploaded_image(uploaded_file) -> Image.Image:
    return Image.open(BytesIO(uploaded_file.getvalue())).convert("RGB")


def render_image_analysis_page() -> None:
    st.markdown(
        """
        <div class="ecosort-kicker">Analyse image</div>
        <h1 class="dashboard-title">Photo du dechet. Prediction directe.</h1>
        <p class="dashboard-subtitle">
            Importe une image ou prends une photo : le modele predit la matiere et affiche la consigne.
        </p>
        """,
        unsafe_allow_html=True,
    )

    upload_col, camera_col = st.columns(2)
    with upload_col:
        uploaded_file = st.file_uploader("Importer une image", type=["jpg", "jpeg", "png", "webp"])
    with camera_col:
        camera_file = st.camera_input("Prendre une photo")

    selected_file = camera_file or uploaded_file
    if selected_file is None:
        st.info("Ajoute une image pour lancer la prediction.")
        return

    image = _read_uploaded_image(selected_file)
    st.image(image, caption="Image analysee", use_column_width=True)

    result = classify_uploaded_image(image)
    ecoscore = compute_ecoscore("Image importee", result.material, result.instruction)
    render_result_panel(result)
    render_ecoscore(ecoscore)
    render_explanation("Image importee", result, ecoscore, image, source_label="Image")


def render_chatbot_page() -> None:
    st.markdown(
        """
        <div class="ecosort-kicker">Assistant IA</div>
        <h1 class="dashboard-title">Questions sur le tri, l'IA et les objets</h1>
        <p class="dashboard-subtitle">
            Pose une question courte. L'assistant combine les informations EcoSort
            et une base de connaissances publique pour repondre clairement.
        </p>
        """,
        unsafe_allow_html=True,
    )

    if "chatbot_messages" not in st.session_state:
        st.session_state["chatbot_messages"] = [
            {
                "role": "assistant",
                "content": (
                    "Bonjour. Je peux expliquer une consigne de tri, le modele IA, Docker, "
                    "l'EcoScore ou un objet precis."
                ),
                "source": "Base EcoSort",
            }
        ]

    with st.form("chatbot_form", clear_on_submit=True):
        question = st.text_input(
            "Question",
            placeholder="Exemple : comment trier une bouteille plastique ?",
            key="chatbot_question",
        )
        submitted = st.form_submit_button("Envoyer", use_container_width=True, type="primary")

    if submitted:
        cleaned_question = question.strip()
        if cleaned_question:
            answer = answer_chatbot_question(cleaned_question)
            st.session_state["chatbot_messages"].append({"role": "user", "content": cleaned_question, "source": ""})
            st.session_state["chatbot_messages"].append(
                {
                    "role": "assistant",
                    "content": answer.answer,
                    "source": answer.source_label,
                }
            )
        else:
            st.warning("Ecris une question avant d'envoyer.")

    for message in st.session_state["chatbot_messages"]:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if message.get("source"):
                st.caption(f"Source : {message['source']}")

    with st.expander("Exemples de questions"):
        st.write("comment lancer Docker ?")
        st.write("comment trier une bouteille plastique ?")
        st.write("qu'est-ce que MobileNetV2 ?")
        st.write("pourquoi utiliser un EcoScore ?")


def render_result_panel(result: PredictionResult) -> None:
    instruction = result.instruction
    confidence_label = ""
    if result.confidence is not None:
        confidence_label = f" - confiance IA : {result.confidence:.1%}"

    st.markdown(
        f"""
        <div class="result-panel" style="background:{instruction.hex_color}; color:{instruction.text_color};">
            <div class="result-label">{instruction.label}</div>
            <div class="result-meta">
                <strong>{instruction.bin_name}</strong><br>
                {instruction.explanation}<br>
                Matiere detectee : {result.material or "non determinee"} - source : {result.source}{confidence_label}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_history_page() -> None:
    st.markdown(
        """
        <div class="ecosort-kicker">Historique intelligent</div>
        <h1 class="dashboard-title">Analyses recentes et exports</h1>
        <p class="dashboard-subtitle">
            Les predictions de la session sont conservees ici avec leur consigne, confiance et EcoScore.
        </p>
        """,
        unsafe_allow_html=True,
    )
    history = get_history()
    if history:
        st.dataframe(history, use_container_width=True, hide_index=True)
    else:
        st.info("Aucune analyse enregistree pour cette session.")

    export_col, report_col = st.columns(2)
    with export_col:
        st.download_button(
            "Exporter CSV",
            data=history_to_csv(history),
            file_name="ecosort_historique.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with report_col:
        st.download_button(
            "Generer rapport PDF",
            data=generate_pdf_report(history),
            file_name="ecosort_rapport_ia.pdf",
            mime="application/pdf",
            use_container_width=True,
        )


def main() -> None:
    inject_styles()
    page = render_navigation()

    if page == "Dashboard IA":
        render_dashboard_page()
    elif page == "Analyse image":
        render_image_analysis_page()
    elif page == "Assistant IA":
        render_chatbot_page()
    elif page == "Historique":
        render_history_page()
    elif page == "A propos du modele":
        render_model_info_page()
    else:
        render_search_page()


if __name__ == "__main__":
    main()
