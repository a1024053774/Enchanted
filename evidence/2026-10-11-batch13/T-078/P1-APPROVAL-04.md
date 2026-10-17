# P1 材料 04：引导预置的文档缺口与 cleanup 修复

**BLOCKED。** 已生成新的材料 04 和实例，但不声称四项引导状态都已预置；launch/continue 阶段在任何启动前明确阻止执行，等待 issue `20261013T154915Z-worker:s13-t078s-issue-001` 的范围决定。没有自动按 Enter、选默认、登录、换 CLI 或更改用户配置。

## 引导状态：逐项来源

| 项 | 已核对的来源与可用程度 |
| --- | --- |
| 主题 | [官方 theme](https://code.claude.com/docs/en/settings-reference#theme) 文档允许 settings.json 中设置 `theme: dark`；旧 .claude.json 的主题仅在未设 settings 时生效。可只写本实例的 claude/settings.json，尚未写入 |
| onboarding | [官方环境变量](https://code.claude.com/docs/en/env-vars) 明确 `IS_DEMO=1` 跳过 onboarding，同时隐藏用户／组织信息；这是文档化变量，不是猜测 hasCompletedOnboarding。可只放入本实例环境，尚未加入启动材料 |
| 假 key 确认 | [官方认证](https://code.claude.com/docs/en/authentication#authentication-precedence) 明确交互模式首次使用 ANTHROPIC_API_KEY 需要批准，但未找到公开的非交互预置格式。不能把 customApiKeyResponses 问题报告当作固定 2.1.296 的文档化契约；未写内部状态 |
| 夹具 repo 信任 | [官方设置](https://code.claude.com/docs/en/settings#find-or-create-your-settings-files) 说明 .claude.json 由 CLI 维护项目信任状态；完整公开参考未列 projects[repo].hasTrustDialogAccepted 的预置契约。问题报告只能作为内部实现线索，未写该字段 |

通过公开 HTTP 只读下载的 settings-reference/env-vars 原件在 p1-onboarding-research-04；没有读取用户 ~/.claude 或凭据。材料 03 归档内的隔离 claude/.claude.json 没有主题、完成引导、key 批准或项目状态字段，不能凭它制造完整预置。

本轮未知的是后两项的文档化写法，以及 IS_DEMO 对固定 CLI 的实际作用；没有执行新 CLI 探针。最小选项见 p1-bootstrap-question-04.md：批准仅用已文档化机制再观察并在 key/trust 提示停止，或明确授权只读核对固定 CLI 的内部格式、把其隔离预置标为版本绑定实现依据。当前不自行选择、不使用 --bare 或其他认证路线。

## cleanup 修复

原真实红态来自主控 #89：cleanup 报 PASS 时 CLI PID 16681 仍存活，随后自行退出。原 result、fixture 和该观察记录均保留，不把最后无残留改写成当时正确退出。

新的 runner 在 CLI 启动后，按生产 pane_process_info 绑定本次 CLI，再用只读 ps 记录 PID、启动时间和命令，保存 `launch/process-manifest.json`，关联 launch/session/shell PID。未核对到 CLI 就停止，不能用假 PID 填表。

cleanup 判定是否有启动尝试及进程 manifest，先让后台停止自己的 PTY。daemon.pid 消失后再按记录 PID 观察，最多等 15 秒；只有明确 ps 无该进程才继续归档和删根。仍存活、PID 身份变化、缺 manifest、ps 错误或无法核对退出都返回 BLOCKED，并保留实例。没有加 SIGKILL、额外 CLI kill 或兜底重试。API 保留原有 PID/命令核对；不发信号给未知进程。

`p1-cleanup-static-final-04` 用主控给出的独立 lifetime 条件验证 CLI 活着时 BLOCKED、退出才 PASS、身份变化／记录缺失不能通过；重现旧只看 daemon 的坏规则。它没有调用 ps、发送信号或启动进程，不替代下一次真实 cleanup 复验。

## 材料和新停点

`p1-materials-04/approval.json` 是只生成、未运行的模板，含新 root/launch/session、完整原 argv/env/hooks；源码、控制端参数、生成命令也在同目录。该模板尚未加入待决定的初始化配置，**不能审批为可完成引导的启动**。

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-launch-04
```

当前该命令只报告 BLOCKED，退出 2，不启动 API/CLI。continue 同样被阻止。只有决定后改材料并重新审批才能放行；仍用隔离 HOME/CLAUDE_CONFIG_DIR、公开假 key，不碰用户配置。合流和真实 Haiku 复核都没有开始。

纯检查重放：`python3 -B workbench/tests/test_t078_p1_cleanup.py --output <新目录>`；新的模板生成必须用 `python3 -B workbench/tests/regenerate_t078_p1.py --label p1-materials-05`，不能覆盖 04 或先前失败。
