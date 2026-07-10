import os
import tempfile
import pytest
from fixlot.guardrails.file_guard import FileGuard, check_path


class TestFileGuard:
    def test_allows_path_inside_work_dir(self):
        guard = FileGuard("/home/user/project")
        result = guard.check("/home/user/project/src/main.py")
        assert result.allowed is True

    def test_allows_relative_path(self):
        guard = FileGuard("/home/user/project")
        result = guard.check("./src/main.py")
        assert result.allowed is True

    def test_blocks_path_outside_work_dir(self):
        guard = FileGuard("/home/user/project")
        result = guard.check("/etc/passwd")
        assert result.allowed is False
        assert "outside" in result.reason.lower()

    def test_blocks_system_sensitive_path(self):
        guard = FileGuard("/home/user/project")
        result = guard.check("/etc/shadow")
        assert result.allowed is False

    def test_blocks_windows_system_path(self):
        guard = FileGuard("C:\\Users\\dev\\project")
        result = guard.check("C:\\Windows\\System32\\config")
        assert result.allowed is False

    def test_allows_path_with_traversal_inside_work_dir(self):
        guard = FileGuard("/home/user/project")
        result = guard.check("/home/user/project/sub/../other/file.py")
        assert result.allowed is True

    def test_blocks_path_traversal_outside_work_dir(self):
        guard = FileGuard("/home/user/project")
        result = guard.check("/home/user/project/../../../etc/passwd")
        assert result.allowed is False

    def test_blocks_ssh_key_access(self):
        guard = FileGuard("/home/user/project")
        result = guard.check("/home/user/.ssh/id_rsa")
        assert result.allowed is False

    def test_check_path_convenience(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = check_path(os.path.join(tmpdir, "file.txt"), tmpdir)
            assert result.allowed is True
            result = check_path("/etc/passwd", tmpdir)
            assert result.allowed is False