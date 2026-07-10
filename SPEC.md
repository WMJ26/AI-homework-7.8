# fixlot — SPEC.md

> A test-driven self-correcting Coding Agent Harness.
> Agent = LLM + Harness. fixlot is the harness.

## 1. 问题陈述

### 要解决的问题
现有的 Coding Agent 在面对代码错误时，依赖 LLM 的"自我检查"——在提示词中要求模型"检查你的代码是否正确"。这种方法不可靠：LLM 可能忽视错误、产生幻觉、或反复犯同一类错误。fixlot 的目标是将**反馈闭环**从"提示词级建议"升级为"代码级确定性机制"——用**确定性代码**解析测试结果、分类失败模式、驱动结构化修正，不依赖 LLM 的自我觉察。

### 目标用户
- 使用 AI 辅助编码的开发者，希望 agent 能自动根据测试失败修正代码
- 对 agent 行为有安全要求的团队，需要治理护栏和可审计的修正记录

### 为什么值得做
当 LLM 完成大部分编码时，工程师的价值在于构建可靠的工程系统：让 agent 的反馈闭环不是"运气好就对了"，而是"每次失败都能被正确解析、分类、驱动修正"。这层工程是当前 agent 框架普遍薄弱的环节。

---

## 2. 用户故事

| # | 用户故事 | INVEST |
|---|---------|--------|
| US1 | 作为开发者，我输入一个编码任务，fixlot 能自动读取项目文件、编写代码、运行测试，让我无需手动操作 | I/N/E/V/T |
| US2 | 作为开发者，当 agent 的代码导致测试失败时，fixlot 能自动解析失败原因并修正代码，最多重试 N 轮 | I/N/E/V/T |
| US3 | 作为开发者，当 agent 尝试执行危险命令（如 rm -rf）时，fixlot 应拦截并拒绝执行，保护我的系统安全 | I/N/E/V/T |
| US4 | 作为开发者，我可以通过 .env 文件配置 LLM API Key，fixlot 首次运行时会引导我完成配置 | I/N/E/V/T |
| US5 | 作为开发者，我可以选择不同的 LLM 供应商（OpenAI / Anthropic 等），fixlot 能适配不同 API | I/N/E/V/T |
| US6 | 作为开发者，fixlot 在执行任务时，文件操作被限制在项目工作目录内，不能访问系统敏感目录 | I/N/E/V/T |
| US7 | 作为开发者，我可以通过 Docker 一键启动 fixlot，或在本地安装二进制文件直接运行 | I/N/E/V/T |

---

## 3. 功能规约

### 3.1 核心引擎 (`core/`)

#### 3.1.1 主循环 (`loop.py`)
- **输入**：用户任务描述、工作目录路径、配置
- **行为**：
  1. 组装上下文（任务 + 历史 + 记忆）
  2. 调用 LLM 获取下一步动作
  3. 解析 LLM 响应为结构化动作
  4. 通过护栏检查动作安全性
  5. 分发动作到工具层执行
  6. 收集执行结果
  7. 通过反馈闭环分析结果
  8. 若测试通过 → 停机；若失败 → 回灌反馈 → 回到步骤 1
- **边界条件**：最大轮数上限（默认 10）、超时限制（默认 300s/轮）
- **错误处理**：LLM 调用失败重试 3 次；解析失败则要求 LLM 重新输出

#### 3.1.2 LLM 抽象层 (`llm.py`)
- **输入**：messages（上下文列表）、provider 标识
- **行为**：封装不同 LLM 供应商的 API 调用
- **输出**：统一的文本响应
- **支持供应商**：OpenAI（GPT-4o）、Anthropic（Claude），可扩展
- **Mock 模式**：注入 `MockLLM` 时返回预设响应，用于单测

#### 3.1.3 上下文组装 (`context.py`)
- **输入**：任务、历史记录、记忆、项目文件摘要
- **行为**：组装 system prompt + user prompt，控制 token 用量
- **输出**：messages 列表

### 3.2 工具层 (`tools/`)

#### 3.2.1 工具注册 (`registry.py`)
- **行为**：注册可用工具，根据 LLM 输出的动作名分发给对应工具
- **工具定义格式**：`{name, description, parameters_schema, handler}`

#### 3.2.2 文件操作 (`file.py`)
- `read_file(path)`：读取文件内容，返回文本
- `write_file(path, content)`：写入文件内容
- **边界**：路径必须在工作目录内，否则被护栏拦截
- **错误处理**：文件不存在 → 返回错误信息；写入权限不足 → 返回错误

#### 3.2.3 Shell 执行 (`shell.py`)
- `run_command(cmd)`：执行 shell 命令，返回 stdout/stderr/exit_code
- **边界**：命令必须先通过护栏检查
- **错误处理**：超时（默认 60s）→ 终止进程

#### 3.2.4 测试运行 (`test_runner.py`)
- `run_tests()`：在工作目录执行测试命令（默认 `pytest`，可配置）
- **输出**：`{passed: bool, total: int, passed_count: int, failed_count: int, failures: [...]}`

### 3.3 治理护栏 (`guardrails/`)

#### 3.3.1 Shell 危险命令拦截 (`shell_guard.py`)
- **输入**：命令字符串
- **行为**：正则匹配危险模式
- **危险模式**：`rm -rf /`, `sudo`, `chmod 777`, `mkfs`, `dd if=`, `:(){ :|:& };:`, `> /dev/sda`, `curl ... | sh`, `wget ... -O - | sh`, `eval`, 包含 `..` 的路径遍历
- **输出**：`{allowed: bool, reason: str}`
- **错误处理**：拦截时返回明确拒绝信息，不执行命令

#### 3.3.2 文件操作沙箱 (`file_guard.py`)
- **输入**：文件路径、工作目录根
- **行为**：检查路径是否在工作目录内
- **输出**：`{allowed: bool, reason: str}`
- **保护范围**：禁止访问 `~/.ssh`, `/etc`, `/System`, `C:\Windows`, `C:\Program Files` 等系统路径

### 3.4 反馈闭环 (`feedback/`) — 重点深入

#### 3.4.1 测试结果解析 (`parser.py`)
- **输入**：pytest 原始输出文本
- **行为**：正则提取失败测试名、错误类型、堆栈信息
- **输出**：`[{test_name, error_type, message, traceback}]`
- **确定性**：纯正则匹配，不依赖 LLM

#### 3.4.2 失败分类 (`classifier.py`)
- **输入**：解析后的失败列表
- **行为**：规则匹配，将失败分为：
  - `SYNTAX_ERROR`：语法错误
  - `IMPORT_ERROR`：导入错误
  - `NAME_ERROR`：未定义变量/函数
  - `TYPE_ERROR`：类型错误
  - `ASSERTION_ERROR`：断言失败
  - `ATTRIBUTE_ERROR`：属性错误
  - `TIMEOUT`：超时
  - `UNKNOWN`：其他
- **输出**：`[{test_name, category, message, traceback}]`
- **确定性**：纯规则匹配，不依赖 LLM

#### 3.4.3 修正策略 (`correction.py`)
- **输入**：分类后的失败列表
- **行为**：根据失败类别生成结构化修正指令
- **输出**：修正指令文本（注入下轮 LLM 上下文）
- **示例**：
  - `ASSERTION_ERROR` → "测试 'test_add' 断言失败：期望 3，实际 2。请检查实现逻辑。"
  - `IMPORT_ERROR` → "模块 'foo' 导入失败。请确认模块已安装或修正导入路径。"
  - `SYNTAX_ERROR` → "文件 'main.py' 第 12 行有语法错误。请修正语法。"
- **确定性**：模板生成，不依赖 LLM

#### 3.4.4 反馈循环状态机 (`loop.py`)
- **状态**：`IDLE → RUNNING → ANALYZING → CORRECTING → (PASSED | MAX_RETRIES)`
- **行为**：控制修正轮数，记录每轮结果
- **最大轮数**：默认 5 轮，可配置
- **输出**：最终状态 + 每轮记录

### 3.5 记忆 (`memory/`)

#### 3.5.1 会话记忆 (`store.py`)
- **行为**：存储当前会话的对话历史、修正历史
- **存储**：内存中（会话内），不持久化

#### 3.5.2 项目记忆 (`retrieval.py`)
- **行为**：存储项目级约定、已知错误模式
- **存储**：工作目录下的 `.fixlot/memory.json`
- **检索**：根据当前任务关键词检索相关记忆

### 3.6 配置 (`config/`)

#### 3.6.1 配置加载 (`loader.py`)
- **输入**：工作目录
- **行为**：加载 `.fixlot/config.yaml`（项目级）+ `.env`（凭据）
- **配置项**：max_rounds, timeout, test_command, allowed_tools, work_dir, provider

#### 3.6.2 凭据管理 (`credentials.py`)
- **行为**：从 `.env` 加载 API Key
- **安全说明**：`.env` 为明文存储，存在以下风险：
  - 文件权限不当可被其他用户读取
  - 进程环境变量对同进程子进程可见
  - 若误提交 Git 则凭据泄露
  - **对策**：`.env` 已加入 `.gitignore`；README 明确警告风险；建议用户使用文件权限限制（`chmod 600`）

### 3.7 CLI 入口 (`cli/main.py`)

- **命令**：`fixlot "任务描述" --dir /path/to/project`
- **参数**：
  - `task`：位置参数，任务描述
  - `--dir`：工作目录（默认当前目录）
  - `--provider`：LLM 供应商（默认 openai）
  - `--max-rounds`：最大修正轮数（默认 5）
  - `--model`：模型名称
- **输出**：任务执行结果、每轮修正记录

---

## 4. 非功能性需求

### 4.1 性能
- 单轮 LLM 调用 + 工具执行应在 120s 内完成
- 上下文组装应控制 token 用量（system prompt < 2K tokens）

### 4.2 安全（凭据威胁模型）
| 威胁 | 风险等级 | 对策 |
|------|---------|------|
| `.env` 文件被其他用户读取 | 中 | README 说明 `chmod 600`；文件权限检查 |
| `.env` 被误提交 Git | 高 | `.gitignore` 包含 `.env`；pre-commit hook 检查 |
| API Key 泄露到日志 | 高 | 日志中屏蔽 key；不记录完整 API 请求 |
| 进程环境变量泄露 | 低 | 说明风险；建议使用临时环境变量 |
| 危险命令执行 | 高 | Shell 护栏拦截；文件沙箱限制 |

### 4.3 可用性
- 首次运行引导用户创建 `.env` 文件
- 清晰的错误提示（LLM 调用失败、解析失败、护栏拦截等）
- 单命令启动（CLI 一行命令即可执行任务）

### 4.4 可观测性
- 每轮执行日志（动作、结果、反馈）
- 最终摘要（轮数、成功/失败、修正次数）
- verbose 模式输出详细日志

---

## 5. 系统架构

### 组件图
```
┌──────────────┐
│   CLI 入口    │  fixlot "task" --dir .
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────────┐
│               core/loop                   │
│  ┌────────────────────────────────────┐   │
│  │  context → LLM → parse → guard →  │   │
│  │  execute → feedback → (loop/stop) │   │
│  └────────────────────────────────────┘   │
└──┬────────┬──────────┬──────────┬────────┘
   │        │          │          │
   ▼        ▼          ▼          ▼
┌──────┐ ┌──────┐ ┌────────┐ ┌────────┐
│tools │ │guard │ │feedback│ │memory  │
│      │ │rails │ │        │ │        │
│ file │ │shell │ │parser  │ │store   │
│ shell│ │file  │ │classify│ │retrieve│
│ test │ │      │ │correct │ │        │
└──────┘ └──────┘ └────────┘ └────────┘
```

### 数据流
1. 用户输入 → CLI 解析参数 → 加载配置
2. 配置 + 任务 → 上下文组装 → 注入 LLM
3. LLM 输出 → 动作解析 → 护栏检查
4. 安全动作 → 工具分发 → 执行
5. 执行结果 → 反馈分析 → 回灌或停机

### 外部依赖
- LLM API：OpenAI API / Anthropic API
- 测试框架：pytest（可配置）
- 无其他外部服务依赖

---

## 6. 数据模型

### 主要实体

```
Action:
  - tool: str          # 工具名
  - params: dict       # 参数
  - raw: str           # LLM 原始输出

ActionResult:
  - success: bool
  - output: str
  - error: str | None

GuardResult:
  - allowed: bool
  - reason: str

TestFailure:
  - test_name: str
  - category: FailureType  # enum
  - message: str
  - traceback: str

FeedbackResult:
  - passed: bool
  - failures: list[TestFailure]
  - correction_hint: str

RoundRecord:
  - round: int
  - action: Action
  - result: ActionResult
  - feedback: FeedbackResult

LoopState:
  - IDLE | RUNNING | ANALYZING | CORRECTING | PASSED | MAX_RETRIES | ERROR
```

---

## 7. 凭据与分发设计

### 7.1 凭据管理
- **方案**：`.env` 文件存储
- **录入**：首次运行 `fixlot` 时检测 `.env` 是否存在，不存在则提示用户创建
- **更新**：用户手动编辑 `.env` 文件
- **清除**：删除 `.env` 文件即可
- **安全**：`.env` 加入 `.gitignore`；README 说明明文风险；建议 `chmod 600`

### 7.2 分发

#### Docker 容器
```bash
docker build -t fixlot .
docker run --rm -v $(pwd):/workspace -v $(pwd)/.env:/workspace/.env fixlot "your task"
```

#### 原生二进制
- **工具**：PyInstaller 打包为单文件
- **平台**：Windows (.exe), macOS, Linux
- **安装**：下载二进制 → 放入 PATH → 运行
- **签名**：macOS 需要 `xattr -d` 解除隔离；Windows 需要 SmartScreen 确认

#### 已知限制
- 需要目标机器安装 Python 3.10+ 和测试框架
- Docker 版需要 Docker 环境
- 二进制版仅支持打包时指定的平台

---

## 8. 技术选型与理由

| 选项 | 选择 | 理由 |
|------|------|------|
| 语言 | **Python 3.10+** | 生态成熟（pytest, openai, anthropic SDK）；开发效率高；PyInstaller 打包方便 |
| LLM SDK | `openai` + `anthropic` | 两个主流供应商的原生 SDK，稳定可靠 |
| 测试框架 | `pytest` | Python 生态标准，输出格式规范，易于解析 |
| CLI 框架 | `argparse`（标准库） | 零依赖，足够简单 |
| 配置格式 | YAML（项目配置）+ .env（凭据） | YAML 可读性好；.env 是通用惯例 |
| 分发 | Docker + PyInstaller | Docker 通用性强；PyInstaller 单文件分发简单 |
| 包管理 | `pip` / `pip-tools` | 标准工具 |

---

## 9. 验收标准

| 功能 | 验收标准 |
|------|---------|
| 主循环 | 给定任务，agent 能完成"读文件→写代码→跑测试"的一个完整循环 |
| LLM 抽象 | 可切换 OpenAI / Anthropic / MockLLM，接口一致 |
| 工具分发 | `read_file`, `write_file`, `run_command`, `run_tests` 四个工具可正常执行 |
| Shell 护栏 | 输入 `rm -rf /` 被拦截，返回拒绝理由 |
| 文件沙箱 | 尝试写入 `/etc/passwd` 被拦截，返回拒绝理由 |
| 反馈闭合 | 给 mock LLM 注入错误代码 → 测试失败 → parser 正确解析 → classifier 正确分类 → correction 生成修正指令 |
| 自修正循环 | mock 场景：第1轮失败 → 第2轮修正 → 第3轮通过（或达上限） |
| 凭据安全 | `.env` 不存在时提示用户；`.env` 在 `.gitignore` 中 |
| 分发 | `docker build && docker run` 可正常运行；`pyinstaller` 可产出二进制 |
| Mock 单测 | 移除真实 LLM 后，核心机制（反馈、护栏、循环）可通过确定性单测验证 |

---

## 10. 风险与未决问题

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| LLM 输出的动作格式不稳定 | 解析失败，循环中断 | 严格 prompt 约束输出格式；解析失败时要求 LLM 重试 |
| 测试框架输出格式差异 | parser 解析失败 | 先支持 pytest 标准格式；后续扩展其他框架 |
| 修正循环可能无限循环 | 资源浪费 | 硬上限 max_rounds |
| 二进制跨平台打包问题 | 分发失败 | CI 中多平台构建测试 |
| 危险命令模式遗漏 | 安全风险 | 白名单 + 黑名单组合；持续更新模式库 |

---

## 11. 领域与机制设计（A 专属）

### 领域分析：Coding
| 维度 | Coding 领域的体现 |
|------|------------------|
| **反馈信号** | 测试结果（pytest pass/fail）、lint 输出、类型检查结果 |
| **危险动作** | 危险 shell 命令、越权文件操作、对外网络请求 |
| **所需工具** | 读写文件、执行 shell、运行测试 |
| **记忆需求** | 项目代码结构、约定、历史错误模式 |

### 机制设计（代码实现，非提示词）

| 机制 | 实现方式 | 可单测性 |
|------|---------|---------|
| 反馈信号 | `parser.py` 正则解析 + `classifier.py` 规则分类 | 构造测试输出文本，验证解析和分类结果 |
| 反馈回灌 | `correction.py` 模板生成修正指令 → 注入 LLM 上下文 | 构造失败列表，验证修正指令内容 |
| 修正循环 | `loop.py` 状态机控制轮数 | 用 mock LLM 模拟多轮修正 |
| 危险动作拦截 | `shell_guard.py` 正则匹配 + `file_guard.py` 路径检查 | 直接传入命令/路径，断言拦截结果 |
| 工具分发 | `registry.py` 注册表映射 | 注册工具后调用，验证分发正确 |

### 重点维度：反馈闭环
选择反馈闭环作为重点深入，因为：
1. 它天然由代码构成（parser, classifier, correction, loop），最契合"机制必须是代码"的要求
2. 它是 agent 自我修正能力的核心，直接影响 agent 的实用性
3. 测试驱动修正是最清晰的客观反馈信号（测试结果要么 pass 要么 fail）
4. 容易用 mock LLM 做确定性单测：注入"产生错误代码"的 LLM 响应，验证整个反馈管道