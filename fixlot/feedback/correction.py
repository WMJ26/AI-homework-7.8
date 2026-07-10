from fixlot.feedback.classifier import FailureType, ClassifiedFailure


CORRECTION_TEMPLATES = {
    FailureType.SYNTAX_ERROR: (
        "SYNTAX_ERROR: The test '{test_name}' has a syntax error in the source code. "
        "Check the file for invalid syntax."
    ),
    FailureType.IMPORT_ERROR: (
        "IMPORT_ERROR: The test '{test_name}' failed because a module could not be imported. "
        "Ensure the module is installed or the import path is correct."
    ),
    FailureType.NAME_ERROR: (
        "NAME_ERROR: The test '{test_name}' references an undefined name. "
        "Check for typos in variable or function names."
    ),
    FailureType.TYPE_ERROR: (
        "TYPE_ERROR: The test '{test_name}' encountered a type mismatch. "
        "Check that the types of values being operated on are compatible."
    ),
    FailureType.ASSERTION_ERROR: (
        "ASSERTION_ERROR: The test '{test_name}' had an assertion failure. "
        "The expected value did not match the actual value. Review the implementation logic."
    ),
    FailureType.ATTRIBUTE_ERROR: (
        "ATTRIBUTE_ERROR: The test '{test_name}' tried to access a non-existent attribute. "
        "Check the object type and available attributes."
    ),
    FailureType.TIMEOUT: (
        "TIMEOUT: The test '{test_name}' timed out. "
        "The implementation may have an infinite loop or be too slow."
    ),
    FailureType.UNKNOWN: (
        "UNKNOWN_ERROR: The test '{test_name}' failed with an unrecognized error. "
        "Review the error message and traceback for details."
    ),
}


def generate_correction_hint(failures: list[ClassifiedFailure]) -> str:
    if not failures:
        return "All tests passed. No corrections needed."

    lines = []
    lines.append(f"Tests failed: {len(failures)} failure(s) detected.\n")

    for failure in failures:
        template = CORRECTION_TEMPLATES.get(
            failure.category,
            CORRECTION_TEMPLATES[FailureType.UNKNOWN],
        )
        hint = template.format(
            test_name=failure.test_name,
            message=failure.message,
        )
        lines.append(f"- {hint}")

    lines.append("\nPlease fix the issues above and re-run the tests.")
    return "\n".join(lines)