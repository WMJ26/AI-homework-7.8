import json
import logging
from dataclasses import dataclass
from fixlot.core.llm import LLMProvider
from fixlot.core.context import ContextBuilder
from fixlot.tools.registry import ToolRegistry, Action
from fixlot.guardrails.shell_guard import ShellGuard
from fixlot.guardrails.file_guard import FileGuard
from fixlot.feedback.loop import FeedbackLoop, FeedbackResult, LoopState
from fixlot.feedback.parser import parse_pytest_output
from fixlot.feedback.classifier import classify_failures
from fixlot.feedback.correction import generate_correction_hint

logger = logging.getLogger(__name__)


@dataclass
class LoopConfig:
    max_rounds: int = 5
    work_dir: str = "."
    test_command: str = "pytest"
    timeout: int = 300


class AgentLoop:
    def __init__(
        self,
        llm: LLMProvider,
        tool_registry: ToolRegistry,
        config: LoopConfig,
        shell_guard: ShellGuard,
        file_guard: FileGuard,
    ):
        self._llm = llm
        self._tool_registry = tool_registry
        self._config = config
        self._shell_guard = shell_guard
        self._file_guard = file_guard
        self._feedback_loop = FeedbackLoop(max_rounds=config.max_rounds)

    def run(self, task: str) -> dict:
        tools = self._tool_registry.get_tool_descriptions()
        context = ContextBuilder(task=task, tools=tools)

        self._feedback_loop = FeedbackLoop(max_rounds=self._config.max_rounds)

        while self._feedback_loop.should_continue():
            round_num = len(self._feedback_loop.rounds) + 1
            logger.info(f"Round {round_num}/{self._config.max_rounds}")

            messages = context.build()
            try:
                response = self._llm.invoke(messages)
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                self._feedback_loop.set_error(f"LLM call failed: {e}")
                break

            action = self._parse_action(response)
            if not action:
                context.add_feedback("Failed to parse your response. Please output valid JSON with 'tool' and 'params' keys.")
                continue

            context.add_history("assistant", response)

            if action.tool == "done":
                logger.info("Agent signaled completion")
                break

            guard_result = self._check_guardrails(action)
            if guard_result and not guard_result.get("allowed", True):
                logger.warning(f"Guardrail blocked: {guard_result.get('reason')}")
                context.add_feedback(
                    f"Your action '{action.tool}' was blocked by the guardrail: {guard_result.get('reason')}. "
                    "Please choose a different approach."
                )
                continue

            result = self._tool_registry.dispatch(action)
            context.add_history("user", f"Tool result: {result.output}")

            if result.error:
                logger.warning(f"Tool error: {result.error}")

            if action.tool == "run_tests":
                feedback = self._analyze_test_results(result.output)
                self._feedback_loop.record_round(
                    action=action,
                    execution_result=result.output,
                    feedback=feedback,
                )

                if not feedback.passed:
                    context.add_feedback(feedback.correction_hint)
                    logger.info(f"Feedback: {len(feedback.failures)} failures, state={self._feedback_loop.state}")
                else:
                    logger.info("All tests passed!")

        return self._feedback_loop.get_summary()

    def _parse_action(self, response: str) -> Action | None:
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start == -1 or json_end == 0:
                return None
            data = json.loads(response[json_start:json_end])
            if "tool" not in data:
                return None
            return Action(
                tool=data["tool"],
                params=data.get("params", {}),
                raw=response,
            )
        except (json.JSONDecodeError, KeyError):
            return None

    def _check_guardrails(self, action: Action) -> dict | None:
        if action.tool == "run_command":
            cmd = action.params.get("cmd", action.params.get("command", ""))
            result = self._shell_guard.check(cmd)
            if not result.allowed:
                return {"allowed": False, "reason": result.reason}

        if action.tool in ("read_file", "write_file"):
            path = action.params.get("path", "")
            result = self._file_guard.check(path)
            if not result.allowed:
                return {"allowed": False, "reason": result.reason}

        return None

    def _analyze_test_results(self, output: str) -> FeedbackResult:
        failures = parse_pytest_output(output)
        if not failures:
            return FeedbackResult(passed=True, failures=[], correction_hint="")

        classified = classify_failures(failures)
        hint = generate_correction_hint(classified)
        return FeedbackResult(passed=False, failures=classified, correction_hint=hint)