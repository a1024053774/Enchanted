# 静态检查与未运行部分

本轮只执行 AST/JSON/路径/纯数据协议重放与提交脚本 --check-only；它们不能证明真实窗口或 HTTP 时序。红态基于冻结父版本的多根历史验证器；绿态覆盖完整 4/6 与 6/11 累积会话历史，工具结果用排队回执的真实形状；Bash schema 来源 A11 实际 Claude tools。反例为错误 tool ID、重复当前 tool_result、正文/seq/身份/角色、真实请求预算超限，以及实际 gate 反馈关联。

A11–A13 缺陷逐项：input.command（安全 argv 拼接）；permission 一次 awaited window.a2a.input 回执且 control action；slot/输出每次唯一；嵌套输出先建父目录；B1 screen plan security-notice+screen_text 与 P1 key onboarding-notice 分开；旧屏新 -02 重读；批准模板字段完整/签字空；签字件不改；成功 B1 label 显式绑定；API 从阶段 A 即加载最终 phase-plan/profile；role-local hooks 与已审 hookTrace 路径一致；dispatch 只去尾部 CR/LF，中间差异仍拒；Stop 异步排队不要求 tool_result 同步 entry；pending 零反馈，实际 delivered 后原 I2；created_at 不重置；提交前模拟所有现有/将生成路径均被两次 git add 覆盖，结果不在最后提交后追加。

需要主控在审阅后沙箱外另跑的新 HTTP/进程检查（本轮 NOT_RUN）：

- python3 -B workbench/tests/test_t078_09b_fake_api_http.py --output evidence/2026-10-11-batch13/T-078/09b-a14-http-01
- python3 -B workbench/tests/test_t078_09b_fake_api_http_claude.py --output evidence/2026-10-11-batch13/T-078/09b-a14-http-claude-01

上述检查只覆盖共享 HTTP core，不是新的 phase-plan DB/批准等待/Electron 完整入口证明；本轮全部真实阶段均 NO_GO。请先审新 phase-plan 驱动，再决定是否要在 A14 之前增加无 Claude 排练。
