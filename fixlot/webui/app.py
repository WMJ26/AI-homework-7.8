import os
import threading
from flask import Flask, render_template, request, jsonify
from fixlot.config.loader import load_config
from fixlot.config.credentials import load_credentials
from fixlot.core.llm import OpenAIProvider, AnthropicProvider, MockLLM
from fixlot.core.loop import AgentLoop, LoopConfig
from fixlot.tools.registry import ToolRegistry
from fixlot.tools.file import create_file_tools
from fixlot.tools.shell import create_shell_tools
from fixlot.tools.test_runner import create_test_runner_tools
from fixlot.guardrails.shell_guard import ShellGuard
from fixlot.guardrails.file_guard import FileGuard

app = Flask(__name__)

_tasks: dict[str, dict] = {}
_lock = threading.Lock()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/run", methods=["POST"])
def run_task():
    data = request.get_json()
    task = data.get("task", "")
    work_dir = data.get("dir", ".")
    provider_name = data.get("provider", "openai")
    max_rounds = int(data.get("max_rounds", 5))
    model = data.get("model")

    if not task:
        return jsonify({"error": "Task description is required"}), 400

    task_id = str(len(_tasks) + 1)
    with _lock:
        _tasks[task_id] = {"status": "running", "result": None}

    def _run():
        try:
            work_dir_abs = os.path.abspath(work_dir)
            config = load_config(work_dir_abs)
            credentials = load_credentials(work_dir_abs)

            if provider_name == "openai":
                api_key = credentials.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
                if not api_key:
                    with _lock:
                        _tasks[task_id] = {"status": "error", "error": "OPENAI_API_KEY not found"}
                    return
                llm = OpenAIProvider(api_key=api_key, model=model or "gpt-4o")
            elif provider_name == "anthropic":
                api_key = credentials.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
                if not api_key:
                    with _lock:
                        _tasks[task_id] = {"status": "error", "error": "ANTHROPIC_API_KEY not found"}
                    return
                llm = AnthropicProvider(api_key=api_key, model=model or "claude-sonnet-4-20250514")
            else:
                with _lock:
                    _tasks[task_id] = {"status": "error", "error": f"Unknown provider: {provider_name}"}
                return

            registry = ToolRegistry()
            create_file_tools(registry)
            create_shell_tools(registry)
            create_test_runner_tools(registry)

            loop_config = LoopConfig(
                max_rounds=max_rounds,
                work_dir=work_dir_abs,
                test_command=config.get("test_command", "pytest"),
                timeout=config.get("timeout", 300),
            )

            loop = AgentLoop(
                llm=llm,
                tool_registry=registry,
                config=loop_config,
                shell_guard=ShellGuard(),
                file_guard=FileGuard(work_dir_abs),
            )

            result = loop.run(task)
            with _lock:
                _tasks[task_id] = {"status": "completed", "result": result}
        except Exception as e:
            with _lock:
                _tasks[task_id] = {"status": "error", "error": str(e)}

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    return jsonify({"task_id": task_id, "status": "running"})


@app.route("/api/status/<task_id>")
def task_status(task_id):
    with _lock:
        task = _tasks.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task)


def main():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    main()