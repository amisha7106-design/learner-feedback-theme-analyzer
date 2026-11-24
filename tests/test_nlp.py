from src.nlp import FeedbackNLP, build_theme_clusters

def test_clean_text_removes_url_and_email():
    result = FeedbackNLP().clean_text("Great class! mail me a@b.com https://example.com")
    assert "https" not in result
    assert "a@b.com" not in result
    assert "great class" in result

def test_language_detection():
    nlp = FeedbackNLP()
    assert nlp.detect_language("यह बहुत अच्छा है") == "Hindi"
    assert nlp.detect_language("This class is helpful") == "English"

def test_sentiment():
    nlp = FeedbackNLP()
    assert nlp.analyse_sentiment("great helpful excellent")[0] == "Positive"
    assert nlp.analyse_sentiment("poor confusing problem")[0] == "Negative"

def test_theme_clustering_returns_assignments():
    themes, labels = build_theme_clusters([
        "Python coding practice is helpful",
        "Python coding examples are useful",
        "Trainer explains biology clearly",
        "Biology lessons are clear"
    ], max_clusters=2)
    assert len(labels) == 4
    assert len(themes) >= 1
