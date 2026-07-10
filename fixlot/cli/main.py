import argparse
import sys
import os
import logging
from fixlot import __version__
from fixlot.config.loader import load_config, DEFAULT_CONFIG
from fixlot.config.credentials import load_credentials
from fixlot.core.llm import OpenAIProvider, AnthropicProvider
from fixlot.core.loop import AgentLoop, LoopConfig
from fixlot.tools.registry import ToolRegistry
from fixlot.tools.file import create_file_tools
from fixlot.tools.shell import create_shell_tools
from fixlot.tools.test_runner import create_test_runner_tools
from fixlot.guardrails.shell_guard import ShellGuard
from fixlot.guardrails.file_guard import FileGuard

logger = logging.getLogger("fixlot")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fixlot",
        description="A test-driven self-correcting Coding Agent Harness",
    )
    parser.add_argument("task", nargs="?", help="The coding task to perform")
    parser.add_argument("--version", action="version", version=f"fixlot {__version__}")
    parser.add_argument("--dir", default=".", help="Working directory (default: current)")
    parser.add_argument("--provider", default="openai", help="LLM provider (openai, anthropic)")
    parser.add_argument("--max-rounds", type=int, default=None, help="Maximum correction rounds")
    parser.add_argument("--model", default=None, help="LLM model name")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    return parser


def main(argv: list[str] | None = None):
    if argv is None:
        argv = sys.argv[1:]

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.verbose:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if not args.task:
        print("Usage: fixlot \"your task description\"")
        print("Run 'fixlot --help' for more information.")
        sys.exit(1)

    work_dir = os.path.abspath(args.dir)
    config = load_config(work_dir)
    credentials = load_credentials(work_dir)

    max_rounds = args.max_rounds if args.max_rounds is not None else config["max_rounds"]
    provider_name = args.provider or config["provider"]
    model = args.model or config.get("model")

    if provider_name == "openai":
        api_key = credentials.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("Error: OPENAI_API_KEY not found. Set it in .env or as an environment variable.")
            sys.exit(1)
        llm = OpenAIProvider(api_key=api_key, model=model or "gpt-4o")
    elif provider_name == "anthropic":
        api_key = credentials.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("Error: ANTHROPIC_API_KEY not found. Set it in .env or as an environment variable.")
            sys.exit(1)
        llm = AnthropicProvider(api_key=api_key, model=model or "claude-sonnet-4-20250514")
    else:
        print(f"Error: Unknown provider '{provider_name}'. Use 'openai' or 'anthropic'.")
        sys.exit(1)

    registry = ToolRegistry()
    create_file_tools(registry)
    create_shell_tools(registry)
    create_test_runner_tools(registry)

    loop_config = LoopConfig(
        max_rounds=max_rounds,
        work_dir=work_dir,
        test_command=config.get("test_command", "pytest"),
        timeout=config.get("timeout", 300),
    )

    loop = AgentLoop(
        llm=llm,
        tool_registry=registry,
        config=loop_config,
        shell_guard=ShellGuard(),
        file_guard=FileGuard(work_dir),
    )

    print(f"fixlot: Starting task with {provider_name} (max {max_rounds} rounds)...")
    print(f"Task: {args.task}")
    print("-" * 50)

    result = loop.run(args.task)

    print("-" * 50)
    print(f"State: {result['state']}")
    print(f"Rounds: {result['total_rounds']}/{result['max_rounds']}")
    if result['passed']:
        print("Result: All tests passed!")
    else:
        print("Result: Did not pass all tests.")


if __name__ == "__main__":
    main()