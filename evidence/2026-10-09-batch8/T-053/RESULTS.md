# T-053 收件箱脚本交付

**PASS（worker 实现与端到端验证）；ticket 保持 open，待主控关闭。**

执行依据：T-053 `ready_rev: 1`，任务书 `brief-T-053.md`，controller-split-user-input spec 第 2～5、8 节。代码提交：`a4d502407e5d593300f84b2b82f899d0624f0949`（含首刀 `251ce27694d28aef54079ab8c1bc691e7d5a4b0b`）。fork 提交：none。没有修改角色卡参数名或内容。

`scripts/inbox` 使用 Python 3 标准库，提供 send/list/ack/ready。条目先以 O_EXCL 写到 `.project-map/.inbox-staging/` 并 fsync，再用原子、拒绝覆盖的 hard link 发布为 inbox 下的 md。正文不解析；确认、处置、答复均追加新条目。

## 验收

| 条件 | 结果与证据 |
| --- | --- |
| 红态在先 | PASS；`red-01` 因入口不存在失败，exit 1，原输出与 argv 已保留。属于新行为契约红态。 |
| 20 进程同秒 send | PASS；固定同一 UTC 秒，20 个完整文件、20 个不同 id，正文集合无丢失；最终套件。 |
| 写入中途被杀 | PASS；只在测试子进程的真实 os.write 边界注入短写，写下 17 字节后 SIGKILL；保留 tmp，inbox 无半截 md，后续发送正常。此证据证明进程中断，不宣称断电恢复。 |
| 未确认清单 | PASS；手写预期 b,d / e，与真实 list 逐条一致；非收件人 ack 不生效，命令拒绝伪造 ack；确认后原字节不变，重复确认无副作用；悬空回复链逐条报错。 |
| 只追加与路径 | PASS；重复 id 退出 1，原文件不变；无 edit/delete；缺失引用/正文、路径穿越、symlink 越界、非 UTF-8 正文均拒绝且不留条目。 |
| 问题派生状态 | PASS；注入时钟覆盖待判断/等你决定、blocking、close/dismiss/forward/snooze/reopen/needs-user、answer/delivered；15 分钟、1 小时只在各自常量定义一次。 |
| ready | PASS；14 个独立夹具，正常 build/task/research 和 closed/superseded 依赖可执行，其余按契约排除；缺字段列不合规。 |
| 角色卡与提醒 | PASS；缺 ideation/executor 卡退出 1；无副本记录不提醒，超过 7 天提醒，新记录消除提醒。user 是呈现角色，不要求不存在的 user 卡，只列等你决定的问题。 |
| 真实项目只读 | PASS；ready 与三个角色的 list 前后 Git 状态完全一致、地图文件字节完全一致；见 real-readonly-reviewed-candidate.json。 |
| 已知坏实现 | PASS；修复后候选的两个 mutant 均被拒绝：秒级文件名造成 20 次仅 1 次成功；忽略 ack 发送者错误隐藏 b。 |
| 共用信封与答复 | PASS；补齐 certainty/bundle_id、全部规定的类型引用、带偏移时间；新增用例先红后绿，原独立探针逐字重放 13/13。 |

最终套件 **12/12，退出 0**：[`review-green-final/output.txt`](review-green-final/output.txt)、[`commands.json`](review-green-final/commands.json)、[`run.json`](review-green-final/run.json)。Python 编译检查和 git diff --check 通过。

一次 fresh-context 独立审查对旧候选的结论为 **FAIL**，发现三项信封遗漏；原结论、局限和修复验证见 [REVIEW.md](REVIEW.md)。没有把旧结论上调为新候选的审查 PASS。

## 失败方式处理

| 失败方式 | 处理 |
| --- | --- |
| 并发同名、时钟回拨 | 无覆盖原子发布；同一 UTC 秒的序号冲突继续分配；回拨后回到原时间仍不覆盖。 |
| 半截写入 | 不进入 inbox；中断后的未发布 tmp 留作现场，脚本不会自行清理别的进程暂存。 |
| 重复确认、伪造确认 | 顺序重复 ack 不新增文件；只有原收件人能写有效确认。身份是 Herdr 期显式参数，不宣称操作系统认证。 |
| 悬空 reply_to | send 拒绝；list 跳过损坏条目及悬空链，逐条诊断、退出 1。 |
| 损坏 front matter、非 UTF-8 | list 跳过并报错、退出 1；写入正文拒绝非 UTF-8；不覆盖失败现场。 |
| 极长正文 | 无静默截断，约 200,000 行 UTF-8 正文逐字保留。 |

## 命令与对接

```sh
scripts/inbox ready
scripts/inbox list --role executor
scripts/inbox ack --role executor --id ENTRY_ID
scripts/inbox send --from worker:s8-t053 --to triage --kind issue --title "标题" --body-file evidence/问题.md
scripts/inbox send --from executor --to triage --kind disposition --reply-to ISSUE_ID --action close --reason "理由" --basis "依据" --body ""
scripts/inbox send --from ideation --to executor --kind answer --reply-to ISSUE_ID --ref issue:ISSUE_ID --ref worker:WORKER_ID --bundle-id BUNDLE_ID --certainty relayed --body-file evidence/答复.md
```

answer 默认 `certainty: relayed`；省略 bundle-id 时生成新包 id，同包可显式复用。ref 支持 spec 的类型引用和角色卡的 file:路径#L行号；file 与 body-file 只允许项目根目录内的现存文件。

**T-054 对接接点**：读取 `evidence/*/sessions/manifest.jsonl` 的 `cutoff_at`，只读清单、不读原生会话或副本正文。此处已用清单夹具验证，尚未与 T-054 的实际 session-copy 输出联合运行；T-054 应采用该字段/位置，或由主控协调统一。role 卡没有参数改名。

真实仓库 ready 列出 T-053/T-054/T-055，但因旧 ticket 缺 ready 三字段返回 1；三个 list 返回 0。这是保留的明确不合规诊断，没有替旧 ticket 补授权字段。

重放须指定尚不存在的输出目录/文件，避免覆盖证据：

```sh
python3 -B acceptance/test_inbox_e2e.py --artifacts /tmp/T-053-replay-01
python3 -B evidence/2026-10-09-batch8/T-053/run-mutants.py --out /tmp/T-053-mutants-replay-01
python3 -B evidence/2026-10-09-batch8/T-053/check-real-readonly.py --output /tmp/T-053-readonly-replay-01.json
python3 -B evidence/2026-10-09-batch8/T-053/independent-replay/probe.py
```

独立探针的进程退出码不是验收：应逐项核对生成的 checks.json；本次 13 个 pass 均为 true。完整版本与证据绑定见 [final-candidate.json](final-candidate.json)，环境及请求配置见 [environment.json](environment.json)。Fast 请求参数不等于供应商实际 tier 证明。

完整夹具、原始失败、暂存文件、候选/反例源码均归档，见 [ARCHIVES.md](ARCHIVES.md)。地图检查为 Problems 0、Stale living docs 0。未做 fork 构建、Herdr 调用、跨会话唤醒或正式工作台操作；这些不属于本票 CLI 验收。没有待用户决定的设计事项；执行主控负责关闭 ticket。
