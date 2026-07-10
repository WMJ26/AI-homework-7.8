import pytest
from fixlot.feedback.parser import TestFailure
from fixlot.feedback.classifier import FailureType, ClassifiedFailure
from fixlot.feedback.correction import generate_correction_hint


class TestGenerateCorrectionHint:
    def test_assertion_error_hint(self):
        failures = [
            ClassifiedFailure(
                test_name="test_add",
                category=FailureType.ASSERTION_ERROR,
                message="assert 3 == 2",
                traceback="test_math.py:5: AssertionError",
            )
        ]
        hint = generate_correction_hint(failures)
        assert "test_add" in hint
        assert "assertion" in hint.lower()

    def test_import_error_hint(self):
        failures = [
            ClassifiedFailure(
                test_name="test_import",
                category=FailureType.IMPORT_ERROR,
                message="ModuleNotFoundError: No module named 'requests'",
                traceback="test_import.py:1: ModuleNotFoundError",
            )
        ]
        hint = generate_correction_hint(failures)
        assert "import" in hint.lower()

    def test_syntax_error_hint(self):
        failures = [
            ClassifiedFailure(
                test_name="test_broken",
                category=FailureType.SYNTAX_ERROR,
                message="SyntaxError: invalid syntax",
                traceback="test_broken.py:12: SyntaxError",
            )
        ]
        hint = generate_correction_hint(failures)
        assert "syntax" in hint.lower()

    def test_multiple_failures_hint(self):
        failures = [
            ClassifiedFailure("test_a", FailureType.ASSERTION_ERROR, "msg", "tb"),
            ClassifiedFailure("test_b", FailureType.TYPE_ERROR, "msg", "tb"),
        ]
        hint = generate_correction_hint(failures)
        assert "test_a" in hint
        assert "test_b" in hint
        assert "2 failure" in hint.lower()

    def test_hint_is_non_empty_string(self):
        failures = [
            ClassifiedFailure("test_x", FailureType.UNKNOWN, "error", "tb"),
        ]
        hint = generate_correction_hint(failures)
        assert isinstance(hint, str)
        assert len(hint) > 0