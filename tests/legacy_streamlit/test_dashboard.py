from app.dashboard import classification_rows, format_percent


def test_dashboard_page_renders_with_artifacts():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file("streamlit_app.py")
    app.run(timeout=30)
    app.radio[0].set_value("Dashboard IA")
    app.run(timeout=30)

    assert not app.exception
    assert any(metric.label == "Accuracy validation" and metric.value == "81.8%" for metric in app.metric)
    assert any(metric.label == "Macro F1" and metric.value == "79.9%" for metric in app.metric)
    assert len(app.dataframe) == 1


def test_new_navigation_pages_render_without_exception():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file("streamlit_app.py")
    expected_content = {
        "Analyse image": "Photo du dechet. Prediction directe.",
        "Assistant IA": "Questions sur le tri, l'IA et les objets",
        "Historique": "Analyses recentes et exports",
        "A propos du modele": "Maturite scientifique",
    }
    for page, title in expected_content.items():
        app.run(timeout=30)
        app.radio[0].set_value(page)
        app.run(timeout=30)
        assert not app.exception
        assert app.radio[0].value == page
        assert any(title in markdown.value for markdown in app.markdown)


def test_chatbot_page_answers_from_form():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file("streamlit_app.py")
    app.run(timeout=30)
    app.radio[0].set_value("Assistant IA")
    app.run(timeout=30)
    app.text_input[0].set_value("comment lancer docker ?")
    app.button[0].click()
    app.run(timeout=30)

    assert not app.exception
    assert app.radio[0].value == "Assistant IA"
    assert any("docker build -t ecosort ." in markdown.value for markdown in app.markdown)
    assert any("Source : Base EcoSort" in caption.value for caption in app.caption)


def test_format_percent_formats_numeric_values():
    assert format_percent(0.817821) == "81.8%"


def test_format_percent_handles_missing_values():
    assert format_percent(None) == "non disponible"


def test_classification_rows_extracts_only_material_classes():
    report = {
        "classification_report": {
            "plastic": {"precision": 0.7, "recall": 0.8, "f1-score": 0.75, "support": 12.0},
            "macro avg": {"precision": 0.7, "recall": 0.8, "f1-score": 0.75, "support": 12.0},
            "accuracy": 0.82,
        }
    }

    assert classification_rows(report) == [
        {
            "Classe": "plastic",
            "Precision": "70.0%",
            "Recall": "80.0%",
            "F1-score": "75.0%",
            "Support": "12",
        }
    ]
