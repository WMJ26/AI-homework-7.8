import os
import json
import tempfile
import pytest
from fixlot.memory.store import SessionMemory, ProjectMemory


class TestSessionMemory:
    def test_add_and_get_history(self):
        mem = SessionMemory()
        mem.add("user", "Hello")
        mem.add("assistant", "Hi there")
        history = mem.get_history()
        assert len(history) == 2
        assert history[0] == {"role": "user", "content": "Hello"}
        assert history[1] == {"role": "assistant", "content": "Hi there"}

    def test_add_round(self):
        mem = SessionMemory()
        mem.add_round(1, "write_file", "PASSED")
        rounds = mem.get_rounds()
        assert len(rounds) == 1
        assert rounds[0]["round"] == 1
        assert rounds[0]["action"] == "write_file"
        assert rounds[0]["result"] == "PASSED"

    def test_get_last_n_history(self):
        mem = SessionMemory()
        for i in range(5):
            mem.add("user", f"msg {i}")
        recent = mem.get_last_n_history(3)
        assert len(recent) == 3
        assert recent[0]["content"] == "msg 2"
        assert recent[2]["content"] == "msg 4"

    def test_clear(self):
        mem = SessionMemory()
        mem.add("user", "Hello")
        mem.clear()
        assert len(mem.get_history()) == 0
        assert len(mem.get_rounds()) == 0


class TestProjectMemory:
    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = ProjectMemory(tmpdir)
            pm.save("key1", "value1")
            pm.save("key2", {"nested": "data"})
            assert pm.load("key1") == "value1"
            assert pm.load("key2") == {"nested": "data"}

    def test_load_nonexistent_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = ProjectMemory(tmpdir)
            assert pm.load("nonexistent") is None

    def test_persistence_across_instances(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pm1 = ProjectMemory(tmpdir)
            pm1.save("convention", "Use pytest")
            pm1.save("known_error", "ImportError: missing module")

            pm2 = ProjectMemory(tmpdir)
            assert pm2.load("convention") == "Use pytest"
            assert pm2.load("known_error") == "ImportError: missing module"

    def test_memory_file_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = ProjectMemory(tmpdir)
            pm.save("test", "data")
            memory_path = os.path.join(tmpdir, ".fixlot", "memory.json")
            assert os.path.isfile(memory_path)

            with open(memory_path, "r") as f:
                data = json.load(f)
            assert data["test"] == "data"