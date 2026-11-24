import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from .config import DB_PATH

class FeedbackDatabase:
    """SQLite repository for feedback, analysis themes and generated reports."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.create_tables()

    def connect(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def create_tables(self):
        schema = """
        CREATE TABLE IF NOT EXISTS courses (
            course_id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_name TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS trainers (
            trainer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            trainer_name TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS feedback_forms (
            form_id INTEGER PRIMARY KEY AUTOINCREMENT,
            form_name TEXT NOT NULL,
            course_id INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY(course_id) REFERENCES courses(course_id)
        );
        CREATE TABLE IF NOT EXISTS feedback_responses (
            response_id INTEGER PRIMARY KEY AUTOINCREMENT,
            form_id INTEGER,
            learner_id TEXT,
            course_id INTEGER,
            trainer_id INTEGER,
            feedback_text TEXT NOT NULL,
            cleaned_text TEXT,
            language TEXT,
            sentiment TEXT,
            sentiment_score REAL,
            theme_id INTEGER,
            submitted_at TEXT,
            status TEXT NOT NULL DEFAULT 'processed',
            created_at TEXT NOT NULL,
            FOREIGN KEY(form_id) REFERENCES feedback_forms(form_id),
            FOREIGN KEY(course_id) REFERENCES courses(course_id),
            FOREIGN KEY(trainer_id) REFERENCES trainers(trainer_id)
        );
        CREATE TABLE IF NOT EXISTS feedback_themes (
            theme_id INTEGER PRIMARY KEY AUTOINCREMENT,
            theme_name TEXT NOT NULL,
            keywords TEXT,
            feedback_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS reports (
            report_id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_title TEXT NOT NULL,
            report_text TEXT NOT NULL,
            provider TEXT NOT NULL,
            model TEXT,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS audit_logs (
            audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            details TEXT,
            created_at TEXT NOT NULL
        );
        """
        with self.connect() as con:
            con.executescript(schema)

    @staticmethod
    def now():
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def _get_or_create(self, con, table, column, value):
        row = con.execute(f"SELECT {table[:-1] if table.endswith('s') else table}_id FROM {table} WHERE {column} = ?", (value,)).fetchone()
        if row:
            return row[0]
        id_col = {"courses": "course_id", "trainers": "trainer_id"}[table]
        cur = con.execute(f"INSERT INTO {table} ({column}, created_at) VALUES (?, ?)", (value, self.now()))
        return cur.lastrowid

    def add_feedback_batch(self, rows: list[dict]) -> int:
        inserted = 0
        with self.connect() as con:
            form_cur = con.execute(
                "INSERT INTO feedback_forms(form_name, created_at) VALUES (?, ?)",
                ("Imported feedback batch", self.now())
            )
            form_id = form_cur.lastrowid
            for row in rows:
                course_id = self._get_or_create(con, "courses", "course_name", str(row.get("course_name") or "General").strip() or "General")
                trainer_id = self._get_or_create(con, "trainers", "trainer_name", str(row.get("trainer_name") or "Not specified").strip() or "Not specified")
                con.execute("""
                    INSERT INTO feedback_responses
                    (form_id, learner_id, course_id, trainer_id, feedback_text, submitted_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (form_id, str(row.get("learner_id") or "anonymous"), course_id, trainer_id,
                      str(row.get("feedback_text", "")).strip(), row.get("submitted_at"), self.now()))
                inserted += 1
            con.execute("INSERT INTO audit_logs(action, details, created_at) VALUES (?, ?, ?)",
                        ("IMPORT_FEEDBACK", json.dumps({"count": inserted}), self.now()))
        return inserted

    def get_unprocessed_feedback(self):
        with self.connect() as con:
            rows = con.execute("""
                SELECT r.response_id, r.feedback_text, c.course_name, t.trainer_name
                FROM feedback_responses r
                LEFT JOIN courses c ON c.course_id=r.course_id
                LEFT JOIN trainers t ON t.trainer_id=r.trainer_id
                WHERE r.cleaned_text IS NULL
                ORDER BY r.response_id
            """).fetchall()
            return [dict(row) for row in rows]

    def save_analysis(self, response_id: int, cleaned_text: str, language: str,
                      sentiment: str, sentiment_score: float, theme_id: int | None):
        with self.connect() as con:
            con.execute("""
                UPDATE feedback_responses
                SET cleaned_text=?, language=?, sentiment=?, sentiment_score=?, theme_id=?, status='processed'
                WHERE response_id=?
            """, (cleaned_text, language, sentiment, sentiment_score, theme_id, response_id))

    def replace_themes(self, themes: list[dict]):
        with self.connect() as con:
            con.execute("UPDATE feedback_responses SET theme_id=NULL")
            con.execute("DELETE FROM feedback_themes")
            ids = []
            for theme in themes:
                cur = con.execute("""
                    INSERT INTO feedback_themes(theme_name, keywords, feedback_count, created_at)
                    VALUES (?, ?, ?, ?)
                """, (theme["theme_name"], json.dumps(theme["keywords"]), theme["feedback_count"], self.now()))
                ids.append(cur.lastrowid)
            return ids

    def assign_themes(self, response_ids: list[int], theme_ids: list[int]):
        with self.connect() as con:
            for response_id, theme_id in zip(response_ids, theme_ids):
                con.execute("UPDATE feedback_responses SET theme_id=? WHERE response_id=?", (theme_id, response_id))

    def get_dashboard_data(self):
        with self.connect() as con:
            total = con.execute("SELECT COUNT(*) FROM feedback_responses").fetchone()[0]
            sentiment_rows = con.execute("""
                SELECT COALESCE(sentiment,'Not analysed') AS sentiment, COUNT(*) AS count
                FROM feedback_responses GROUP BY sentiment
            """).fetchall()
            theme_rows = con.execute("""
                SELECT COALESCE(th.theme_name,'Unassigned') AS theme_name, COUNT(r.response_id) AS count
                FROM feedback_responses r LEFT JOIN feedback_themes th ON th.theme_id=r.theme_id
                GROUP BY th.theme_name ORDER BY count DESC
            """).fetchall()
            recent = con.execute("""
                SELECT r.response_id, r.feedback_text, r.sentiment, r.language,
                       COALESCE(c.course_name,'General') course_name,
                       COALESCE(t.trainer_name,'Not specified') trainer_name
                FROM feedback_responses r
                LEFT JOIN courses c ON c.course_id=r.course_id
                LEFT JOIN trainers t ON t.trainer_id=r.trainer_id
                ORDER BY r.response_id DESC LIMIT 100
            """).fetchall()
            return {
                "total": total,
                "sentiments": [dict(x) for x in sentiment_rows],
                "themes": [dict(x) for x in theme_rows],
                "feedback": [dict(x) for x in recent],
            }

    def save_report(self, title: str, report_text: str, provider: str, model: str, status: str):
        with self.connect() as con:
            cur = con.execute("""
                INSERT INTO reports(report_title, report_text, provider, model, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (title, report_text, provider, model, status, self.now()))
            con.execute("INSERT INTO audit_logs(action, details, created_at) VALUES (?, ?, ?)",
                        ("REPORT_CREATED", json.dumps({"report_id": cur.lastrowid, "provider": provider}), self.now()))
            return cur.lastrowid

    def list_reports(self):
        with self.connect() as con:
            return [dict(r) for r in con.execute(
                "SELECT * FROM reports ORDER BY report_id DESC"
            ).fetchall()]

    def delete_all_feedback(self):
        """Demo reset: deletes feedback and its dependent theme/report data."""
        with self.connect() as con:
            con.execute("DELETE FROM feedback_responses")
            con.execute("DELETE FROM feedback_themes")
            con.execute("DELETE FROM feedback_forms")
            con.execute("DELETE FROM reports")
            con.execute("INSERT INTO audit_logs(action, details, created_at) VALUES (?, ?, ?)",
                        ("DEMO_RESET", "Feedback, themes and reports cleared", self.now()))
