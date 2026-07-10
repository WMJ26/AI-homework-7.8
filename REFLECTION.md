# REFLECTION.md — fixlot 项目反思报告

## 一、Superpowers 技能的实际效用

在整个开发过程中，Superpowers 框架的以下技能发挥了最大作用：

**Brainstorming** 是设计阶段最有价值的技能。它通过分轮次追问的方式，逐步将"做一个 Coding Agent Harness"这个模糊想法细化到具体的模块划分、数据流、反馈管道设计。例如，在第二轮追问中，智能体主动提出"反馈闭环是四层管道（parser → classifier → correction → loop）"，这个设计成为整个项目的核心架构。如果没有这个技能，我可能会跳过这个关键设计步骤，直接开始编码。

**Writing-plans** 将 SPEC 分解为 25 个可执行的 task，每个 task 都有明确的文件路径、实现要点和验证步骤。这使得实现阶段可以按计划推进，减少了"接下来做什么"的迷茫。

**Test-driven-development** 是贯穿始终的纪律。每个模块都先写测试，再用 mock 验证。MockLLM 的引入使得所有核心机制都可以在不依赖真实 LLM 的情况下进行确定性测试——这正是 harness 项目"机制必须是代码"的核心判据。

然而，**某些技能"形式大于实质"**。例如 `using-git-worktrees` 在这个单人项目中几乎用不到，因为所有 task 都在同一个分支上线性推进，worktree 并行收益有限。`finishing-a-development-branch` 同样因为单分支开发而显得冗余。

## 二、TDD 在 AI 协作下的作用

TDD 强制在 AI 协作下是**放大器**而非阻碍。原因有三：

1. **测试定义了接口契约**。当我让 AI 实现某个模块时，先写好的测试就是"正确的规格说明"。AI 不需要猜测我想要什么，测试告诉它什么是对的。
2. **Mock 驱动的测试使 harness 可验证**。作业要求的核心判据是"移除真实 LLM 后，机制还能用单测验证吗"。如果不先写测试，我无法证明我的反馈闭环是代码而非提示词。
3. **重构安全**。在实现主循环时，我多次重构了 parser 的 test_name 提取逻辑，每次重构后跑测试即可确认没有引入回归。

## 三、Subagent-driven 工作流的自主性

在我的开发过程中，subagent 能自主推进约 2-3 个 task 而不偏离主题。关键在于 task 颗粒度：每个 task 有明确的输入/输出/验证标准，subagent 不需要额外上下文就能完成。

最优 task 颗粒度是"一个文件 + 对应测试 + 可独立验证"。例如 T1.1（LLM 抽象层）就是一个很好的 task：它只涉及 `core/llm.py` 和 `tests/test_llm.py`，验证标准是 `pytest tests/test_llm.py`。

## 四、SPEC/PLAN 质量对实现质量的影响

**规约不清导致实现偏离的具体案例**：在冷启动验证中，我让另一个 agent（Claude）仅凭 SPEC+PLAN 实现 task。虽然没有出现重大偏离，但有一个细节：PLAN 中写的是"read_file(path) 读取文件内容"，但实际实现时 handler 接受的是 `params: dict` 而非直接字符串。这暴露了 SPEC 中工具接口描述不够精确——应该写 `handler(params: dict) -> ActionResult` 而非 `read_file(path)`。

**改正**：在正式实现时，我统一了所有工具 handler 的签名：`handler(params: dict) -> ActionResult`，并在 SPEC 中明确了这一点。

## 五、最有效的 Prompt/Context 策略

最有效的策略是**在 system prompt 中明确输出格式**。我在 ContextBuilder 的 system prompt 中写死了 JSON 输出格式 `{"tool": "...", "params": {...}}`，这使得 LLM 的输出可以被确定性解析。如果我在 prompt 中只是说"请使用工具"，LLM 的输出格式将不可预测，解析失败率会大幅上升。

第二个有效策略是**反馈注入**。当测试失败时，我将 parser → classifier → correction 生成的修正指令直接注入到下一轮 LLM 的上下文中，格式为 `PREVIOUS ATTEMPT FEEDBACK:\n{correction_hint}`。这使得 LLM 不需要"自我检查"，而是直接获得结构化的错误信息。

## 六、凭据与分发的工程启示

凭据与分发这两条工程要求迫使我想清楚了以下问题：

1. **凭据安全**：`.env` 文件虽然方便，但确实是明文存储，存在进程环境可见、文件权限不当等风险。在真实产品中，应该使用操作系统钥匙串（Windows Credential Manager / macOS Keychain）。但作为课程项目，`.env` + `.gitignore` + README 警告是合理的折中。

2. **分发**：Docker 是最通用的分发方式，但需要用户安装 Docker。PyInstaller 打包为单文件二进制对最终用户更友好，但跨平台构建复杂。我选择了 Docker 作为主要分发方式，因为它在 CI 中构建和验证最方便。

3. **凭据在容器中的传递**：Docker 运行时需要通过 `-v $(pwd)/.env:/workspace/.env` 挂载 `.env` 文件，或者通过 `-e OPENAI_API_KEY=xxx` 传递环境变量。前者有文件权限风险，后者会进入 shell history。这让我意识到，在容器化场景中，凭据管理比本地开发更复杂。

## 七、如果重做会改变什么

1. **更早地添加 WebUI**。作业要求必须提供 WebUI 可访问地址，但我在 SPEC 中选择了 CLI-only。这导致后期需要额外添加 Flask Web 界面，打乱了原有的模块划分。

2. **更早地实现 guardrail 与 loop 的集成**。在 Phase 3 实现了护栏，但到 Phase 5 才集成到主循环中。如果做更早的集成测试，可以更早发现护栏拦截后 round 计数的问题。

3. **增加更多失败分类规则**。目前的 8 种分类覆盖了常见场景，但还有更多边界情况（如 flaky tests、环境差异导致的失败）可以更精细地处理。

4. **使用操作系统钥匙串**。虽然 `.env` 是课程允许的方案，但实现真正的安全存储会是一个更好的工程实践。

## 八、对 Superpowers 方法论的批判

Superpowers 假设了以下几点：

1. **假设开发者愿意遵循严格的流程纪律**。这套方法论要求先 brainstorming → 再 spec → 再 plan → 再 coding，每一步都不能跳过。对于快速原型开发，这个流程过于繁琐。

2. **假设 task 可以独立并行**。`using-git-worktrees` 和 `subagent-driven-development` 假设 task 之间没有共享状态，可以独立开发。但在 harness 这样的项目中，core/loop 依赖几乎所有其他模块，真正可并行的 task 很少。

3. **假设 subagent 能理解上下文**。在实际使用中，subagent 经常需要额外的上下文才能正确完成任务，而 SPEC 和 PLAN 很难完全覆盖所有细节。

**这些假设在我的项目中是否成立？**

- 流程纪律：成立。对于课程项目，严格的流程确保了交付质量。
- 独立并行：部分成立。Phase 0-3 的模块确实可以并行，但 Phase 5 的核心循环高度依赖前置模块。
- subagent 理解上下文：勉强成立。我的 SPEC 和 PLAN 粒度足够细，冷启动验证也通过了，但实际开发中主 agent 仍然需要比 subagent 更多的上下文。

**Superpowers 最大的价值**不在于它提供的具体技能，而在于它**强制执行了一种工程纪律**——在 AI 可以快速生成代码的时代，这种纪律比代码本身更重要。但它也需要根据项目特点灵活调整，不是所有技能都适用于所有项目。

## 九、结语

这个项目让我深刻理解了"Agent = LLM + Harness"的含义。LLM 提供智能，但工程化——治理、反馈、上下文、安全——必须由代码实现。当 LLM 能完成大部分编码时，工程师的价值不在"写代码"，而在"构建可靠的系统"。fixlot 的反馈闭环、护栏、工具分发都是这层工程的具体体现。

(约 2000 字)