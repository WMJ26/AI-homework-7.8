import os
import tempfile
import pytest
from fixlot.tools.file import read_file, write_file, create_file_tools
from fixlot.tools.registry import ToolRegistry


class TestReadFile:
    def test_reads_file_content(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("hello world")
            path = f.name

        try:
            result = read_file({"path": path})
            assert result.success is True
            assert result.output == "hello world"
        finally:
            os.unlink(path)

    def test_returns_error_for_nonexistent_file(self):
        result = read_file({"path": "/nonexistent/path/file.txt"})
        assert result.success is False
        assert "not found" in result.error.lower() or "no such" in result.error.lower()


class TestWriteFile:
    def test_writes_file_content(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.txt")
            result = write_file({"path": path, "content": "new content"})
            assert result.success is True

            with open(path, "r") as f:
                assert f.read() == "new content"

    def test_overwrites_existing_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.txt")
            with open(path, "w") as f:
                f.write("old")

            result = write_file({"path": path, "content": "new"})
            assert result.success is True

            with open(path, "r") as f:
                assert f.read() == "new"


class TestFileToolsRegistration:
    def test_registers_both_tools(self):
        registry = ToolRegistry()
        create_file_tools(registry)
        tools = registry.list_tools()
        assert "read_file" in tools
        assert "write_file" in tools