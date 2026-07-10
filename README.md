# fixlot

A test-driven self-correcting Coding Agent Harness.

**Agent = LLM + Harness.** fixlot is the harness — the engineering layer that
turns an LLM into a reliable coding agent with deterministic feedback loops,
governance guardrails, and tool orchestration.

## Quick Start

### Install

```bash
pip install -e ".[dev]"
```

### Run

```bash
fixlot "Implement a function that adds two numbers" --dir /path/to/your/project
```

Or:

```bash
python -m fixlot "your task description"
```

### Key Configuration

Before running, create a `.env` file in your working directory:

```
OPENAI_API_KEY=sk-your-key-here
```

Or for Anthropic:

```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

**Security Warning:** `.env` is plaintext. Ensure file permissions are restricted
(`chmod 600 .env` on Linux/macOS). Never commit `.env` to Git.

## Project-Level Configuration

Create `.fixlot/config.yaml` in your working directory:

```yaml
max_rounds: 5
timeout: 300
test_command: "pytest"
provider: "openai"
```

## How It Works

```
User Task → Context Assembly → LLM → Action Parsing → Guardrail Check
                                                          ↓
                    Feedback Loop ← Test Results ← Tool Execution
                         ↓
                    (Pass/Fail/Retry)
```

### Core Mechanisms

1. **Agent Main Loop** (`core/loop.py`): Context → LLM → Parse → Guard → Execute → Feedback → Repeat
2. **LLM Abstraction** (`core/llm.py`): OpenAI, Anthropic, and MockLLM for testing
3. **Tool Registry** (`tools/`): read_file, write_file, run_command, run_tests
4. **Guardrails** (`guardrails/`): Shell command filtering and file path sandboxing
5. **Feedback Loop** (`feedback/`): Deterministic failure parsing, classification, correction hints
6. **Memory** (`memory/`): Session memory and project-level persistent memory

## Docker

### CLI Mode

```bash
docker build -t fixlot .
docker run --rm -v $(pwd):/workspace -v $(pwd)/.env:/workspace/.env fixlot "your task"
```

### Web UI Mode

```bash
docker build -t fixlot .
docker run --rm -p 5000:5000 -e FIXLOT_MODE=web -v $(pwd)/.env:/workspace/.env fixlot
```

Then open http://localhost:5000 in your browser.

## Online Deployment

fixlot Web UI is deployed at: **[your-deployment-url]**

### Deploy to Render (one-click)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/YOUR_USERNAME/fixlot)

Or use the included `render.yaml`:

1. Fork this repo to your GitHub account
2. Go to [Render Dashboard](https://dashboard.render.com) → New → Web Service
3. Connect your forked repo — Render auto-detects `render.yaml`
4. Add environment variables: `OPENAI_API_KEY` and/or `ANTHROPIC_API_KEY`
5. Click "Create Web Service"

### Deploy to Railway

```bash
railway up
```

Set `OPENAI_API_KEY` in Railway dashboard → Variables.

## Requirements

- Python 3.10+
- pytest (for test-driven feedback)
- OpenAI or Anthropic API key

## Running Tests

```bash
pytest
```

All core mechanism tests run with mock LLM — no API key or network required.

## 目录结构

```
fixlot/
├── core/          # Main loop, LLM abstraction, context assembly
├── tools/         # File, shell, test runner tools
├── guardrails/    # Shell guard, file sandbox
├── feedback/      # Parser, classifier, correction, loop state machine
├── memory/        # Session and project memory
├── config/        # YAML config loader, credential management
├── cli/           # CLI entry point
tests/
├── demo/          # Mechanism demonstration tests
├── test_*.py      # Unit tests for each module
```

## 安全边界说明

- **API keys never hardcoded** — use `.env` file (not committed to Git)
- **Shell guard** blocks dangerous commands (rm -rf, sudo, curl pipe sh, etc.)
- **File sandbox** restricts file access to the working directory
- **No credentials in logs** — API keys are not written to log output

## Mechanism Demos

Run the mechanism demonstration tests (no LLM required):

```bash
pytest tests/demo/ -v
```

Demonstrates:
1. Guardrail intercepting dangerous commands
2. Feedback loop detecting and classifying test failures
3. Complete feedback pipeline (parser → classifier → correction → loop)

## License

MIT