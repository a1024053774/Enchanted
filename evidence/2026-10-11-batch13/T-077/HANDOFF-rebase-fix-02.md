# T-077 shutdown 夹具修正（主控 #58）

状态：**INCOMPLETE**。rebase-01 的 S3 25 项、8/9/18、CAS、cards、Panes 4 项、原生末尾日志、派发状态和 identity 4 项均已通过；shutdown 为 4 项中的 1 error，原输出不改写，整体不补记 PASS。

## 真实依据与根因

已从 T-076-1 的 `outside-real-04` 读回真实启动记录、原始 native 轨迹归档和编排事件，三个来源绑定同一个 launch `b1041c2a-795f-4aeb-9570-571308c4e50f`、根会话 `01a12ba0-0467-7c00-8c86-e7871e8ae65c`：

- `launch-record.json`：`cli_version=codex-cli 0.162.1`，`-C` 与 worktree 均为 `/private/tmp/t76-real-ulse52um/state/worktrees/a0842017-9355-4e8a-bc6b-aa6b9b6628d1`。
- `fixture-artifacts.tar.gz` 内 `state/traces/b1041c2a-795f-4aeb-9570-571308c4e50f/native.jsonl` 首行：`session_meta.payload.cli_version=0.162.1`、`source=cli`，`cwd` 与上述路径完全相等。
- `orchestration-events.json` 的 seq 70：同一根 rollout 的 offset 0 记录，与归档首行解析后的整个对象相等。

本卡失败归档中的合成记录只有 `id` 和 `source`，确实没有 cwd。首次输入已发生（`turn_submit_intent=1`），但 `native_record=0`，所以运行一直未绑定原生身份。之后的 `fixture_runtime_failure` 是测试超时清理主动注入的标记，不是原始失败原因。产品按工作目录过滤该不完整合成记录，符合本次固定版本的真实数据。

读取和断言脚本为 `prove-rollout-cwd.py`，结果 [rollout-cwd-proof-01.json](rollout-cwd-proof-01.json) 的九项核对均通过。重放使用新文件名：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/prove-rollout-cwd.py --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/rollout-cwd-proof-02.json
```

## 修正与复验

只改 `workbench/tests/startup_shutdown_host.ts` 两处：PTY stub 接收原 spawn 的 `options`，合成 `session_meta` 增加 `cwd: options.cwd`。数据来自实际请求的工作目录，没有从待验证的身份结果反推。`test_startup_shutdown_e2e.py` 及其全部断言未改，产品源码和原生身份检查与 `446f25c3` 完全一致。

范围审计只放行上述两处精确替换；把 cwd 改为 control 目录的反例仍须拒绝。没有扩展业务断言白名单，也没有增加重试或忽略未知原生记录。

本次只执行主控指定的三组，全部用新输出：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-sandbox.sh rebase-fix-02
```

顺序为 shutdown 4 项 → identity 4 项 → Panes 4 项。结果、前后版本核对、实际夹具 diff 和源码快照保存在 `outside-rebase-fix-02/`，最终回执为其中的 `run.json`。先前通过的组不重复运行；原 `outside-rebase-01-shutdown` 继续保持 INCOMPLETE，不补写旧汇总。

当前只完成只读诊断、夹具修正、语法与范围检查，新绿态待主控运行。真实用量保持 **0/4**；本次读取既有真实归档，不新增 CLI 或模型会话。真实冲突整理、复用 home 的历史根记录隔离和独立审查仍在后续阶段。
