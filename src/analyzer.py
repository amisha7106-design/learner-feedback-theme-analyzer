from .nlp import FeedbackNLP, build_theme_clusters


class FeedbackAnalyzer:

    def __init__(self, database):
        self.database = database
        self.nlp = FeedbackNLP()

    def run_analysis(self, max_clusters: int = 5) -> dict:

        # Step 1: Get feedback that has not been analysed yet
        rows = self.database.get_unprocessed_feedback()

        # Step 2: If no pending feedback exists, fetch all saved feedback
        if not rows:
            with self.database.connect() as con:
                rows = [
                    dict(row)
                    for row in con.execute(
                        """
                        SELECT
                            fr.response_id,
                            fr.feedback_text,
                            c.course_name,
                            t.trainer_name
                        FROM feedback_responses AS fr
                        LEFT JOIN courses AS c
                            ON fr.course_id = c.course_id
                        LEFT JOIN trainers AS t
                            ON fr.trainer_id = t.trainer_id
                        ORDER BY fr.response_id
                        """
                    ).fetchall()
                ]

        # Step 3: Check whether feedback exists
        if not rows:
            raise ValueError(
                "Import feedback before running analysis."
            )

        # Step 4: Perform NLP analysis
        analyses = [
            self.nlp.analyse_one(row["feedback_text"])
            for row in rows
        ]

        # Step 5: Prepare text for theme clustering
        texts = [
            item["cleaned_text"] or "empty feedback"
            for item in analyses
        ]

        # Step 6: Identify recurring themes
        themes, labels = build_theme_clusters(
            texts,
            max_clusters=max_clusters
        )

        # Step 7: Save themes in database
        theme_ids = self.database.replace_themes(themes)

        theme_id_by_label = {
            theme["cluster_label"]: theme_ids[index]
            for index, theme in enumerate(themes)
        }

        # Step 8: Save individual feedback analysis
        for index, (row, result) in enumerate(
            zip(rows, analyses)
        ):

            theme_id = theme_id_by_label[labels[index]]

            self.database.save_analysis(
                response_id=row["response_id"],
                cleaned_text=result["cleaned_text"],
                language=result["language"],
                sentiment=result["sentiment"],
                sentiment_score=result["sentiment_score"],
                theme_id=theme_id
            )

        # Step 9: Return analysis summary
        return {
            "processed": len(rows),

            "positive": sum(
                item["sentiment"] == "Positive"
                for item in analyses
            ),

            "negative": sum(
                item["sentiment"] == "Negative"
                for item in analyses
            ),

            "neutral": sum(
                item["sentiment"] == "Neutral"
                for item in analyses
            ),

            "themes": themes
        }     