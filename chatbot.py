"""Knowledge assistant for EcoSort-Search.

The assistant answers project questions locally and can enrich general answers
with a public encyclopedic knowledge base when the network is available.
"""

from __future__ import annotations

from dataclasses import dataclass
import html
import re
import unicodedata
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.config import REQUEST_TIMEOUT_SECONDS


KNOWLEDGE_API_BASE = "https://fr.wikipedia.org"
KNOWLEDGE_API_FALLBACK_BASE = "https://en.wikipedia.org"


@dataclass(frozen=True)
class ChatbotAnswer:
    answer: str
    source_label: str
    source_title: str = ""
    source_url: str = ""
    used_remote: bool = False


@dataclass(frozen=True)
class KnowledgeCandidate:
    title: str
    language: str


@dataclass(frozen=True)
class KnowledgeSummary:
    title: str
    extract: str
    content_url: str
    language: str


def _session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=2,
        connect=2,
        read=2,
        status=2,
        backoff_factor=0.25,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


HTTP_SESSION = _session()


def answer_chatbot_question(question: str) -> ChatbotAnswer:
    """Return a clear, robust answer for a user question."""

    cleaned_question = re.sub(r"\s+", " ", question).strip()
    if not cleaned_question:
        return ChatbotAnswer(
            answer="Pose une question sur le tri, le modele IA, Docker, l'EcoScore ou un objet a recycler.",
            source_label="Base EcoSort",
        )

    local_answer = _answer_project_question(cleaned_question)
    if local_answer is not None:
        return local_answer

    remote_answer = _answer_from_public_knowledge(cleaned_question)
    if remote_answer is not None:
        return remote_answer

    return ChatbotAnswer(
        answer=(
            "Je n'ai pas trouve de reponse assez fiable pour cette question. "
            "Essaie de reformuler avec un objet, une matiere ou un sujet lie au tri, "
            "au modele IA, a Docker ou a l'impact environnemental."
        ),
        source_label="Base EcoSort",
    )


def _answer_project_question(question: str) -> ChatbotAnswer | None:
    normalized = _normalize(question)

    if _is_source_question(normalized):
        return ChatbotAnswer(
            answer=(
                "Pour les questions du projet, j'utilise la base EcoSort : consignes de tri, "
                "EcoScore, modele IA, Docker et historique. Pour les questions generales, "
                "je peux consulter une base encyclopedique publique quand le reseau est disponible."
            ),
            source_label="Base EcoSort",
        )

    if _contains_any(normalized, {"docker", "compose", "conteneur", "container", "image docker"}):
        return ChatbotAnswer(
            answer=(
                "Pour lancer le projet comme le professeur : place-toi a la racine du dossier, puis execute "
                "`docker build -t ecosort .` et ensuite `docker run -p 8501:8501 ecosort`. "
                "Tu peux aussi utiliser `docker-compose up -d --build`. Ensuite ouvre "
                "`http://127.0.0.1:8501` dans le navigateur."
            ),
            source_label="Base EcoSort",
        )

    if _contains_any(normalized, {"ecoscore", "score eco", "score ecologique", "recyclabilite", "risque"}):
        return ChatbotAnswer(
            answer=(
                "L'EcoScore resume l'impact probable d'un produit sur 100. Il combine la matiere detectee, "
                "la recyclabilite, le niveau de risque environnemental et un conseil d'achat plus durable. "
                "Un score eleve signifie que le produit est plus facile a trier ou a valoriser."
            ),
            source_label="Base EcoSort",
        )

    if _contains_any(normalized, {"photo", "image", "camera", "upload", "importer", "analyse image"}):
        return ChatbotAnswer(
            answer=(
                "Dans la page Analyse image, tu peux importer une photo ou utiliser la camera. "
                "Le modele predit une classe parmi cardboard, glass, metal, paper, plastic et trash, "
                "puis l'application affiche la consigne de tri, la confiance, l'EcoScore et une explication IA."
            ),
            source_label="Base EcoSort",
        )

    if _contains_any(normalized, {"modele", "mobilenet", "accuracy", "precision", "gradcam", "dataset", "entrainement"}):
        return ChatbotAnswer(
            answer=(
                "Le modele utilise une architecture MobileNetV2 adaptee a la classification d'images. "
                "Il travaille sur six classes : cardboard, glass, metal, paper, plastic et trash. "
                "Le Dashboard IA presente l'accuracy, la matrice de confusion, les courbes d'entrainement "
                "et un exemple Grad-CAM pour expliquer visuellement les predictions."
            ),
            source_label="Base EcoSort",
        )

    if _contains_any(normalized, {"historique", "csv", "pdf", "rapport", "export"}):
        return ChatbotAnswer(
            answer=(
                "La page Historique conserve les analyses de la session avec la date, la source, "
                "la matiere detectee, la consigne, la confiance et l'EcoScore. Elle permet aussi "
                "d'exporter les resultats en CSV et de generer un rapport PDF de demonstration."
            ),
            source_label="Base EcoSort",
        )

    if _contains_any(
        normalized,
        {
            "tri",
            "trier",
            "dechet",
            "dechets",
            "poubelle",
            "plastique",
            "verre",
            "papier",
            "carton",
            "metal",
            "canette",
            "bouteille",
        },
    ):
        return ChatbotAnswer(
            answer=(
                "Regle pratique : le verre va dans la filiere verre, le papier et le carton propres "
                "dans la filiere papier/carton, les emballages plastiques et metaux selon les consignes locales, "
                "et les objets souilles ou non recyclables dans les dechets residuels. En cas de doute, "
                "l'application EcoSort donne une consigne et explique la raison."
            ),
            source_label="Base EcoSort",
        )

    return None


def _answer_from_public_knowledge(question: str) -> ChatbotAnswer | None:
    for language in ("fr", "en"):
        try:
            candidates = _search_public_knowledge(question, language=language)
        except requests.RequestException:
            continue

        for candidate in candidates:
            try:
                summary = _fetch_public_summary(candidate.title, language=candidate.language)
            except requests.RequestException:
                continue

            if not summary.extract:
                continue

            return ChatbotAnswer(
                answer=_format_public_answer(summary),
                source_label="Base de connaissances publique",
                source_title=summary.title,
                source_url=summary.content_url,
                used_remote=True,
            )

    return None


def _search_public_knowledge(question: str, language: str = "fr") -> list[KnowledgeCandidate]:
    base_url = KNOWLEDGE_API_BASE if language == "fr" else KNOWLEDGE_API_FALLBACK_BASE
    response = HTTP_SESSION.get(
        f"{base_url}/w/api.php",
        params={
            "action": "query",
            "list": "search",
            "format": "json",
            "srlimit": 3,
            "srsearch": question,
        },
        headers=_headers(language),
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()
    results = payload.get("query", {}).get("search", [])
    return [
        KnowledgeCandidate(title=str(result.get("title", "")).strip(), language=language)
        for result in results
        if str(result.get("title", "")).strip()
    ]


def _fetch_public_summary(title: str, language: str = "fr") -> KnowledgeSummary:
    base_url = KNOWLEDGE_API_BASE if language == "fr" else KNOWLEDGE_API_FALLBACK_BASE
    safe_title = quote(title.replace(" ", "_"), safe="")
    response = HTTP_SESSION.get(
        f"{base_url}/api/rest_v1/page/summary/{safe_title}",
        headers=_headers(language),
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()
    content_urls = payload.get("content_urls", {}).get("desktop", {})
    return KnowledgeSummary(
        title=str(payload.get("title") or title),
        extract=str(payload.get("extract") or "").strip(),
        content_url=str(content_urls.get("page") or ""),
        language=language,
    )


def _format_public_answer(summary: KnowledgeSummary) -> str:
    extract = _shorten(summary.extract, limit=620)
    if summary.language == "en":
        return (
            f"J'ai trouve une information pertinente sur **{summary.title}**. "
            f"{extract} Cette reponse peut etre completee avec une verification locale si le sujet touche "
            "aux consignes de tri de ta commune."
        )
    return (
        f"J'ai trouve une information pertinente sur **{summary.title}**. "
        f"{extract} Pour une consigne de tri precise, il faut toujours tenir compte des regles locales."
    )


def _headers(language: str) -> dict[str, str]:
    return {
        "User-Agent": "EcoSort-Search/1.0 (student academic project)",
        "Accept": "application/json",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8" if language == "fr" else "en-US,en;q=0.9,fr;q=0.7",
    }


def _contains_any(text: str, words: set[str]) -> bool:
    return any(word in text for word in words)


def _is_source_question(text: str) -> bool:
    if "wiki" in text or "wikipedia" in text:
        return True

    source_words = {"source", "sources", "origine", "provient", "donnees"}
    intent_words = {"ou", "quelle", "quelles", "vient", "viens", "utilise", "base"}
    return _contains_any(text, source_words) and _contains_any(text, intent_words)


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.casefold())
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", normalized).strip()


def _shorten(text: str, limit: int) -> str:
    cleaned = html.unescape(re.sub(r"\s+", " ", text)).strip()
    if len(cleaned) <= limit:
        return cleaned
    shortened = cleaned[:limit].rsplit(" ", 1)[0].rstrip(".,;:")
    return f"{shortened}..."
