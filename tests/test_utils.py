import pytest
from src.utils import validate_feedback_rows

def test_valid_feedback_row_is_normalized():
    rows = validate_feedback_rows([{"feedback_text": "  Great lesson!  "}])
    assert rows[0]["feedback_text"] == "Great lesson!"
    assert rows[0]["course_name"] == "General"

def test_empty_feedback_rows_raise_error():
    with pytest.raises(ValueError):
        validate_feedback_rows([])

def test_blank_feedback_is_skipped():
    with pytest.raises(ValueError):
        validate_feedback_rows([{"feedback_text": "   "}])

def test_missing_optional_fields_get_defaults():
    row = validate_feedback_rows([{"feedback_text": "Helpful"}])[0]
    assert row["trainer_name"] == "Not specified"
    assert row["learner_id"] == "sample_1"

def test_multiple_rows_are_preserved():
    rows = validate_feedback_rows([{"feedback_text":"A"},{"feedback_text":"B"}])
    assert len(rows) == 2

def test_non_dictionary_row_is_rejected():
    with pytest.raises(ValueError):
        validate_feedback_rows(["not a row"])
