import pytest
from fixlot.feedback.parser import TestFailure
from fixlot.feedback.classifier import FailureType, classify_failures


class TestClassifyFailures:
    def test_classifies_assertion_error(self):
        failures = [
            TestFailure(
                test_name="test_foo",
                message="assert 5 == 3",
                traceback="test_foo.py:5: AssertionError",
            )
        ]
        result = classify_failures(failures)
        assert len(result) == 1
        assert result[0].category == FailureType.ASSERTION_ERROR

    def test_classifies_import_error(self):
        failures = [
            TestFailure(
                test_name="test_import",
                message="ModuleNotFoundError: No module named 'foo'",
                traceback="test_import.py:1: ModuleNotFoundError",
            )
        ]
        result = classify_failures(failures)
        assert result[0].category == FailureType.IMPORT_ERROR

    def test_classifies_name_error(self):
        failures = [
            TestFailure(
                test_name="test_name",
                message="NameError: name 'foo' is not defined",
                traceback="test_name.py:3: NameError",
            )
        ]
        result = classify_failures(failures)
        assert result[0].category == FailureType.NAME_ERROR

    def test_classifies_type_error(self):
        failures = [
            TestFailure(
                test_name="test_type",
                message="TypeError: unsupported operand type(s) for +: 'int' and 'str'",
                traceback="test_type.py:4: TypeError",
            )
        ]
        result = classify_failures(failures)
        assert result[0].category == FailureType.TYPE_ERROR

    def test_classifies_attribute_error(self):
        failures = [
            TestFailure(
                test_name="test_attr",
                message="AttributeError: 'NoneType' object has no attribute 'foo'",
                traceback="test_attr.py:2: AttributeError",
            )
        ]
        result = classify_failures(failures)
        assert result[0].category == FailureType.ATTRIBUTE_ERROR

    def test_classifies_syntax_error(self):
        failures = [
            TestFailure(
                test_name="test_broken",
                message="SyntaxError: invalid syntax",
                traceback="test_broken.py:3: SyntaxError",
            )
        ]
        result = classify_failures(failures)
        assert result[0].category == FailureType.SYNTAX_ERROR

    def test_classifies_unknown(self):
        failures = [
            TestFailure(
                test_name="test_mystery",
                message="Something went wrong",
                traceback="???",
            )
        ]
        result = classify_failures(failures)
        assert result[0].category == FailureType.UNKNOWN

    def test_classifies_multiple_failures(self):
        failures = [
            TestFailure("test_a", "AssertionError: x", "tb"),
            TestFailure("test_b", "TypeError: x", "tb"),
            TestFailure("test_c", "NameError: x", "tb"),
        ]
        result = classify_failures(failures)
        assert len(result) == 3
        assert result[0].category == FailureType.ASSERTION_ERROR
        assert result[1].category == FailureType.TYPE_ERROR
        assert result[2].category == FailureType.NAME_ERROR