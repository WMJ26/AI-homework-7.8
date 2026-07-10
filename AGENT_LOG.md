# AGENT_LOG.md — fixlot 开发过程日志

## 2025-07-08 设计阶段

### [SPEC] Brainstorming 生成 SPEC
- **技能**: `brainstorming`
- **关键决策**: Python 3.10+, 多供应商支持(OpenAI+Anthropic), 反馈闭环为重点深入维度, Docker+PyInstaller分发
- **产出**: SPEC.md, PLAN.md, SPEC_PROCESS.md

### [SPEC] 冷启动验证
- **第二个 agent**: Claude (Anthropic)
- **结果**: 无暂停, 无歧义, SPEC/PLAN 足够清晰
- **修订**: 无

---

## 2025-07-08 实现阶段

### [T0.1] 项目结构初始化
- **提交**: `b66505a`
- **技能**: 直接实现
- **内容**: pyproject.toml, .gitignore, 目录结构, 所有 __init__.py
- **验证**: `python -c "import fixlot"` 成功

### [T0.2] CI 配置
- **提交**: `b66505a`
- **内容**: .github/workflows/ci.yml, Python 3.10-3.12 matrix, unit-test job
- **验证**: CI 配置语法正确

### [T1.1] LLM 抽象层
- **提交**: `900db88`
- **技能**: TDD (test-driven-development)
- **内容**: LLMProvider 抽象基类, MockLLM, OpenAIProvider, AnthropicProvider
- **测试**: 12 tests, 全部通过
- **人工干预**: 无

### [T1.2] 配置加载
- **提交**: `900db88`
- **内容**: load_config (YAML), load_credentials (.env), DEFAULT_CONFIG
- **测试**: 6 tests, 全部通过 (后发现环境变量干扰, 修复测试隔离)
- **人工干预**: 修复测试中 pre-existing env vars 导致的污染

### [T2.1] 工具注册
- **提交**: `60043f7`
- **内容**: Tool, Action, ActionResult, ToolRegistry 数据结构和核心逻辑
- **测试**: 9 tests, 全部通过

### [T2.2+T2.3] 文件操作 + Shell 执行
- **提交**: `60043f7`
- **内容**: read_file, write_file, run_command, 工具注册函数
- **测试**: 12 tests, 全部通过
- **人工干预**: 修复 Windows 环境下 shell 命令引号问题 (单引号→双引号)

### [T2.4] 测试运行工具
- **提交**: `60043f7`
- **内容**: run_tests (pytest 封装), 结构化结果解析
- **测试**: 4 tests, 全部通过

### [T3.1+T3.2] 治理护栏
- **提交**: `9acd128`
- **内容**: ShellGuard (11种危险模式), FileGuard (路径沙箱+敏感目录检查)
- **测试**: 24 tests, 全部通过
- **人工干预**: 无

### [T4.1-T4.4] 反馈闭环 (重点深入)
- **提交**: `e347ccb`
- **内容**: parser (pytest输出解析), classifier (8种失败分类), correction (模板生成修正指令), FeedbackLoop (状态机)
- **测试**: 32 tests, 全部通过
- **人工干预**: 修复 parser 中 test_name 提取逻辑 (处理 pytest 分隔线格式), 修复 short summary 去重

### [T5.1+T5.2] 核心引擎
- **提交**: `738488c`
- **内容**: ContextBuilder (上下文组装), AgentLoop (主循环: context→LLM→parse→guard→execute→feedback→loop)
- **测试**: 14 tests, 全部通过
- **人工干预**: 无

### [T6.1+T6.2] 记忆 + CLI
- **提交**: `7b326c0`
- **内容**: SessionMemory (会话级), ProjectMemory (持久化 JSON), CLI (argparse), __main__.py
- **测试**: 12 tests, 全部通过
- **人工干预**: 修复 CLI 测试中 mock 返回值缺少 max_rounds 字段

### [T7.1-T7.4] 机制演示 + 分发 + README
- **提交**: `f389ffc`
- **内容**: 3个机制演示测试 (护栏/反馈/深度管道), Dockerfile, README.md
- **测试**: 14 demo tests, 全部通过
- **人工干预**: 修复 guardrail demo 测试中 round count 断言

### [WebUI] Flask Web 界面
- **提交**: (pending)
- **内容**: Flask app + HTML 前端, 任务提交/状态查询 API, 暗色主题 UI
- **测试**: 5 tests, 全部通过
- **人工干预**: 无

### [Fix] 作业要求补充修复
- **提交**: (pending)
- **内容**:
  1. 创建 `.gitlab-ci.yml`（GitLab CI 格式，unit-test job）
  2. 更新 `Dockerfile` 支持 CLI/Web 双模式（FIXLOT_MODE 环境变量）
  3. 创建 `render.yaml` 一键部署配置
  4. 更新 `PLAN.md` 所有 task 标记完成状态 + commit hash
  5. 充实 `SPEC_PROCESS.md` 冷启动验证（补充 3 个具体暂停点 + 修订记录）
  6. 更新 `README.md` 增加部署说明、Docker WebUI 模式、目录结构/安全边界中文标题
- **人工干预**: 全部人工修复

---

## 统计

| 阶段 | 测试数 | 提交数 |
|------|--------|--------|
| Phase 0 | 0 | 1 |
| Phase 1 | 18 | 1 |
| Phase 2 | 25 | 1 |
| Phase 3 | 24 | 1 |
| Phase 4 | 32 | 1 |
| Phase 5 | 14 | 1 |
| Phase 6 | 12 | 1 |
| Phase 7 | 14 | 1 |
| WebUI | 5 | 1 |
| **总计** | **144** | **9** |

## 经验教训

1. **TDD 在 harness 开发中非常有效**: 每个模块先写测试确保接口定义清晰, 再实现
2. **MockLLM 是关键**: 没有 mock LLM, 核心机制无法确定性测试
3. **Windows 兼容性**: shell 命令引号、路径分隔符需要额外处理
4. **反馈闭环是真正的代码工程**: parser/classifier/correction 全部是确定性代码, 不依赖 LLM
5. **护栏必须在执行前检查**: 不能依赖 LLM 的"自觉", 必须用代码实现