# T-006 运行与验收结果（2026-10-06）

状态：PASS — 仅限首个本地受管理交付闭环。项目完整 MVP 仍未完成。

## 候选与范围

- 实现提交：5ab42ffe1c49770ed83f19a4a40e3fd8653ccbf1。
- 完整现场证据候选：73724ef0ba3c1e8de96ef10517e26c1096632bbc。
- 修正 oracle 后的验收候选：033631dd84e020591e6879c48ebdfe6d11a4ce9e。
- 三者中的 coop.py 相同；最后一轮只补上已有分页契约的边界验收。
- 实际 Codex 交付并集成的夹具 commit：349b26fb9ec8c10b7fa0b12e020aaa8d9f2322c4。
- Herdr client 0.9.3 / server 0.9.1，协议相容，未重启或升级 Herdr。
- Codex 最终执行版本 0.160.1；最初启动触发的 0.160.0 更新异常保留在 commands.jsonl。
- 同用户可信协作；不宣称 worktree/SQLite 是恶意 agent 的安全隔离。

## 分工

实现与独立验收分别由两个 gpt-6.1-sol xhigh Fast worker 完成；
gpt-6.1-sol high monitor 只读采样，单独的 xhigh Fast reviewer 审查固定候选。
主控负责现场接入、跨任务协调、反事实、真实运行与本地集成。
Fast 有请求 argv 和 UI 证据，供应商实际 tier 未独立观测。
所有本项目临时 worker / monitor / reviewer pane 已回收，见 final-panes.json。

## 验收

| 检查 | 结果与证据 |
| --- | --- |
| CLI 端到端 | 8/8，check-20261006T051250.900302Z-868b0dd9.json |
| 并发和身份 | 两组 task 各四个 claim 子进程、只有一个成功；错 session/fence/spec 与撤销后旧 attempt 拒绝 |
| 交付和验收 | 未验收/坏候选不能改集成引用；输入 oracle 快照和代码候选冻结 |
| 基线与重放 | 验收后引用改变拒绝；成功后重放不新增 reflog |
| fence / oracle gate mutant | 两个错误变体均在业务断言上失败，mutations.jsonl |
| 真实 Herdr/Codex | live-02/result.json 为 PASS；143 条事件，claim、dispatch、submit、验收、集成和回收各一次 |
| 启动受阻 | live-01 正确暂停，prompt_sent=false；目录信任经主控核对后回收原 attempt，再创建新 attempt |
| 独立行为审查 | review-initial.txt 的上界 P2 已经 review-targeted.txt 定向复核关闭 |

真实运行命令：

```sh
python3 -B acceptance/live_herdr.py --parent-pane wF:p1 \
  --fixture-repo /Users/luckye/Documents/Code/a2a/.runtime/live-01/fixture \
  --output evidence/2026-10-06-managed-01/live-02
```

上式是已执行命令，不能覆盖重跑。重建时用新的输出目录和独立夹具，
按 README 完成有界目录信任准备。当前夹具已集成，不能悄悄复位旧证据来重跑。

独立本地验收可重新运行：

```sh
python3 -B acceptance/test_coop_e2e.py
```

套件自动创建新的临时 Git repo、状态和 check 文件，不覆盖旧运行。

## 审查修复的反事实

原 oracle 没检查 limit=101。遗漏上界的坏候选通过旧 10 项 oracle；新增真实 CLI
验收先出现 0 != 1 的业务失败（check-20261006T051215.814686Z-74ea90a1.json）。
补入 100 正控制和 101 负控制后，坏候选返回 oracle_failed，引用仍为基线。
同一个实际集成 commit 经更新后 12 项 oracle 读回全部通过，见 oracle-upper-after.json。
旧 live 的验收快照未改写，新增结果是补充验证，完整 Herdr 执行没有为这次测试修复重复。

## 下一步和限制

T-007 是下一张 build ticket：完整中断与恢复注入。持久邮箱、租约/心跳、
更多 CLI 和收益对照仍在后续范围。本轮不提供生产部署、长期无人值守、
总成本降低或可靠性提升的结论。公开 claim/submit 门禁已运行，绕过磁盘权限的
恶意写入不在这个信任模型内。
