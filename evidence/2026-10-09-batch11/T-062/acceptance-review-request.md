# T-062 独立审查输入记录

本记录在审查返回后保存，不补称为当时的独立监控。调用 `collaboration.spawn_agent`，`task_name=t062_acceptance`、`agent_type=acceptance-auditor`、`fork_turns=none`；配置模型 gpt-5.6-luna / max，actual tier 未核验。

输入范围：a2a 固定候选 `45893b7c70b30b2659337875b043795127819686`，fork 固定版本 `d9fc40a5f8b14d22ec7568c7ccef542572e79102`，无产品 diff。依据 T-062 的 What to build、Acceptance、说明，以及 brief；要求只判断浮层遮挡、归因是否支持环境分支、oracle 独立性及已知坏夹具。

明确约束原文：

> 按 behavioral-acceptance-review 做一次 fresh-context、只读独立审查；这是 brief 明确要求的唯一一次审查。禁止修改任何文件、测试、分支、提交、应用或服务；不要再找 reviewer。不要阅读实现 agent 的聊天、RESULTS.md、ticket Resolution 或 issue 正文中的实现理由。

> 仅检查冻结候选，不跟进其他人的并行变动。

提供的核心证据：原 T-055 截图、T-062 的 red03/green03 脚本、JSON、命令与截图、red02 自然结束诊断；要求从产品源码独立核对 Sidebar、既有 Activity 浏览器测试、FeatureTourDialog 和旧 panel-send。另提供失败诊断位置，要求不把 `resume01` exit 0 当作重开业务通过。要求以技能的 STATUS/TARGET/EVIDENCE/FINDINGS/COUNTEREXAMPLE/LIMITATIONS 格式返回，正文中文，不写文件。

返回原文完整保留在 `acceptance-review-raw.txt`。收到 INCOMPLETE 后只整理报告、上报，不改变冻结夹具，不启动第二次审查。
