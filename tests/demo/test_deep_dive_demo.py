"""
Mechanism Demo 3: Deep dive - the complete feedback pipeline.

This test demonstrates the full feedback pipeline (parser -> classifier ->
correction -> loop) working deterministically with mock LLM, proving
that every step is code, not prompt engineering.
"""
from fixlot.feedback.parser import parse_pytest_output
from fixlot.feedback.classifier import classify_failures, FailureType
from fixlot.feedback.correction import generate_correction_hint
from fixlot.feedback.loop import FeedbackLoop, FeedbackResult, LoopState


SAMPLE_MULTI_FAILURE = """
============================= test session starts =============================
collected 4 items

test_math.py::test_add PASSED
test_math.py::test_sub FAILED
test_math.py::test_mul FAILED
test_math.py::test_div FAILED

================================== FAILURES ===================================
_________________________________ test_sub ___________________________________

    def test_sub():
>       assert subtract(5, 3) == 2
E       assert 8 == 2

test_math.py:8: AssertionError
_________________________________ test_mul ___________________________________

    def test_mul():
        import nonexistent_module
>       from missing import function
E       ModuleNotFoundError: No module named 'missing'

test_math.py:12: ModuleNotFoundError
_________________________________ test_div ___________________________________

    def test_div():
>       return 1 / 0
E       ZeroDivisionError: division by zero

test_math.py:16: ZeroDivisionError
=========================== short test summary info ===========================
FAILED test_math.py::test_sub - assert 8 == 2
FAILED test_math.py::test_mul - ModuleNotFoundError: No module named 'missing'
FAILED test_math.py::test_div - ZeroDivisionError: division by zero
========================= 3 failed, 1 passed in 0.10s ========================
"""


def test_full_pipeline_step_by_step():
    failures = parse_pytest_output(SAMPLE_MULTI_FAILURE)
    assert len(failures) == 3, f"Expected 3 failures, got {len(failures)}"

    classified = classify_failures(failures)
    assert len(classified) == 3

    categories = {c.category for c in classified}
    assert FailureType.ASSERTION_ERROR in categories
    assert FailureType.IMPORT_ERROR in categories

    hint = generate_correction_hint(classified)
    assert len(hint) > 0
    assert "test_sub" in hint
    assert "test_mul" in hint
    assert "test_div" in hint
    assert "ASSERTION_ERROR" in hint
    assert "IMPORT_ERROR" in hint


def test_feedback_loop_state_machine():
    loop = FeedbackLoop(max_rounds=3)
    assert loop.state == LoopState.IDLE

    failures = parse_pytest_output(SAMPLE_MULTI_FAILURE)
    classified = classify_failures(failures)
    hint = generate_correction_hint(classified)

    feedback = FeedbackResult(passed=False, failures=classified, correction_hint=hint)
    loop.record_round(action=None, execution_result="round 1", feedback=feedback)
    assert loop.state == LoopState.RUNNING
    assert loop.should_continue() is True

    loop.record_round(action=None, execution_result="round 2", feedback=feedback)
    assert loop.should_continue() is True

    loop.record_round(action=None, execution_result="round 3", feedback=feedback)
    assert loop.state == LoopState.MAX_RETRIES
    assert loop.should_continue() is False


def test_feedback_pipeline_is_deterministic():
    for _ in range(5):
        failures = parse_pytest_output(SAMPLE_MULTI_FAILURE)
        assert len(failures) == 3

        classified = classify_failures(failures)
        assert len(classified) == 3
        assert classified[0].category == FailureType.ASSERTION_ERROR
        assert classified[1].category == FailureType.IMPORT_ERROR

        hint = generate_correction_hint(classified)
        assert "test_sub" in hint
        assert "test_mul" in hint


def test_feedback_pipeline_no_llm_needed():
    """The entire feedback pipeline runs without any LLM dependency."""
    failures = parse_pytest_output(SAMPLE_MULTI_FAILURE)
    classified = classify_failures(failures)
    hint = generate_correction_hint(classified)

    assert isinstance(hint, str)
    assert len(hint) > 100
    assert "failures" in hint.lower() or "failure" in hint.lower()