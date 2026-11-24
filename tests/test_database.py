from src.database import FeedbackDatabase

def test_database_creates_tables(tmp_path):
    db=FeedbackDatabase(str(tmp_path/"test.db"))
    with db.connect() as con:
        names={r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"courses","trainers","feedback_responses","feedback_themes","reports","audit_logs"}.issubset(names)

def test_add_feedback_batch_and_dashboard(tmp_path):
    db=FeedbackDatabase(str(tmp_path/"test.db"))
    count=db.add_feedback_batch([{"feedback_text":"Very useful class","course_name":"Science","trainer_name":"Teacher A","learner_id":"anon1"}])
    assert count == 1
    assert db.get_dashboard_data()["total"] == 1

def test_import_creates_audit_record(tmp_path):
    db=FeedbackDatabase(str(tmp_path/"test.db"))
    db.add_feedback_batch([{"feedback_text":"Good pace"}])
    with db.connect() as con:
        row=con.execute("SELECT action FROM audit_logs ORDER BY audit_id DESC LIMIT 1").fetchone()
    assert row[0] == "IMPORT_FEEDBACK"

def test_delete_all_feedback_clears_responses(tmp_path):
    db=FeedbackDatabase(str(tmp_path/"test.db"))
    db.add_feedback_batch([{"feedback_text":"Good pace"}])
    db.delete_all_feedback()
    assert db.get_dashboard_data()["total"] == 0

def test_save_and_list_report(tmp_path):
    db=FeedbackDatabase(str(tmp_path/"test.db"))
    db.save_report("Test", "# Report", "Offline", "local", "offline_fallback")
    assert db.list_reports()[0]["report_title"] == "Test"
