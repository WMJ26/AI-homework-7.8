import pytest
from fixlot.feedback.parser import TestFailure, parse_pytest_output


SAMPLE_PASSING_OUTPUT = """
============================= test session starts =============================
collected 3 items

test_math.py::test_add PASSED                                          [ 33%]
test_math.py::test_sub PASSED                                          [ 66%]
test_math.py::test_mul PASSED                                          [100%]

============================== 3 passed in 0.10s ==============================
"""

SAMPLE_FAILING_OUTPUT = """
============================= test session starts =============================
collected 3 items

test_math.py::test_add PASSED                                          [ 33%]
test_math.py::test_sub FAILED                                          [ 66%]
test_math.py::test_mul FAILED                                          [100%]

================================== FAILURES ===================================
_________________________________ test_sub ___________________________________

    def test_sub():
>       assert subtract(5, 3) == 2
E       assert 8 == 2
E        +  where 8 = subtract(5, 3)

test_math.py:8: AssertionError
_________________________________ test_mul ___________________________________

    def test_mul():
        import nonexistent_module
>       from missing import function
E       ModuleNotFoundError: No module named 'missing'

test_math.py:12: ModuleNotFoundError
=========================== short test summary info ===========================
FAILED test_math.py::test_sub - assert 8 == 2
FAILED test_math.py::test_mul - ModuleNotFoundError: No module named 'missing'
========================= 2 failed, 1 passed in 0.10s ========================
"""

SAMPLE_SYNTAX_ERROR = """
============================= test session starts =============================
collected 0 items / 1 error

==================================== ERRORS ====================================
____________________ ERROR collecting test_broken.py __________________________
test_broken.py:3:1: E999 SyntaxError: invalid syntax
=========================== short test summary info ===========================
ERROR test_broken.py
=============================== 1 error in 0.05s ==============================
"""


class TestParsePytestOutput:
    def test_parses_passing_output(self):
        failures = parse_pytest_output(SAMPLE_PASSING_OUTPUT)
        assert len(failures) == 0

    def test_parses_failing_output(self):
        failures = parse_pytest_output(SAMPLE_FAILING_OUTPUT)
        assert len(failures) == 2

    def test_extracts_test_name(self):
        failures = parse_pytest_output(SAMPLE_FAILING_OUTPUT)
        names = [f.test_name for f in failures]
        assert "test_sub" in names
        assert "test_mul" in names

    def test_extracts_assertion_error_message(self):
        failures = parse_pytest_output(SAMPLE_FAILING_OUTPUT)
        sub_failure = [f for f in failures if "test_sub" in f.test_name][0]
        assert "assert 8 == 2" in sub_failure.message

    def test_extracts_module_not_found_error(self):
        failures = parse_pytest_output(SAMPLE_FAILING_OUTPUT)
        mul_failure = [f for f in failures if "test_mul" in f.test_name][0]
        assert "ModuleNotFoundError" in mul_failure.message

    def test_parses_syntax_error(self):
        failures = parse_pytest_output(SAMPLE_SYNTAX_ERROR)
        assert len(failures) >= 1
        assert any("SyntaxError" in f.message for f in failures)

    def test_handles_empty_output(self):
        failures = parse_pytest_output("")
        assert len(failures) == 0

    def test_handles_non_pytest_output(self):
        failures = parse_pytest_output("some random text")
        assert len(failures) == 0