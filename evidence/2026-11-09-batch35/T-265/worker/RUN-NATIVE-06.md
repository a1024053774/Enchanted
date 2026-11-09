# T-265 第六轮外部验证：先关闭自有 PTY，再确认回收

INCOMPLETE。候选“短入口 → 原生完整读取 → 材料只读 → 回合结束”已由主控独立核对为 PASS，见主仓库 controller 的 `native-candidate-05-behavior.json`。native-04 整轮及 candidate-05 原始结果仍因 PTY 退出清理 INCOMPLETE；本轮待验证原父版与候选均完成业务检查、同一 Popen 确认退出并清理夹具。原始结果不改写。

人工介入记录：主控经工作台正常输入继续，要求完整读取 `native-05-feedback.txt`，只调整测试 finally 的自有 PTY 关闭/回收顺序。worker 已读完该文件并核对 `process-wait-probe-02-events.jsonl` 与候选独立行为结果；未运行原生 CLI、ps 或信号，未操作主控夹具。按本轮要求不再创建 issue。

主控核对最终脚本后执行这一条命令，脚本使用绝对路径，无须依赖当前目录：

```sh
/usr/bin/python3 -B '/Users/luckye/Library/Application Support/a2a-orchestrator/worktrees/a2a/T-265-1-a1/workbench/tests/test_t265_review_cli_e2e.py' --codex /Users/luckye/.local/bin/codex --node /opt/homebrew/Cellar/node/26.5.0/bin/node --summary /Users/luckye/Documents/Code/a2a/evidence/2026-11-09-batch35/T-265/controller/native-cli-06.json
```

输出为 `native-cli-06.json` 和 `native-cli-06-artifacts/`，均在主仓库 `evidence/2026-11-09-batch35/T-265/controller/`。检查时这两个路径尚不存在；脚本要求新路径，拒绝覆盖。继续使用交互 Codex、gpt-6-astra、xhigh、default、`-a never`、workspace-write、空 writable_roots，无 hooks/MCP；每 case 240 秒，不自动重试。隔离 CODEX_HOME 仍在 `/private/tmp`，只复制 auth.json，不改全局配置。

直接原因证据来自主控的窄探针：PID 25165 在 TERM 三秒后 getpgid=ESRCH、Popen.poll=None，但 ps 仍见该 PID、父 PID 25157、PGID 25165 和 `?Es (codex)`；关闭该测试自有 master 后，同一 Popen.wait 返回 -15。该探针只跑父版，证明这一次退出时序受持有的 master 影响，不是业务验收，也不证明所有 ESRCH 都已退出。probe-01 的偶然快速回收不覆盖 native-04/05 的失败。

本轮只改 `interact` 的 finally：先 flush/fsync 终端并保存原生事件；取出本次 master、将 fd 清空，再关闭一次；成功时记录 `pty_master_closed=true` 和 `pty-master-closed` 阶段；之后调用原有 `stop_owned`。关闭失败保存 diagnostic_errors，结果继续 INCOMPLETE，原交互异常不被替换。原有 PID/PGID、EPERM、poll/wait 身份和退出证据约束保持原样，ESRCH 本身不能代表清理完成。

新增一个离线顺序检查方法，覆盖 EOF、期限到达、交互异常伴清理 EPERM、master 关闭失败四个场景，要求诊断先保存、仅关闭各自创建的描述符一次、master 先于回收释放。所有 PTY/Popen/进程操作均 mock，临时目录自动清理：

- `pty-order-red-06.txt`：修改前四个场景全部在顺序断言失败。
- `pty-order-native04-counterfactual-06.txt`：同一断言在 native-04 冻结脚本上四个场景全部失败。
- `driver-green-pty-order-06.txt`：11 个检查方法通过，包含原诊断、onboarding、身份与退出竞态检查。
- `driver-scope-06.json`：产品逐字节相同；驱动除 interact.finally 外的 AST 全部相同；没有自有 mock 夹具残留。

这些离线检查证明修正的顺序与错误报告，不能代替真实 PTY 回收。主控下一轮仍运行原 `case` 业务断言：父版必须实际投递、被原生上限拒绝且没有启动回合；候选必须从短入口执行原 probe、读出全部输入计数与随机标记、材料写入被拒绝并结束回合。两 case 回收成功且夹具删除后整轮才能 PASS。清理失败继续保留原终端、原生事件、过程记录和失败夹具；未确认退出时不删除相应 CODEX_HOME。

本轮没有额外目录改动。README stale 仍由主控在集成点处理。收到完整真实结果后再补最终报告、Git 提交与显式 submit；本轮交接不宣称已完成这些步骤。
