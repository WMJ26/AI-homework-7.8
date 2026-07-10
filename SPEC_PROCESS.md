# SPEC_PROCESS.md — fixlot 规约与计划生成过程记录

## 1. Brainstorming 关键节点

### 1.1 初始意图
用户明确选择作业 A（Coding Agent Harness），并对 Superpowers 框架有一定了解。初始意图是"构建一个测试驱动的自修正 Coding Agent"，但具体设计细节（语言、重点维度、分发方式等）在 brainstorming 中逐步明确。

### 1.2 智能体追问的关键问题

**轮次 1：核心定位（5 个问题）**
- 编程语言：用户选择 Python——生态成熟，pytest/openai SDK 可用，PyInstaller 打包方便。
- LLM 供应商：用户选择多供应商支持——OpenAI + Anthropic，体现 harness 的抽象层设计。
- 重点深入维度：用户选择反馈闭环——这是最契合"机制必须是代码"要求的维度。
- 分发形态：用户选择容器 + 二进制——兼顾通用性和便捷性。
- 项目命名：用户命名为 fixlot——"fix a lot"的谐音，暗示自动修复。

**轮次 2：交互与深度（4 个问题）**
- 交互模式：CLI 单次任务——简洁实用，避免过度工程化。用户明确不考虑 Web UI（虽然作业要求 WebUI 可访问地址，但那是通用要求第 9 条，需要后续确认如何处理）。
- 反馈闭环深度：测试驱动的自动修正——parser → classifier → correction → re-loop 管道。
- 凭据存储：.env 文件——用户接受明文风险，需在 SPEC 中明确标注。
- 项目命名确认：用户确认 fixlot。

**轮次 3：工具与防护（2 个问题）**
- 工具/动作：基础三件套（读写文件、shell、运行测试）——MVP 范围，足够闭环。
- 治理护栏：Shell 危险命令拦截 + 文件操作沙箱——两层防护。

### 1.3 设计决策处理

**用户采纳的 AI 建议：**
- 模块划分结构（core/tools/guardrails/feedback/memory/config/cli）
- 反馈闭环的四层管道设计（parser → classifier → correction → loop）
- 失败分类的枚举类型设计
- 主循环的伪代码结构

**用户推翻或修正的 AI 建议：**
- （无显著推翻——用户对设计整体认可，签字确认每轮）

**用户主动提出的决策：**
- 项目名称 fixlot
- 多供应商支持
- 反馈闭环为重点
- CLI 单次任务模式

### 1.4 反思：Brainstorming 技能的评价

**做得好的地方：**
- 分轮次追问，逐步细化设计，避免一次性抛出过多问题
- 每轮先呈现设计再确认，用户有充足的审视空间
- 模块划分清晰，数据流图直观

**可改进的地方：**
- 用户在某些轮次未直接输入项目名，需要额外追问——应提供更明确的输入提示
- 可更早地提出"WebUI 要求"与"CLI 单次任务"之间的矛盾（通用要求第 9 条要求 WebUI 可访问地址，但用户选择 CLI 单次任务）
- 对作业要求的"线上部署 URL"和"WebUI 接口"的讨论不够充分

---

## 2. 冷启动验证

### 2.1 验证设置
- **第二个 agent 类型**：Claude (Anthropic)，与主开发 agent 不同
- **提供给 agent 的材料**：仅 `SPEC.md` + `PLAN.md`，不提供任何对话历史或额外解释
- **指定 task**：从 PLAN 中选 T3.1（Shell 护栏）和 T4.1（测试结果解析）
- **指令**：明确告知"遇到不确定之处即暂停询问，而非凭猜测继续"

### 2.2 发现的问题

**问题 1：工具 handler 签名不明确**
- **暂停位置**：T3.1 实现 Shell 护栏时，Claude 询问"check 函数应该返回什么类型？"
- **暴露的 SPEC 缺陷**：SPEC 中只写了 `check(command) -> GuardResult {allowed, reason}`，但没有明确定义 `GuardResult` 的数据结构。Claude 不确定 `allowed` 是 `bool` 还是 `str`，`reason` 在允许时应该为空还是 `"ok"`。
- **修订**：在 SPEC §3.3.1 中补充：`GuardResult` 为 `{allowed: bool, reason: str}`，允许时 `allowed=True, reason=""`，拦截时 `allowed=False, reason="具体原因"`。

**问题 2：pytest 输出格式边界情况**
- **暂停位置**：T4.1 实现 parser 时，Claude 询问"pytest 输出中如果测试名包含 `::` 特殊字符怎么办？以及短摘要行（short test summary info）和失败详情行（FAILURES）的 test_name 格式不一致如何处理？"
- **暴露的 SPEC 缺陷**：SPEC 中只描述了 pytest 的"标准格式"，但没有说明边界情况。例如 `short test summary info` 行格式为 `FAILED path::test_name - message`，而 `FAILURES` 节格式为 `_ test_name _`。此外，pytest 的 `ERRORS` 和 `FAILURES` 是两种不同的节。
- **修订**：在 SPEC §3.4.1 中补充：parser 需同时处理 `FAILURES` 和 `ERRORS` 两种节；需处理 `short test summary info` 中的去重逻辑；test_name 提取时需要处理 `::` 分隔符。

**问题 3：工作目录边界**
- **暂停位置**：Claude 在实现 file_guard 时询问"工作目录是绝对路径还是相对路径？如果用户传入 `..` 但解析后仍在工作目录内，是否允许？"
- **暴露的 SPEC 缺陷**：SPEC 中只说"路径必须在工作目录内"，但没有说明路径解析规则。Claude 不确定是否应该先 `os.path.realpath()` 解析后再判断。
- **修订**：在 SPEC §3.3.2 中明确：路径检查前必须先 `os.path.realpath()` 解析符号链接和相对路径，然后以解析后的绝对路径判断是否在工作目录内。

### 2.3 未被发现的缺陷（实现阶段暴露）
以下问题在冷启动验证中未被发现，但在实际实现时遇到：
- Windows 环境下 shell 命令的引号问题（单引号 vs 双引号）
- 测试环境中预先存在的环境变量对 credentials 加载的干扰
- parser 中 pytest 分隔线格式的 test_name 提取逻辑需要额外处理

### 2.4 对 SPEC/PLAN 的修订总结
| 修订项 | 修订前 | 修订后 |
|--------|--------|--------|
| GuardResult 定义 | 未明确字段类型 | 明确 `allowed: bool`, `reason: str` |
| parser 边界 | 仅处理标准格式 | 补充 ERRORS 节、去重、`::` 处理 |
| 路径解析 | 未说明解析规则 | 明确 `realpath()` 后再判断 |
| 工具 handler 签名 | `read_file(path)` | 统一为 `handler(params: dict) -> ActionResult` |

### 2.5 反思
冷启动验证是 SPEC 质量最有效的反馈机制。主 agent 在 brainstorming 中积累了大量隐性上下文（如"GuardResult 应该用 dataclass"、"pytest 输出格式大家都懂"），这些假设在 SPEC 中未被明文记录。Claude 作为全新 agent 在每个未写明的假设处都遇到了障碍——这恰好证明了"隐性上下文"对 SPEC 清晰度的危害。三个暂停点分别对应了类型定义、边界情况和解析规则——这些都是 SPEC 中最容易"想当然"的部分。

---

## 3. 关键迭代记录

### 迭代 1：从模糊想法到结构化设计
- **输入**：用户说"做作业 A"
- **对话节选**：AI 追问语言、供应商、重点维度、分发、命名
- **决策**：Python + 多供应商 + 反馈闭环 + Docker + 二进制
- **产出**：项目骨架确立

### 迭代 2：模块与架构确认
- **输入**：第一轮选择
- **对话节选**：AI 呈现模块划分和主循环架构
- **决策**：用户确认模块划分和架构
- **产出**：SPEC.md 结构框架

### 迭代 3：反馈闭环深度设计
- **输入**：架构确认
- **对话节选**：AI 详细设计反馈闭环的四层管道
- **决策**：用户确认 parser → classifier → correction → loop 设计
- **产出**：反馈闭环完整设计，可单测验证

### 迭代 4：汇总确认
- **输入**：全部设计要素
- **对话节选**：AI 汇总设计要点，逐一确认
- **决策**：全部确认，进入 SPEC 编写
- **产出**：SPEC.md 正式文档