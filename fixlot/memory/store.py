import os
import json


class SessionMemory:
    def __init__(self):
        self._history: list[dict] = []
        self._rounds: list[dict] = []

    def add(self, role: str, content: str):
        self._history.append({"role": role, "content": content})

    def get_history(self) -> list[dict]:
        return list(self._history)

    def get_last_n_history(self, n: int) -> list[dict]:
        return self._history[-n:] if n > 0 else []

    def add_round(self, round_num: int, action: str, result: str):
        self._rounds.append({
            "round": round_num,
            "action": action,
            "result": result,
        })

    def get_rounds(self) -> list[dict]:
        return list(self._rounds)

    def clear(self):
        self._history = []
        self._rounds = []


class ProjectMemory:
    def __init__(self, work_dir: str):
        self._dir = os.path.join(work_dir, ".fixlot")
        self._path = os.path.join(self._dir, "memory.json")
        self._data: dict = {}
        self._load()

    def _load(self):
        if os.path.isfile(self._path):
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._data = {}

    def _save(self):
        os.makedirs(self._dir, exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)

    def save(self, key: str, value):
        self._data[key] = value
        self._save()

    def load(self, key: str):
        return self._data.get(key)