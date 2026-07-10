import pytest
from fixlot.feedback.parser import TestFailure, parse_pytest_output
from fixlot.feedback.classifier import FailureType, ClassifiedFailure, classify_failures
from fixlot.feedback.correction import generate_correction_hint
from fixlot.feedback.loop import FeedbackLoop, LoopState, FeedbackResult, RoundRecord


class TestFeedbackLoop:
    def test_initial_state_is_idle(self):
        loop = FeedbackLoop(max_rounds=5)
        assert loop.state == LoopState.IDLE

    def test_record_round(self):
        loop = FeedbackLoop(max_rounds=5)
        loop.record_round(
            action=None,
            execution_result="test output",
            feedback=FeedbackResult(
                passed=False,
                failures=[
                    ClassifiedFailure("test_x", FailureType.ASSERTION_ERROR, "msg", "tb"),
                ],
                correction_hint="fix it",
            ),
        )
        assert len(loop.rounds) == 1
        assert loop.state == LoopState.RUNNING

    def test_marks_passed_when_no_failures(self):
        loop = FeedbackLoop(max_rounds=5)
        loop.record_round(
            action=None,
            execution_result="all good",
            feedback=FeedbackResult(passed=True, failures=[], correction_hint=""),
        )
        assert loop.state == LoopState.PASSED

    def test_max_retries_reached(self):
        loop = FeedbackLoop(max_rounds=2)
        feedback = FeedbackResult(
            passed=False,
            failures=[
                ClassifiedFailure("test_x", FailureType.ASSERTION_ERROR, "msg", "tb"),
            ],
            correction_hint="fix it",
        )
        loop.record_round(action=None, execution_result="out1", feedback=feedback)
        loop.record_round(action=None, execution_result="out2", feedback=feedback)
        assert loop.state == LoopState.MAX_RETRIES

    def test_rounds_capped_at_max(self):
        loop = FeedbackLoop(max_rounds=3)
        feedback = FeedbackResult(
            passed=False,
            failures=[
                ClassifiedFailure("test_x", FailureType.ASSERTION_ERROR, "msg", "tb"),
            ],
            correction_hint="fix it",
        )
        loop.record_round(action=None, execution_result="out1", feedback=feedback)
        loop.record_round(action=None, execution_result="out2", feedback=feedback)
        loop.record_round(action=None, execution_result="out3", feedback=feedback)
        assert loop.state == LoopState.MAX_RETRIES
        assert len(loop.rounds) == 3

    def test_passed_on_last_round(self):
        loop = FeedbackLoop(max_rounds=3)
        fail_feedback = FeedbackResult(
            passed=False,
            failures=[
                ClassifiedFailure("test_x", FailureType.ASSERTION_ERROR, "msg", "tb"),
            ],
            correction_hint="fix it",
        )
        pass_feedback = FeedbackResult(passed=True, failures=[], correction_hint="")

        loop.record_round(action=None, execution_result="out1", feedback=fail_feedback)
        loop.record_round(action=None, execution_result="out2", feedback=fail_feedback)
        loop.record_round(action=None, execution_result="out3", feedback=pass_feedback)
        assert loop.state == LoopState.PASSED
        assert len(loop.rounds) == 3

    def test_should_continue_when_running(self):
        loop = FeedbackLoop(max_rounds=5)
        assert loop.should_continue() is True

    def test_should_not_continue_when_passed(self):
        loop = FeedbackLoop(max_rounds=5)
        loop.record_round(
            action=None,
            execution_result="ok",
            feedback=FeedbackResult(passed=True, failures=[], correction_hint=""),
        )
        assert loop.should_continue() is False

    def test_should_not_continue_when_max_retries(self):
        loop = FeedbackLoop(max_rounds=1)
        feedback = FeedbackResult(
            passed=False,
            failures=[
                ClassifiedFailure("test_x", FailureType.ASSERTION_ERROR, "msg", "tb"),
            ],
            correction_hint="fix it",
        )
        loop.record_round(action=None, execution_result="out", feedback=feedback)
        assert loop.should_continue() is False

    def test_error_state(self):
        loop = FeedbackLoop(max_rounds=5)
        loop.set_error("Something went wrong")
        assert loop.state == LoopState.ERROR
        assert loop.should_continue() is False

    def test_mock_llm_three_rounds(self):
        loop = FeedbackLoop(max_rounds=5)

        fail_feedback = FeedbackResult(
            passed=False,
            failures=[
                ClassifiedFailure("test_x", FailureType.ASSERTION_ERROR, "assert 3 == 2", "tb"),
            ],
            correction_hint="The assertion failed: expected 3, got 2",
        )

        loop.record_round(action=None, execution_result="pytest output round 1", feedback=fail_feedback)
        assert loop.should_continue() is True

        loop.record_round(action=None, execution_result="pytest output round 2", feedback=fail_feedback)
        assert loop.should_continue() is True

        pass_feedback = FeedbackResult(passed=True, failures=[], correction_hint="")
        loop.record_round(action=None, execution_result="pytest output round 3", feedback=pass_feedback)
        assert loop.state == LoopState.PASSED
        assert loop.should_continue() is False
        assert len(loop.rounds) == 3