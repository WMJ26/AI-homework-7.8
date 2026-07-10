# PLAN.md — fixlot 实现计划

> 每个 task 颗粒度：2-5 分钟，可由一个 subagent 在一次会话内完成。
> 标记：`[P]` = 可并行，`[T]` = 含 TDD（先写失败测试），`[D]` = 依赖前序 task

---

## Phase 0：项目基础设施

### T0.1 [P] 初始化项目结构 ✅
- **状态**：完成 | commit: `b66505a`
- **目标**：创建目录结构、`pyproject.toml`、`.gitignore`
- **涉及文件**：`pyproject.toml`, `.gitignore`, `fixlot/__init__.py`, 各子包 `__init__.py`
- **实现要点**：
  - `pyproject.toml` 包含 `pytest`, `openai`, `anthropic`, `pyyaml`, `python-dotenv` 依赖
  - `.gitignore` 包含 `.env`, `__pycache__`, `*.pyc`, `dist/`, `build/`, `.fixlot/`
  - 创建目录结构：`core/`, `tools/`, `guardrails/`, `feedback/`, `memory/`, `config/`, `cli/`
- **验证**：`python -c "import fixlot"` 不报错；`ls fixlot/` 显示正确目录结构

### T0.2 [P] 配置 CI（GitHub Actions + GitLab CI） ✅
- **状态**：完成 | commit: `b66505a`
- **涉及文件**：`.github/workflows/ci.yml`
- **实现要点**：Python 3.10+，`pip install -e ".[dev]"`，`pytest` 运行测试
- **验证**：push 后 CI 运行（最初会因无测试而失败，后续变绿）

---

## Phase 1：LLM 抽象层 + 配置

### T1.1 [T] LLM 抽象层 (`core/llm.py`) ✅
- **状态**：完成 | commit: `900db88`
- **涉及文件**：`fixlot/core/llm.py`, `tests/test_llm.py`
- **实现要点**：
  - `LLMProvider` 抽象类：`async invoke(messages) -> str`
  - `MockLLM`：注入预设响应列表，按顺序返回
  - `OpenAIProvider`：封装 OpenAI SDK
  - `AnthropicProvider`：封装 Anthropic SDK
- **验证**：`MockLLM` 单测——注入 `["hello", "world"]`，调用两次分别返回 "hello" 和 "world"

### T1.2 [P] [T] 配置加载 (`config/loader.py`) ✅
- **状态**：完成 | commit: `900db88`
- **涉及文件**：`fixlot/config/loader.py`, `fixlot/config/credentials.py`, `tests/test_config.py`
- **实现要点**：
  - `load_config(work_dir)` 加载 `.fixlot/config.yaml`（不存在则使用默认值）
  - `load_credentials(work_dir)` 从 `.env` 加载 API Key
  - 默认配置：max_rounds=5, timeout=300, test_command="pytest", provider="openai"
- **验证**：创建临时 YAML 和 .env，加载后验证配置值正确；缺少 .env 时提示用户

---

## Phase 2：工具层

### T2.1 [T] 工具注册 (`tools/registry.py`) ✅
- **状态**：完成 | commit: `60043f7`
- **涉及文件**：`fixlot/tools/registry.py`, `tests/test_registry.py`
- **实现要点**：
  - `Tool` 数据类：`{name, description, parameters_schema, handler}`
  - `ToolRegistry`：`register(tool)`, `dispatch(action) -> ActionResult`
  - `ActionResult` 数据类：`{success, output, error}`
- **验证**：注册一个 mock tool，dispatch 后验证返回正确结果

### T2.2 [T] 文件操作工具 (`tools/file.py`) ✅
- **状态**：完成 | commit: `60043f7`
- **涉及文件**：`fixlot/tools/file.py`, `tests/test_file_tools.py`
- **实现要点**：
  - `read_file(path)` 读取文件内容
  - `write_file(path, content)` 写入文件
  - 路径检查（调用护栏，但护栏此时尚未实现——先做基础路径验证）
- **验证**：创建临时文件 → read_file 验证内容 → write_file 修改 → read_file 验证修改

### T2.3 [T] Shell 执行工具 (`tools/shell.py`) ✅
- **状态**：完成 | commit: `60043f7`
- **涉及文件**：`fixlot/tools/shell.py`, `tests/test_shell_tools.py`
- **实现要点**：
  - `subprocess.run` 封装，捕获 stdout/stderr/returncode
  - 超时控制（默认 60s）
- **验证**：执行 `echo hello` 验证输出；执行 `sleep 0.1` 验证超时

### T2.4 [D] [T] 测试运行工具 (`tools/test_runner.py`) ✅
- **状态**：完成 | commit: `60043f7`
- **涉及文件**：`fixlot/tools/test_runner.py`, `tests/test_test_runner.py`
- **依赖**：T2.3（shell 工具）
- **实现要点**：
  - 调用 `pytest --json-report` 或解析 pytest 文本输出
  - 返回结构化结果：`{passed, total, passed_count, failed_count, failures}`
- **验证**：在有测试文件的项目中运行，验证解析结果正确

---

## Phase 3：治理护栏

### T3.1 [T] Shell 危险命令拦截 (`guardrails/shell_guard.py`) ✅
- **状态**：完成 | commit: `9acd128`
- **涉及文件**：`fixlot/guardrails/shell_guard.py`, `tests/test_shell_guard.py`
- **实现要点**：
  - 危险模式列表：`rm -rf`, `sudo`, `chmod 777`, `mkfs`, `dd if=`, fork bomb, `curl ... | sh`, `wget ... | sh`, `eval`, `> /dev/`
  - `check(command) -> GuardResult {allowed, reason}`
- **验证**：传入 `rm -rf /` → 断言 `allowed=False`；传入 `echo hello` → 断言 `allowed=True`

### T3.2 [T] 文件操作沙箱 (`guardrails/file_guard.py`) ✅
- **状态**：完成 | commit: `9acd128`
- **涉及文件**：`fixlot/guardrails/file_guard.py`, `tests/test_file_guard.py`
- **实现要点**：
  - `check(path, work_dir) -> GuardResult`
  - 检查路径是否在工作目录内
  - 检查路径是否访问系统敏感目录
- **验证**：传入 `/etc/passwd` → 断言 `allowed=False`；传入 `./src/main.py` → 断言 `allowed=True`

---

## Phase 4：反馈闭环（重点深入）

### T4.1 [T] 测试结果解析 (`feedback/parser.py`) ✅
- **状态**：完成 | commit: `e347ccb`
- **涉及文件**：`fixlot/feedback/parser.py`, `tests/test_parser.py`
- **实现要点**：
  - 正则解析 pytest 摘要行和失败详情
  - 提取：test_name, error_type, message, traceback
  - 输出：`list[TestFailure]`
- **验证**：构造 pytest 失败输出文本 → 解析 → 验证失败数量、测试名、错误类型

### T4.2 [T] 失败分类 (`feedback/classifier.py`) ✅
- **状态**：完成 | commit: `e347ccb`
- **涉及文件**：`fixlot/feedback/classifier.py`, `tests/test_classifier.py`
- **实现要点**：
  - `FailureType` 枚举：SYNTAX_ERROR, IMPORT_ERROR, NAME_ERROR, TYPE_ERROR, ASSERTION_ERROR, ATTRIBUTE_ERROR, TIMEOUT, UNKNOWN
  - 规则匹配：根据错误消息中的关键词分类
- **验证**：构造各类失败 → 分类 → 验证分类结果正确

### T4.3 [T] 修正策略 (`feedback/correction.py`) ✅
- **状态**：完成 | commit: `e347ccb`
- **涉及文件**：`fixlot/feedback/correction.py`, `tests/test_correction.py`
- **实现要点**：
  - 每种 FailureType 对应一个修正指令模板
  - 生成结构化的修正指令文本
- **验证**：传入 ASSERTION_ERROR 失败 → 验证指令包含测试名、期望值、实际值

### T4.4 [D] [T] 反馈循环状态机 (`feedback/loop.py`) ✅
- **状态**：完成 | commit: `e347ccb`
- **涉及文件**：`fixlot/feedback/loop.py`, `tests/test_feedback_loop.py`
- **依赖**：T4.1, T4.2, T4.3
- **实现要点**：
  - `LoopState` 枚举：IDLE, RUNNING, ANALYZING, CORRECTING, PASSED, MAX_RETRIES, ERROR
  - `FeedbackLoop` 类：控制轮数、记录每轮结果
  - 使用 mock LLM 测试多轮修正
- **验证**：mock LLM 注入 3 轮响应（错误→错误→正确）→ 验证循环在第 3 轮 PASSED

---

## Phase 5：核心引擎

### T5.1 [D] [T] 上下文组装 (`core/context.py`) ✅
- **状态**：完成 | commit: `738488c`
- **涉及文件**：`fixlot/core/context.py`, `tests/test_context.py`
- **依赖**：T1.1（LLM 抽象层）
- **实现要点**：
  - System prompt：定义 agent 角色、可用工具、输出格式
  - User prompt：任务描述 + 历史 + 反馈
  - 控制 token 用量
- **验证**：构造任务和配置 → 验证生成的 messages 包含 system prompt 和 user prompt

### T5.2 [D] [T] 主循环 (`core/loop.py`) ✅
- **状态**：完成 | commit: `738488c`
- **涉及文件**：`fixlot/core/loop.py`, `tests/test_loop.py`
- **依赖**：T1.1, T1.2, T2.1, T3.1, T3.2, T4.4, T5.1
- **实现要点**：
  - 伪代码实现：context → LLM → parse → guard → execute → feedback → (loop/stop)
  - 动作解析：从 LLM 文本输出中提取 JSON 格式的动作
  - 停机条件：测试通过 或 达到最大轮数 或 护栏拦截
- **验证**：mock LLM 注入"写文件→跑测试→通过"序列 → 验证循环正常结束

---

## Phase 6：记忆 + CLI

### T6.1 [P] [T] 记忆存储 (`memory/store.py`, `memory/retrieval.py`) ✅
- **状态**：完成 | commit: `7b326c0`
- **涉及文件**：`fixlot/memory/store.py`, `fixlot/memory/retrieval.py`, `tests/test_memory.py`
- **实现要点**：
  - 会话记忆：内存中存储对话历史和修正历史
  - 项目记忆：`.fixlot/memory.json` 读写
- **验证**：写入记忆 → 检索 → 验证内容一致

### T6.2 [D] CLI 入口 (`cli/main.py`) ✅
- **状态**：完成 | commit: `7b326c0`
- **涉及文件**：`fixlot/cli/main.py`, `fixlot/__main__.py`
- **依赖**：T5.2（主循环）
- **实现要点**：
  - `argparse` 解析参数：task, --dir, --provider, --max-rounds, --model, --verbose
  - 加载配置 → 初始化 LLM → 运行主循环 → 输出结果
- **验证**：`python -m fixlot "echo hello" --verbose` 运行并输出日志

---

## Phase 7：机制演示 + 分发

### T7.1 [D] [T] 机制演示测试 ✅
- **状态**：完成 | commit: `f389ffc`
- **涉及文件**：`tests/demo/test_guardrail_demo.py`, `tests/demo/test_feedback_demo.py`, `tests/demo/test_deep_dive_demo.py`
- **依赖**：所有 Phase 1-5
- **实现要点**：
  1. **护栏拦截演示**：mock LLM 输出危险命令 → 护栏拦截 → 验证不执行
  2. **反馈闭环演示**：mock LLM 注入错误代码 → 测试失败 → 反馈解析 → 修正指令 → 下一轮
  3. **重点维度演示**：完整的反馈闭环管道（parser→classifier→correction→loop）
- **验证**：`pytest tests/demo/` 全部通过，不依赖网络

### T7.2 [D] Dockerfile ✅
- **状态**：完成 | commit: `f389ffc`
- **涉及文件**：`Dockerfile`
- **依赖**：T6.2（CLI 入口）
- **实现要点**：Python 3.10 基础镜像，安装依赖，ENTRYPOINT 指向 fixlot
- **验证**：`docker build -t fixlot . && docker run --rm fixlot --help`

### T7.3 [D] PyInstaller 打包 ✅
- **状态**：完成 | commit: `f389ffc`
- **涉及文件**：`scripts/build_binary.py`, `fixlot.spec`
- **依赖**：T6.2（CLI 入口）
- **实现要点**：PyInstaller 配置，单文件输出
- **验证**：`pyinstaller fixlot.spec` 产出可执行文件

### T7.4 [D] README.md ✅
- **状态**：完成 | commit: `f389ffc`
- **涉及文件**：`README.md`
- **依赖**：T7.2, T7.3
- **实现要点**：项目简介、安装、运行、分发命令、目录结构、安全边界说明

### T7.5 [D] WebUI 界面 ✅
- **状态**：完成 | commit: `f389ffc`
- **目标**：实现 Flask Web 界面
- **涉及文件**：`fixlot/webui/app.py`, `fixlot/webui/templates/index.html`, `tests/test_webui.py`
- **依赖**：T5.2（主循环）
- **实现要点**：Flask app + HTML 前端，任务提交/状态查询 API，暗色主题 UI
- **验证**：`pytest tests/test_webui.py` 全部通过；`python -m fixlot.webui.app` 可启动

### T7.6 [D] 部署配置 ✅
- **状态**：完成 | commit: `f389ffc`
- **目标**：创建部署配置文件，支持一键部署
- **涉及文件**：`render.yaml`, `.gitlab-ci.yml`, `Dockerfile`（更新支持 WebUI 模式）
- **依赖**：T7.5
- **实现要点**：Render 自动检测 render.yaml；Dockerfile 支持 CLI/Web 双模式；GitLab CI 配置
- **验证**：`docker build -t fixlot . && docker run --rm -e FIXLOT_MODE=web -p 5000:5000 fixlot`

---

## Phase 8：收尾

### T8.1 AGENT_LOG.md ✅
- **状态**：完成
- **涉及文件**：`AGENT_LOG.md`

### T8.2 REFLECTION.md ✅
- **状态**：完成
- **涉及文件**：`REFLECTION.md`

---

## 依赖关系图

```
Phase 0: T0.1, T0.2 [并行]

Phase 1: T1.1 → T1.2 [T1.1与T1.2可并行]

Phase 2: T2.1 → T2.2, T2.3 [T2.2与T2.3可并行]
         T2.3 → T2.4

Phase 3: T3.1, T3.2 [并行]

Phase 4: T4.1, T4.2, T4.3 [并行] → T4.4

Phase 5: T1.1 + T1.2 + T2.1 + T3.1 + T3.2 + T4.4 → T5.1 → T5.2

Phase 6: T6.1 [与Phase 5并行] → T6.2

Phase 7: T5.2 + T6.2 → T7.1, T7.2, T7.3 [T7.1/T7.2/T7.3可并行]
         T7.2 + T7.3 → T7.4
         T5.2 → T7.5 → T7.6

Phase 8: T8.1, T8.2 [可并行，最后完成]
```

---

## 并行批次建议

| 批次 | Tasks | 说明 |
|------|-------|------|
| 1 | T0.1, T0.2 | 基础设施 |
| 2 | T1.1, T1.2, T2.1, T3.1, T3.2 | LLM抽象+配置+工具注册+护栏 |
| 3 | T2.2, T2.3, T4.1, T4.2, T4.3 | 文件+Shell工具+反馈前三层 |
| 4 | T2.4, T4.4 | 测试运行+反馈循环 |
| 5 | T5.1, T6.1 | 上下文+记忆 |
| 6 | T5.2 | 主循环（核心集成） |
| 7 | T6.2 | CLI入口 |
| 8 | T7.1, T7.2, T7.3 | 演示+分发 |
| 9 | T7.4, T7.5, T7.6 | 文档+WebUI+部署 |
| 10 | T8.1, T8.2 | 收尾文档 |