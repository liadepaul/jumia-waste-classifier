import requests

from app.chatbot import (
    ChatbotAnswer,
    KnowledgeCandidate,
    KnowledgeSummary,
    answer_chatbot_question,
)


def test_chatbot_answers_project_docker_question():
    answer = answer_chatbot_question("comment lancer docker ?")

    assert isinstance(answer, ChatbotAnswer)
    assert "docker build -t ecosort ." in answer.answer
    assert "docker run -p 8501:8501 ecosort" in answer.answer
    assert answer.source_label == "Base EcoSort"
    assert answer.used_remote is False


def test_chatbot_does_not_confuse_product_information_with_source_question():
    answer = answer_chatbot_question("donne moi des informations sur le plastique")

    assert "Regle pratique" in answer.answer
    assert answer.source_label == "Base EcoSort"


def test_chatbot_answers_public_knowledge_question(monkeypatch):
    def fake_search(question, language="fr"):
        return [KnowledgeCandidate(title="Energie solaire", language=language)]

    def fake_summary(title, language="fr"):
        return KnowledgeSummary(
            title=title,
            extract="L'energie solaire est une source d'energie issue du rayonnement du soleil.",
            content_url="https://example.test/energie-solaire",
            language=language,
        )

    monkeypatch.setattr("app.chatbot._search_public_knowledge", fake_search)
    monkeypatch.setattr("app.chatbot._fetch_public_summary", fake_summary)

    answer = answer_chatbot_question("qu'est-ce que l'energie solaire ?")

    assert "Energie solaire" in answer.answer
    assert "rayonnement du soleil" in answer.answer
    assert answer.source_label == "Base de connaissances publique"
    assert answer.used_remote is True


def test_chatbot_has_helpful_fallback_when_network_fails(monkeypatch):
    def fake_search(question, language="fr"):
        raise requests.RequestException("network unavailable")

    monkeypatch.setattr("app.chatbot._search_public_knowledge", fake_search)

    answer = answer_chatbot_question("question generale impossible a trouver")

    assert "reformuler" in answer.answer
    assert answer.source_label == "Base EcoSort"
    assert answer.used_remote is False
