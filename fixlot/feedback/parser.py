import re
from dataclasses import dataclass, field


@dataclass
class TestFailure:
    test_name: str
    message: str
    traceback: str


def parse_pytest_output(output: str) -> list[TestFailure]:
    failures = []

    failures.extend(_parse_failure_section(output))
    failures.extend(_parse_error_section(output))
    failures.extend(_parse_short_summary(output, already_parsed={f.test_name for f in failures}))

    return failures


def _parse_failure_section(output: str) -> list[TestFailure]:
    failures = []
    failure_section = re.search(r"=+\s+FAILURES\s+=+\n(.*?)(?=\n=+|\Z)", output, re.DOTALL)
    if not failure_section:
        return failures

    blocks = re.split(r"\n_{3,}\s", failure_section.group(1))
    for block in blocks:
        lines = block.strip().split("\n")
        if not lines or not lines[0].strip():
            continue

        header = lines[0].strip()
        test_name = _extract_test_name_from_header(header)

        body = "\n".join(lines[1:])
        error_match = re.search(
            r"E\s+(.+?)(?:\n(?!E\s).*?)*",
            body,
            re.DOTALL,
        )
        message = ""
        if error_match:
            message_lines = re.findall(r"E\s+(.*)", body)
            message = "\n".join(message_lines)

        if not message:
            message = body.strip()

        failures.append(TestFailure(
            test_name=test_name,
            message=message.strip(),
            traceback=body.strip(),
        ))

    return failures


def _extract_test_name_from_header(header: str) -> str:
    name = header.strip("_").strip()
    return name


def _parse_error_section(output: str) -> list[TestFailure]:
    failures = []
    error_section = re.search(r"=+\s+ERRORS\s+=+\n(.*?)(?=\n=+|\Z)", output, re.DOTALL)
    if not error_section:
        return failures

    blocks = re.split(r"\n_{3,}\s", error_section.group(1))
    for block in blocks:
        lines = block.strip().split("\n")
        if not lines or not lines[0].strip():
            continue

        header = lines[0].strip()
        test_name = _extract_test_name_from_header(header)

        body = "\n".join(lines[1:])
        message = body.strip()

        failures.append(TestFailure(
            test_name=test_name,
            message=message,
            traceback=body.strip(),
        ))

    return failures


def _parse_short_summary(output: str, already_parsed: set[str]) -> list[TestFailure]:
    failures = []
    summary_match = re.search(
        r"short test summary info\s*=+\n(.*?)(?:\n=+|\Z)",
        output,
        re.DOTALL,
    )
    if not summary_match:
        return failures

    for line in summary_match.group(1).strip().split("\n"):
        match = re.match(r"FAILED\s+(\S+)\s*-\s*(.*)", line)
        if match:
            test_name = match.group(1)
            test_name_short = test_name.split("::")[-1] if "::" in test_name else test_name
            if test_name not in already_parsed and test_name_short not in already_parsed:
                failures.append(TestFailure(
                    test_name=test_name,
                    message=match.group(2).strip(),
                    traceback="",
                ))

    return failures