# T-081 能力检查首轮运行交接（主控 #169）

状态：INCOMPLETE，脚本已准备，真实回合尚未运行。批准引用固定为 `T-081 controller-decision-01 capability-turn-1`；本轮只准备交给主控的脚本，未执行已批准的启动步骤。第 7 项首轮上限 1，不自动追加输入或重试；home cleanup 另批。

## 主控依次执行

第一步沿用已审的 home 脚本，仅复制 auth.json 并生成最小信任配置与 git add/commit 两条 allow 规则：

```sh
python3 -B workbench/tests/t081_capability_home.py prepare --approval-ref 'T-081 controller-decision-01 capability-turn-1' --receipt evidence/2026-10-14-batch14/T-081/home-prepared-01.json
```

第二步在沙箱外一次运行：

```sh
python3 -B workbench/tests/run_t081_capability_turn.py --approval-ref 'T-081 controller-decision-01 capability-turn-1' --output evidence/2026-10-14-batch14/T-081/capability-run-01 --turn-timeout 600
```

输出或 reservation/state 已存在即拒绝，不接管、不重试。本脚本不生成 home、不删除 home、不提交代码、不 submit、不验收或集成任务。实际失败保留现场，不能再次执行本次批准来补跑。

## 执行路径与边界

- 核对 home prepare 收据、目录与文件权限、精确 config/rules、空 sessions；核对固定夹具 G/T、空裸仓库引用、无真实 remote/原 hook，核对已批准源码归档和角色卡。
- 将 #169 的批准引用写入本次启动配置。通过原产品 CLI 的 `daemon_start` 创建真正的隔离后台，保存 PID/PGID/SID；后台脱离调用进程组。
- 标准产品入口验证/保存任务卡、创建任务，再用 `dispatch` 原子认领并创建窗格。不会先 claim 再重复 dispatch。产品生成的首轮正文必须与已审 FIRST-TURN 模板按实际 UUID 展开后完全一致。
- 测试预加载模块 [t081_capability_audit.ts](../../../workbench/tests/t081_capability_audit.ts) 仅在后台截获真实 node-pty spawn；核对完整 argv、zsh argv、home、Git hook 环境、模型/强度/default tier 和 1 回合上限，匹配后调用原生 spawn。没有替换进程观察或门禁结果。NODE_OPTIONS 审计环境不会传入 worker。
- 确认真实 Codex 前台领导进程后才用 `pane_release` 放行首轮。等待期限 600 秒，首次启动就绪期限 30 秒；CLI 调用另有 40 秒上限。超时走正常 daemon_stop，停止后确认已记录 PID 与端点退出的期限 20 秒；不额外输入、不重试、不强杀未知进程。
- 只认绑定本 attempt/launch/native session 的一次回合提交、一条 Stop/idle 和一次根会话 task_complete。读回 probe-results.json、真实工具调用与工具回执、共享仓库/本地裸仓库 refs、任务与事件。模型写的 probe-results 只作产物，不能替代原生工具回执或独立 Git 引用读回。

## 主要输出

`capability-run-01/` 保存：launch-before-spawn.json、spawned.json、first-turn-before-queue.json、attempt.json、launch-record.json、before-release.json、turn-completed.json、probe-results.json、refs-and-task.json、final-refs.json、原始 native-root.jsonl 与 actual-command-results.json、原始 PTY trace、命令输出、正常停止后的 SQLite 副本和 PID 退出记录。

真实终端工具格式优先按实际原生记录读取；如不能把两条命令各一次的工具调用与结构化退出状态对应，原文仍保留，结果写 INCOMPLETE，不能用模型自报或推断退出码补齐。拒绝执行、命令失败和本地引用被改变均按实际结果记录，不能把“门禁不放行”当作 worker 没有能力。

正常观察结束仅可记本回合 PASS；product_status 仍为 INCOMPLETE，CAS 补充、6a/6e 裁定和 home cleanup 未完成。脚本把完整已观察 PID 列表写 `/private/tmp/t081-capability-01/owned-pids.json`，保留 home 等主控另批清理。未确认退出、超大文件或未知 daemon 启动结果均不自动接管或删除。

## 已做的局部检查

`capability-script-check-01/` 只验证启动审计：关闭 spawn 前拒绝的变异体会错误调用 PTY spy，产生业务断言红态；正常策略通过，错误 tier 在当前审计中被挡在 spawn 前。该检查没有创建真实 PTY、读取 auth 或运行模型。另用既有真实原生记录验证工具回执格式；旧记录不替本次实际结果背书。

全部已审提示词、argv、hook 与隔离 home 路径仍见 [审批包](CAPABILITY-REVIEW.md)。运行脚本本身尚未调用真实 Codex，不把静态/spy 检查记成第 7 项能力结论。
