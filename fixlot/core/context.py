import json


def build_system_prompt(tools: list[dict]) -> str:
    tool_descriptions = "\n".join(
        f"- {t['name']}: {t['description']}"
        for t in tools
    )

    return f"""You are a coding agent harness. Your job is to complete the user's task by using the available tools.

Available tools:
{tool_descriptions}

Output format:
Always respond with a JSON object containing:
- "tool": the name of the tool to use
- "params": the parameters for the tool

Example: {{"tool": "read_file", "params": {{"path": "src/main.py"}}}}

When tests pass, respond with: {{"tool": "done", "params": {{}}}}
"""


class ContextBuilder:
    def __init__(self, task: str, tools: list[dict] | None = None):
        self._task = task
        self._tools = tools or []
        self._history: list[dict] = []
        self._feedback: str = ""
        self._system_prompt = build_system_prompt(self._tools)

    def add_history(self, role: str, content: str):
        self._history.append({"role": role, "content": content})

    def add_feedback(self, feedback: str):
        self._feedback = feedback

    def reset(self, new_task: str = ""):
        self._history = []
        self._feedback = ""
        if new_task:
            self._task = new_task

    def build(self) -> list[dict]:
        messages = [
            {"role": "system", "content": self._system_prompt},
        ]

        for h in self._history:
            messages.append(h)

        user_content = self._task
        if self._feedback:
            user_content = f"PREVIOUS ATTEMPT FEEDBACK:\n{self._feedback}\n\nORIGINAL TASK:\n{self._task}"

        messages.append({"role": "user", "content": user_content})
        return messages