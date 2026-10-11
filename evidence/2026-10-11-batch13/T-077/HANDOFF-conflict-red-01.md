# T-077 冲突流程起点红态（主控 #44 后）

状态：**INCOMPLETE**。已读回 `outside-regression-03-cards/run.json`：PASS，15/0/0/0，`collection_errors=[]`。它与 regression-02 的 coop 8、recovery 9、run 18、cas 1 构成本轮冲突实现前的完整回归；不能用这些结果替尚未实现的冲突流程背书。

本轮只增加冲突测试和外部会话夹具，产品源码保持 cards-03 的版本。按 evidence-first-testing 先取得起点红态，再实现已批准 PLAN 第 5 节。检查仍经真实 CLI → 编排后台 → 门禁 → Git/SQLite，只有原生会话服务由受控边界替代。`conflict_acceptance_host.ts` 从被测 `gate` 路径加载同一版本的 daemon 和原生服务夹具，不能混用候选 daemon 与起点 core。

执行命令：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-sandbox.sh conflict-red-01
```

`prepare_s3_baseline.py` 从已确认的 red-01 归档重建起点，逐文件与 `git show 14b57d22a84bcaebfa91c5051b9909b53a570fac:<路径>` 比对；不切换或修改 checkout。新输出为 `baseline-conflict-red-01.json`、`outside-conflict-red-01/`，遇到已有同名产物拒绝运行。后台使用短 `/tmp` socket、独立进程组；沿用现有生命周期夹具核对并停止自己启动的后台，保存退出和只读状态回执。

## 预先固定的场景与预期

依据：ticket T-077 第 4 项、Acceptance 冲突条款，native-cli spec 第 4 节，以及已批准 PLAN 第 5 节和第 8 节反例表。

| 用例后缀 | 起点应出现的业务红态 | 候选须完成的后续检查 |
| --- | --- | --- |
| `active_worker_reworks_and_integrates` | 未向原 worker 回写；重交 C2 被冻结候选检查拒绝 | 同一原生会话新回合显式重交 C2；只回写一次；新 verifier 跑路径、完成条件、尾注并集成；原 claim base 和 C1/G 记录保留；C2 再次冻结 |
| `ended_session_gets_new_attempt` | 确认停止后仍沿用旧 attempt | 新 attempt/session/thread/fence/worktree；从最新 G 开始；保留旧 C1 隐藏引用；旧身份拒绝；重复旧请求不多建 attempt；新 worker 重交并集成 |
| `unknown_session_preserves_scene_and_reports` | 未上报无法确认原生会话的问题 | 原候选、目录、工作分支均保留；不把未知当 ended；不向未知线程投递；上报绑定原 attempt |
| `unknown_delivery_does_not_resend` | 未执行一次冲突投递 | 夹具在记录一次投递后丢失回执；后续 verify 不盲重发、不换 attempt，保留现场并上报 |
| `merge_command_error_is_not_text_conflict` | 合并退出 73、索引无未合并条目仍返回 `merge_conflict` | 保留原始命令失败与退出码，返回 `git_failed`；不启动冲突整理 |
| `rework_still_rejects_forbidden_path` | C2 无法通过重交入口 | 合法重交后，worker 自己新增的 `src/private/secret.txt` 必须被路径检查拒绝，完成条件不运行 |
| `rework_still_rejects_foreign_trailer` | C2 无法通过重交入口 | 合法重交后，C2 自己带的其他任务尾注必须被拒绝；不能因为有重整基线就跳过尾注检查 |

七个案例的合并输入都由独立夹具预先固定：C1 把单行 JSON 的 worker 改为 ready；G 把同一行的 host 改为 ready，并修改当前卡不允许写的 `host.txt`，带其他任务尾注。完成条件要求两个值都为 ready，且 `host.txt` 保持 G 的准确内容。测试不从产品输出生成答案，不以正则或关键词判断消息含义。完整回写文本留在 `gate-feedback.jsonl`，由后续真实 worker 的整理和独立 oracle 检查其可用性。

最后两项在起点首先证明“冲突后可重交”的入口缺失；起点不会运行到后续路径/尾注拒绝断言。不能把这次红态声称为那两条拒绝断言各自已通过反事实验证。候选上必须实际走完后续拒绝；原有路径/尾注反例也继续保留。未知投递的“不重发”同理：须等候选实际发生一次投递后检查，起点只证明没有投递。

## 边界与后续

本轮不运行真实 Codex、不创建隔离 home、不复制 auth、不安装 hook，真实用量保持 **0/4**。新 host 只提供拟接入的 `sendGateFeedback(thread, messageId, message)` 外部边界，并记录每一次调用；它不修改生产 SQLite，不替门禁改变 candidate、attempt 或 verification，不在夹具里自动去重投递。整理动作由测试模拟 worker 在其自建 worktree 上执行，不能算真实模型场景。

冲突产品实现、候选绿态、原生 Codex 冲突场景、独立审查和变基后验收均未完成。真实启动前按主控 #44 另交准确 argv、隔离 home 和逐项 hook 清单；目前的占位 argv 不作启动授权。T-076-2 的审查生产与判定仍由其负责，本卡只通过唯一 `verifyCandidate` 衔接；本轮不声称证明审查会话行为。

静态准备检查的重放命令：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/check-conflict-preparation.py --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/conflict-preparation-02.json
```

首次检查写入 `conflict-preparation-01.json`；重放使用新的输出名。静态准备通过只表示语法、范围和版本绑定可检查，业务红态仍待主控在沙箱外运行。
