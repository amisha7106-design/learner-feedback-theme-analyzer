import pytest
from src.database import FeedbackDatabase
from src.analyzer import FeedbackAnalyzer

def test_analysis_requires_feedback(tmp_path):
    db=FeedbackDatabase(str(tmp_path/"test.db"))
    with pytest.raises(ValueError):
        FeedbackAnalyzer(db).run_analysis()
