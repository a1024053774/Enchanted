# T-077：real-02 诊断与 relay 修复待后台复验

2026-10-11，回应主控 #66。**INCOMPLETE**：定点红/绿、原 relay 回归与三个变异体已完成；新的受控后台复验待主控执行。真实场景仍未通过，预算 **4/4**，本轮新增真实回合 **0**。

## 1. 根因与规范依据

修复前 `workbench/src/relay.ts` 以 `id:<request_id>` 为主键查找 `relay_requests`。该表属于整个 state 数据库，既不按 task，也不按 attempt/launch 分区。找到旧记录后，launch 不同就返回 `relay_request_id_reused`，发生在登记新 intent、调用 submit 门禁之前。`relay-scope-red-01/relay-preimage.ts` 与起点 `14b57d22a84bcaebfa91c5051b9909b53a570fac`、真实运行候选 `93094e7be82c21448c460436c360ffb0f75a3412` 的 relay 源码逐字节相同，核对见同目录 `preimage.json`。

规范没有直接规定 SQL key 的拼法，也没有找到“request_id 必须跨 attempt 或整个 state 唯一”的要求。判断依据是：

- `managed-delivery-2026-10-06.md` “CLI contract v1”中的 submit 契约（第 34～39 行）：同身份、同 commit 的重交可幂等；身份包含 attempt/session/fence/spec。
- `native-cli-orchestration-2026-10-10.md` 第 3 节第 1、3 步及第 4 节：新 attempt 有新身份，结束后的冲突 worker 应换新 attempt 并显式重交。
- T-075 Resolution 第 118、131 行：B 通道为每 attempt 配独立请求目录。修复前 README 第 216 行只写编号去重，没有提出跨 attempt 唯一约束。
- 主控 #66 明确指定“新 attempt 用与旧 attempt 相同的 request_id 显式交付”作为应接受的受控场景。

据此把缺陷归在产品的 state 全局去重作用域；不修改原真实任务卡的 `--request-id delivery` 来绕过它。

## 2. 真实归档的身份与失败证据

只读提取见 `real-relay-diagnosis-01.json`，七项检查 PASS。原始来源为 `real-conflict-01/attempt-2/events-before-stop.json`、结束后的 SQLite 快照、`fixture-artifacts.tar.gz`，以及 attempt 1 的原始 rollout。

| 事实 | 原始观察 |
| --- | --- |
| a1 原生身份 | launch `9906fa57-4877-48f9-afb4-c1aceef3edd4`，native `01a12cb4-2907-79c0-8198-4b5aadd226bd`；metadata 事件 39，cwd 为 a1 工作目录 |
| a2 原生身份 | launch `7cb79cbe-a73d-49ce-836a-c43d23f1572c`，native `01a12cb5-bd2d-7a30-9641-e83b614bb306`；metadata 事件 386，cwd 为 a2 工作目录 |
| a2 Stop 已匹配自己的原生会话 | 事件 729、762 的 session_id 均为 a2 UUID；随后有 pane_idle 732、764 |
| 历史日志保留 | 最后归档中的旧 rollout 与 a1 保存的 279,082 字节原文完全一致；新 rollout 为另一个文件，共 226,302 字节 |
| 请求有不同身份 | 两份请求均为 `delivery`，a2 有新 attempt/session、fence 2、C2 `2b3171f00611f6d70bf8a17039e111d8f14e3537` |
| 拒收发生在门禁之前 | 事件 730、763 均为 key `id:delivery` 的 `relay_request_id_reused`；库中只有 a1 relay intent/result，没有 a2 submitted 事件 |

两次拒收来自工作回合和回执回合的 Stop 重读同一请求文件，不能据此称 worker 显式提交了两次。

`daemon.ts:86–98` 只有在 relay 调用 `perform` 后才建立 gate caller、执行 submit；`gates/core.ts:2814–2816` 在 submit 路径补绑定已观察到的 native，成功后在第 2890 行保存。手动 dispatch 不走自动 run 的持续身份观察。上述提前拒收与 task 仍 claimed、candidate 为 null、a2 持久化 native_session 为 null 一致。已有 rollout/Stop 证据支持历史记录隔离成功；尚未执行的真实门禁交付不能补称成功。修复后的绑定、验收与集成由下述受控后台场景进一步验证。

## 3. 修复和已取得的证据

产品只改 `workbench/src/relay.ts` 的 lookup/key 生成：有合法编号时按持久化的 `launch + request_id` 查 intent，已有记录沿用其原 key；新记录用 `id:<launch>:<request_id>`。不改表、追加约束、Stop 匹配、身份检查或未知结果处理。旧格式的完成结果仍直接返回，旧 pending intent 仍为 `relay_outcome_unknown`，不会因换 key 再执行。README 明确了作用域。

| 检查 | 结果与产物 |
| --- | --- |
| 修复前定点信号 | `relay-scope-red-01/run.json`：2 个业务断言失败、0 夹具异常；同 attempt 重放等 3 个控制通过 |
| 同一测试候选绿态 | `relay-scope-green-01/run.json`：5 项 PASS；测试字节与红态相同，候选源码归档在 `sources.tar.gz` |
| 既有 relay 核心 | `relay-core-green-01/results.json`：failure=null；保留错身份、坏请求、旧 Stop、重放、pending intent、追加约束检查 |
| 既有 CLI 请求写入 | `relay-cli-green-01/results.json`：PASS，submit/status/issue 均通过 |
| 全库去重变异体 | `relay-mutants-02/global-lookup/run.json`：跨 attempt、跨任务两项断言失败，0 异常 |
| 重放重复执行变异体 | `relay-mutants-02/duplicate-effect/run.json`：3 项业务失败，包括同 launch 的 gate effect 次数，0 异常 |
| 遗忘旧 intent 变异体 | `relay-mutants-02/forget-persisted-intent/run.json`：旧结果/pending intent 控制失败，0 异常 |
| 准备检查 | `relay-preparation-01.json`：TS/Python/shell 语法、diff 空白检查 PASS；不等于后台验收 |

单测只隔离了 gate effect 回调，使用真实 RequestRelay 与 SQLite，便于检出重复执行和旧 pending intent 被遗忘的错误。完整调用链另行交主控运行，不以这些定点结果冒充端到端通过。变异体在独立 `/tmp` 源码副本运行，三个都被检出；未改候选来制造失败。第一次变异体 runner 把证据目录向上多取一层，尚未执行产品就报错；原输出留在 `relay-mutants-01/runner-error.txt`，只修路径，新输出改为 `relay-mutants-02`，不算业务红态。

## 4. 交主控执行的步骤

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-sandbox.sh relay-check-01
```

产物：`outside-relay-check-01/`。先用当前产品、仅把 relay 还原成已确认的修复前原文，再跑当前候选；副本逐文件核对，只允许 relay 不同。红态必须在“a2 新请求应 submitted”的业务断言处失败、0 errors；随后候选须通过所有断言。任一步不符即停，旧输出不覆盖。

该场景经真实 CLI 写请求文件、CLI signal、Unix socket、daemon、Panes、RequestRelay、门禁、Git 和 SQLite。只模拟 PTY 回调及进程观察；version-only 程序不启动 Codex、不读取认证。合成 rollout 带真实 spawn options.cwd；同一个合成 home 保留两个 attempt 的日志。旧 worker 显式交付后结束，主线发生同一行 Git 冲突，由生产门禁创建新 attempt，新 attempt 仍用 `delivery` 重交。每次将同一请求复制为第二个文件，在同一个有效 Stop 中转交，再重复一个回执 Stop，检查没有重复 gate effect。预期新 C2 入库、正确 native 持久化、旧日志不变、重新验收并集成，最终隐藏引用可读。

受控夹具会创建自己的 detached 后台、Unix socket 和 `/tmp` 仓库；只停止自建后台，证据归档后保留现场。由于任务卡规定这些操作由执行主控在沙箱外运行，本 worker 在 READY 后停下。**不会调用 real-01/real-02，不消耗新真实回合。** 没有重新申请权限、没有写全局配置、没有改主 checkout。

## 5. 重现命令与限制

以下命令中的新输出路径不得已存在。修复前源码已保存，完整调用链的修复前/候选组合由第 4 节脚本重新生成。

```sh
python3 -B evidence/2026-10-11-batch13/T-077/diagnose-real-relay.py --output /tmp/t077-diagnosis-replay.json
node workbench/tests/test_relay_scope.ts /Users/luckye/Documents/Code/a2a-wt-t077/workbench/src/relay.ts /tmp/t077-relay-scope-replay
node workbench/tests/test_relay_core.ts /tmp/t077-relay-core-replay
python3 -B workbench/tests/test_relay_cli.py --output /tmp/t077-relay-cli-replay
python3 -B evidence/2026-10-11-batch13/T-077/check-relay-mutants.py --output /tmp/t077-relay-mutants-replay
```

命令工作目录均为本 worker worktree。诊断 PASS 只表示证据相符；真实冲突端到端仍为 **INCOMPLETE**，4/4 预算已用完，不能原地继续或追加真实回合。新的真实预算与启动由主控另行请用户决定；独立审查、最终变基和交付尚未完成。本次 relay 改动后的全量回归也未宣称通过。
