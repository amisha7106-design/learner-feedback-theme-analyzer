import re


# =========================================
# FEEDBACK NLP
# =========================================

class FeedbackNLP:
    """Text cleaning, language detection and sentiment analysis."""

    POSITIVE_WORDS = {
        "good", "great", "excellent", "helpful", "clear",
        "love", "best", "understand", "amazing",
        "supportive", "interesting",
        "अच्छा", "अच्छी", "बहुत", "शानदार", "मदद"
    }

    NEGATIVE_WORDS = {
        "bad", "poor", "confusing", "difficult", "slow",
        "late", "issue", "problem", "boring", "unclear",
        "worst", "समस्या", "मुश्किल", "खराब", "धीमा",
        "नहीं"
    }

    def clean_text(self, text: str) -> str:
        if not isinstance(text, str):
            raise TypeError("Feedback must be text.")

        text = text.strip().lower()

        text = re.sub(r"https?://\S+|www\.\S+", " ", text)

        text = re.sub(
            r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b",
            " ",
            text
        )

        text = re.sub(
            r"[^\w\s']",
            " ",
            text,
            flags=re.UNICODE
        )

        return re.sub(r"\s+", " ", text).strip()

    def detect_language(self, text: str) -> str:
        devanagari = sum(
            "\u0900" <= ch <= "\u097F"
            for ch in text
        )

        latin = sum(
            "a" <= ch.lower() <= "z"
            for ch in text
        )

        if devanagari > 0 and devanagari >= latin:
            return "Hindi"

        if latin > 0:
            return "English"

        return "Unknown"

    def analyse_sentiment(self, text: str) -> tuple[str, float]:
        tokens = re.findall(
            r"\w+",
            text.lower(),
            flags=re.UNICODE
        )

        positive = sum(
            token in self.POSITIVE_WORDS
            for token in tokens
        )

        negative = sum(
            token in self.NEGATIVE_WORDS
            for token in tokens
        )

        total = positive + negative

        if total == 0:
            return "Neutral", 0.0

        score = (positive - negative) / total

        if score > 0:
            label = "Positive"
        elif score < 0:
            label = "Negative"
        else:
            label = "Neutral"

        return label, round(score, 3)

    def analyse_one(self, text: str) -> dict:
        cleaned = self.clean_text(text)
        language = self.detect_language(text)

        sentiment, score = self.analyse_sentiment(cleaned)

        return {
            "cleaned_text": cleaned,
            "language": language,
            "sentiment": sentiment,
            "sentiment_score": score
        }


# =========================================
# SMART THEME NAMING
# =========================================

THEME_RULES = {
    "Practical Learning": [
        "practical", "project", "projects",
        "example", "examples", "database",
        "hands on"
    ],

    "Trainer Support": [
        "trainer", "teacher", "teaching",
        "supportive", "explains", "explain",
        "question", "questions"
    ],

    "Study Material": [
        "notes", "material", "revision",
        "revise", "videos", "video",
        "content", "resources"
    ],

    "Course Scheduling": [
        "schedule", "scheduling", "timing",
        "time", "late"
    ],

    "Assignments & Assessment": [
        "assignment", "assignments",
        "assessment", "instructions",
        "task", "tasks", "exam"
    ],

    "Interactive Activities": [
        "activities", "activity",
        "interactive", "discussion",
        "engagement", "engaging"
    ]
}


def get_theme_name(cluster_text: str, keywords: list[str]) -> str:
    """Generate meaningful English theme names."""

    content = (
        cluster_text + " " + " ".join(keywords)
    ).lower()

    content = re.sub(
        r"[\u0900-\u097F]+",
        " ",
        content
    )

    scores = {}

    for theme, terms in THEME_RULES.items():
        scores[theme] = sum(
            1 for term in terms
            if re.search(
                r"\b" + re.escape(term) + r"\b",
                content
            )
        )

    best_theme = max(scores, key=scores.get)

    if scores[best_theme] > 0:
        return best_theme

    return "General Learning Experience"


# =========================================
# TF-IDF + KMEANS THEME CLUSTERING
# =========================================

def build_theme_clusters(
    texts: list[str],
    max_clusters: int = 5
):
    """Discover feedback themes and assign readable names."""

    if not texts:
        return [], []

    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans

    theme_texts = [
        re.sub(r"[\u0900-\u097F]+", " ", text)
        for text in texts
    ]

    vectorizer = TfidfVectorizer(
        stop_words="english",
        max_features=1000,
        ngram_range=(1, 2),
        min_df=1
    )

    try:
        matrix = vectorizer.fit_transform(theme_texts)

    except ValueError:
        return [{
            "cluster_label": 0,
            "theme_name": "General Learning Experience",
            "keywords": [],
            "feedback_count": len(texts)
        }], [0] * len(texts)

    distinct = len(set(theme_texts))

    n_clusters = max(
        1,
        min(max_clusters, len(texts), distinct)
    )

    if n_clusters == 1:
        labels = [0] * len(texts)

    else:
        model = KMeans(
            n_clusters=n_clusters,
            random_state=42,
            n_init=10
        )

        labels = model.fit_predict(matrix).tolist()

    terms = vectorizer.get_feature_names_out()

    themes = []

    for cluster_id in sorted(set(labels)):

        indexes = [
            i for i, label in enumerate(labels)
            if label == cluster_id
        ]

        cluster_matrix = matrix[indexes]
        mean_scores = cluster_matrix.mean(axis=0).A1

        top_indices = mean_scores.argsort()[::-1][:5]

        keywords = [
            str(terms[i])
            for i in top_indices
            if mean_scores[i] > 0
        ]

        cluster_text = " ".join(
            theme_texts[i]
            for i in indexes
        )

        # Use smart theme naming
        name = get_theme_name(
            cluster_text,
            keywords
        )

        themes.append({
            "cluster_label": int(cluster_id),
            "theme_name": name,
            "keywords": keywords,
            "feedback_count": len(indexes)
        })

    return themes, [int(x) for x in labels]