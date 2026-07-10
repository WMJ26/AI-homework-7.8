from dataclasses import dataclass, field
from enum import Enum, auto
from fixlot.feedback.parser import TestFailure
from fixlot.feedback.classifier import ClassifiedFailure


class LoopState(Enum):
    IDLE = auto()
    RUNNING = auto()
    ANALYZING = auto()
    CORRECTING = auto()
    PASSED = auto()
    MAX_RETRIES = auto()
    ERROR = auto()


@dataclass
class FeedbackResult:
    passed: bool
    failures: list[ClassifiedFailure]
    correction_hint: str


@dataclass
class RoundRecord:
    round: int
    action: object | None
    result: str
    feedback: FeedbackResult


class FeedbackLoop:
    def __init__(self, max_rounds: int = 5):
        self.max_rounds = max_rounds
        self.state = LoopState.IDLE
        self.rounds: list[RoundRecord] = []

    def record_round(
        self,
        action: object | None,
        execution_result: str,
        feedback: FeedbackResult,
    ):
        if self.state in (LoopState.PASSED, LoopState.MAX_RETRIES, LoopState.ERROR):
            return

        self.state = LoopState.RUNNING
        self.rounds.append(RoundRecord(
            round=len(self.rounds) + 1,
            action=action,
            result=execution_result,
            feedback=feedback,
        ))

        if feedback.passed:
            self.state = LoopState.PASSED
        elif len(self.rounds) >= self.max_rounds:
            self.state = LoopState.MAX_RETRIES

    def should_continue(self) -> bool:
        return self.state in (LoopState.IDLE, LoopState.RUNNING, LoopState.ANALYZING, LoopState.CORRECTING)

    def set_error(self, error: str):
        self.state = LoopState.ERROR

    def get_last_feedback(self) -> FeedbackResult | None:
        if not self.rounds:
            return None
        return self.rounds[-1].feedback

    def get_summary(self) -> dict:
        return {
            "state": self.state.name,
            "total_rounds": len(self.rounds),
            "passed": self.state == LoopState.PASSED,
            "max_rounds": self.max_rounds,
        }