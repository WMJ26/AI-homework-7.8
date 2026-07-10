import os
from dataclasses import dataclass


@dataclass
class GuardResult:
    allowed: bool
    reason: str


SENSITIVE_PATHS = [
    "/etc/",
    "/boot/",
    "/sys/",
    "/proc/",
    "/dev/",
    "/root/",
    "/var/log/",
    "C:\\Windows\\",
    "C:\\Program Files\\",
    "C:\\Program Files (x86)\\",
    "C:\\ProgramData\\",
]


class FileGuard:
    def __init__(self, work_dir: str):
        self._work_dir = os.path.abspath(work_dir)

    def check(self, path: str) -> GuardResult:
        resolved = os.path.abspath(os.path.join(self._work_dir, path))
        normalized = os.path.normpath(resolved)

        common = os.path.commonpath([normalized, self._work_dir])
        if common != self._work_dir:
            return GuardResult(
                allowed=False,
                reason=f"Path '{path}' is outside the working directory",
            )

        for sensitive in SENSITIVE_PATHS:
            if normalized.lower().startswith(sensitive.lower()):
                return GuardResult(
                    allowed=False,
                    reason=f"Path '{path}' accesses a sensitive system directory",
                )

        if ".ssh" in normalized.split(os.sep):
            return GuardResult(
                allowed=False,
                reason=f"Path '{path}' accesses SSH keys",
            )

        return GuardResult(allowed=True, reason="Path is safe")


def check_path(path: str, work_dir: str) -> GuardResult:
    guard = FileGuard(work_dir)
    return guard.check(path)