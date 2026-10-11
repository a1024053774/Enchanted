# T-077 冲突候选绿态交接（主控 #47）

状态：**INCOMPLETE**。conflict-red-01 已逐项读回：7 项全部业务红态，active 用例 3 failures，其余各 1，0 errors、无真实回合。失败证据原样保留。现在的候选增加了冲突处理，之前 8/9/18/CAS/cards 的通过结果不能替这个新版本背书。

执行命令：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-sandbox.sh conflict-green-01
```

输出目录为 `outside-conflict-green-01/`，已存在则拒绝。先跑 red-01 的同一七项 CLI 场景，期望 7 项全通过、0 failures/errors/skipped；随后复验两份受影响的旧窗格探针，分别输出 `outside-conflict-native-final-01/`、`outside-conflict-dispatch-state-01/`。未执行，不预填 PASS。不启动真实 Codex，不安装 hook，不重复已有整套回归。后台启动、核对、退出和收证据沿用受控生命周期夹具。

## 本次实现

- `core.ts` 以合并退出 1 和非空 unmerged 索引确认冲突；无冲突条目的 Git 错误仍返回 `git_failed`。保存原始输出、冲突文件/阶段/差异，并用 verifier 序号下的 `-candidate`、`-base` 引用保留 C/G；不存在 M，也不生成验收通过记录。
- 在原操作锁内持久化 `rework` 意图后观察会话。原 worker 可确认时经 `sendGateFeedback` 回写；忙时走原队列。确认投递后只解除这一次交付回合的绑定，attempt/session/fence/card 保持；新 C 重交后重新冻结并运行同一 `verifyCandidate`。未知投递不自动重发。
- 确认会话结束后先核对停止/归档，再回收旧 attempt，经提取后的唯一 `claim` 实现从当前 G 创建新 attempt。新 claim 重新检查所有活跃路径占用，不偷用旧并行理由。旧 run 仍持有原 attempt；冲突请求以失败/待处理返回，不替它接管新 worker。
- 重交基线只从门禁读取的工作分支头取得，须是已观察 G 的后代、也是 C 的祖先。原 claim base 不变。路径和尾注只排除已集成历史，继续检查 worker 新增内容与 G→M；新 C 清除 R8 连续计数，保存 `review_required: fresh` 的候选/合同/身份绑定。该事件是给 T-076-2 的衔接事实，不是审查通过结论。
- 完整冲突证据先保存，确认反馈或结束后再核对临时 verifier 未变化，撤销其中的临时合并并普通删除目录；不修改 worker 工作区或工作分支，不强删未知现场。
- `panes.ts` 复用原队列和 gate 来源；只有 stopped+archived 的旧 pane 释放名额，按 rollout 的工作目录隔离不同 attempt。已知原生领导进程退出且只剩原 shell、上一回合空闲时记录结束；辅助进程、替换进程和不明状态不能冒充正常结束。

没有改旧验收断言、存储表结构、daemon、scripts、spec 或地图。新增 JSON 字段沿用现有记录存储。README 同步描述当前行为。

静态检查发现旧 `test_native_final_read.ts:25` 和 `test_pane_dispatch_state.ts:48` 的合成 `session_meta` 缺少所属工作目录。按任务卡“探针或测试本身的错误可以直接修，但要记录”，仅给两处元数据加 `cwd: root`，没有改业务断言或期望值。范围审计单独核对这两处精确替换，任何额外编辑仍拒绝；新增两个反例证明“补元数据时顺带反转原断言”会被审计拒绝。这不是扩大 W01～W16 的业务断言白名单。

## 已运行与未运行

Panes 的四项检查有独立起点红态和候选绿态：`panes-conflict-red-01.json`、`panes-conflict-green-01.json`。它们使用生产 Panes/Store，替换外部 ps 返回和 PTY 对象；没有启动真实进程，因此不能证明真实原生会话或终端可用。故障方式、准确命令见 [PANES-BOUNDARY.md](PANES-BOUNDARY.md)。临时夹具和源码随 `conflict-implementation-01/` 保存。

静态核对与证据打包命令：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/check-conflict-implementation.py --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/conflict-implementation-02
```

首次输出为 `conflict-implementation-01/`；重放使用新目录。脚本保存 Node 语法、shell 语法、断言范围、地图状态、冻结起点绑定、Panes 红绿回执及原始夹具归档；不运行 CLI 业务场景。

当前分支仍从 `14b57d22` 开始，尚未合入 T-076-1 的稳定原生身份与后台停止改动。当前脚本只检验冲突流程的受控原生边界；真实多回合场景前须接上主控指定的 T-076-1 身份语义，不能用这些受控结果替代它。最终合流仍逐处保留双方行为，并重跑完成条件与 8/9/18。

真实用量 **0/4**。真实冲突场景的准确 argv、隔离 home、三个 Codex hook 和 Git 尾注 hook 会另交逐次批准；本脚本没有真实启动入口。独立审查和最终交付均未完成。
