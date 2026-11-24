import json
from .config import OPENAI_API_KEY, OPENAI_MODEL

class ReportGenerator:
    """Creates a grounded report. Uses OpenAI when a valid key is configured."""

    def _build_context(self, dashboard: dict) -> dict:
        excerpts = []
        for row in dashboard["feedback"][:30]:
            excerpts.append({
                "course": row["course_name"],
                "trainer": row["trainer_name"],
                "sentiment": row["sentiment"] or "Not analysed",
                # Only anonymized sample excerpts; no learner ID is sent.
                "feedback_excerpt": row["feedback_text"][:240],
            })
        return {
            "total_feedback": dashboard["total"],
            "sentiment_counts": dashboard["sentiments"],
            "theme_counts": dashboard["themes"],
            "anonymized_excerpts": excerpts,
        }

    def generate(self, dashboard: dict) -> dict:
        context = self._build_context(dashboard)
        if not OPENAI_API_KEY:
            return {
                "provider": "Offline template",
                "model": "local-fallback",
                "status": "offline_fallback",
                "text": self._fallback_report(context),
            }

        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            prompt = (
                "You are an education quality analyst. Use ONLY the supplied JSON data. "
                "Do not invent causes, statistics, quotes, or facts. If evidence is limited, say so. "
                "Write a balanced report with: Executive Summary, Positive Signals, Improvement Areas, "
                "Recurring Themes, Representative Feedback (short anonymized excerpts), and Recommended "
                "Human-Reviewed Actions. Include counts where supplied. Do not identify learners. "
                "Return clear Markdown.\n\nDATA:\n" + json.dumps(context, ensure_ascii=False)
            )
            response = client.responses.create(model=OPENAI_MODEL, input=prompt)
            output = getattr(response, "output_text", "").strip()
            if not output:
                raise ValueError("The API returned an empty report.")
            return {
                "provider": "OpenAI",
                "model": OPENAI_MODEL,
                "status": "api_success",
                "text": output,
            }
        except Exception as exc:
            # Keep the app usable, but make the API failure visible in report metadata.
            return {
                "provider": "Offline template",
                "model": "local-fallback",
                "status": f"api_error: {type(exc).__name__}",
                "text": self._fallback_report(context),
            }

    @staticmethod
    def _fallback_report(data: dict) -> str:
        sentiment = {x["sentiment"]: x["count"] for x in data["sentiment_counts"]}
        lines = [
            "# Learner Feedback Analysis Report",
            "",
            "## Executive Summary",
            f"- Total feedback responses analysed: **{data['total_feedback']}**",
            f"- Positive: **{sentiment.get('Positive', 0)}** | Negative: **{sentiment.get('Negative', 0)}** | Neutral: **{sentiment.get('Neutral', 0)}**",
            "",
            "## Recurring Themes",
        ]
        if data["theme_counts"]:
            lines += [f"- {x['theme_name']}: {x['count']} response(s)" for x in data["theme_counts"]]
        else:
            lines.append("- No theme data is available yet.")
        lines += ["", "## Representative Feedback"]
        if data["anonymized_excerpts"]:
            lines += [f"- ({x['sentiment']}) “{x['feedback_excerpt']}”" for x in data["anonymized_excerpts"][:8]]
        else:
            lines.append("- No excerpts available.")
        lines += [
            "",
            "## Recommended Human-Reviewed Actions",
            "- Review recurring negative themes with the relevant academic team.",
            "- Compare feedback across courses and trainers before deciding on changes.",
            "- Collect another feedback cycle to check whether actions improve learner experience.",
            "",
            "_This report is generated from the supplied sample and is a decision-support aid. "
            "A human reviewer must verify findings before taking action._",
        ]
        return "\n".join(lines)
