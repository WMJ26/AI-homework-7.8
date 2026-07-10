import re
from dataclasses import dataclass


@dataclass
class GuardResult:
    allowed: bool
    reason: str


DANGEROUS_PATTERNS = [
    (r"\brm\s+-rf\b", "rm -rf is dangerous"),
    (r"\bsudo\b", "sudo command is dangerous"),
    (r"\bchmod\s+777\b", "chmod 777 is dangerous"),
    (r"\bmkfs\b", "mkfs command is dangerous"),
    (r"\bdd\s+if=", "dd command is dangerous"),
    (r":\(\)\s*\{", "fork bomb detected"),
    (r"\bcurl\b.*\|\s*(?:sh|bash)\b", "curl pipe to shell is dangerous"),
    (r"\bwget\b.*\|\s*(?:sh|bash)\b", "wget pipe to shell is dangerous"),
    (r"\beval\b", "eval command is dangerous"),
    (r">\s*/dev/sd[a-z]", "writing to block device is dangerous"),
    (r">\s*/dev/hd[a-z]", "writing to block device is dangerous"),
    (r">\s*/dev/xvd[a-z]", "writing to block device is dangerous"),
]


class ShellGuard:
    def __init__(self, extra_patterns: list[tuple[str, str]] | None = None):
        self._patterns = list(DANGEROUS_PATTERNS)
        if extra_patterns:
            self._patterns.extend(extra_patterns)

    def check(self, command: str) -> GuardResult:
        for pattern, reason in self._patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return GuardResult(allowed=False, reason=reason)
        return GuardResult(allowed=True, reason="Command is safe")


_default_guard = ShellGuard()


def check_command(command: str) -> GuardResult:
    return _default_guard.check(command)