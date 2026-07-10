import re
from dataclasses import dataclass
from enum import Enum, auto
from fixlot.feedback.parser import TestFailure


class FailureType(Enum):
    SYNTAX_ERROR = auto()
    IMPORT_ERROR = auto()
    NAME_ERROR = auto()
    TYPE_ERROR = auto()
    ASSERTION_ERROR = auto()
    ATTRIBUTE_ERROR = auto()
    TIMEOUT = auto()
    UNKNOWN = auto()


@dataclass
class ClassifiedFailure:
    test_name: str
    category: FailureType
    message: str
    traceback: str


CLASSIFICATION_RULES = [
    (r"SyntaxError", FailureType.SYNTAX_ERROR),
    (r"IndentationError", FailureType.SYNTAX_ERROR),
    (r"ModuleNotFoundError", FailureType.IMPORT_ERROR),
    (r"ImportError", FailureType.IMPORT_ERROR),
    (r"NameError", FailureType.NAME_ERROR),
    (r"TypeError", FailureType.TYPE_ERROR),
    (r"AssertionError", FailureType.ASSERTION_ERROR),
    (r"AttributeError", FailureType.ATTRIBUTE_ERROR),
    (r"Timeout", FailureType.TIMEOUT),
    (r"timed out", FailureType.TIMEOUT),
]


def classify_failure(failure: TestFailure) -> ClassifiedFailure:
    combined = failure.message + " " + failure.traceback
    for pattern, category in CLASSIFICATION_RULES:
        if re.search(pattern, combined, re.IGNORECASE):
            return ClassifiedFailure(
                test_name=failure.test_name,
                category=category,
                message=failure.message,
                traceback=failure.traceback,
            )
    return ClassifiedFailure(
        test_name=failure.test_name,
        category=FailureType.UNKNOWN,
        message=failure.message,
        traceback=failure.traceback,
    )


def classify_failures(failures: list[TestFailure]) -> list[ClassifiedFailure]:
    return [classify_failure(f) for f in failures]