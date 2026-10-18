# T-095-1：选 B 后的红态、回落与第 5 回合交接

**INCOMPLETE。** 按用户新裁定，红态“修前没有独立等待状态”已取得 PASS 证据；第 4 回合两形态独立真实验证 PASS，跳过后的三个 unknown 满足“离开等待”的回落要求。真实“已回答”路径尚未运行，不能宣称整票 PASS。第 5 回合脚本与零模型检查已准备，交主控在沙箱外运行，之后再冻结读回并派独立审查。

task T-095 / attempt a1 / worker s16-t095 / ready_rev 1；session `983db526-dfe8-473a-857b-b3f2af0af582`，launch `launch-4b1abba18e87460da9cbacec04905c78`。基线 `3c9016d0230223945f0e16543b230a047c2ad032`，产品版本仍为 `faa2b9b3b9ac6195012fc8ea88e6e6d73dee2bf4`。本轮只改证据、探针与回放判据，不改产品、合同测试、dispatch、launcher、Herdr、工作台、gates、地图或全局配置。完整冻结 SHA 由交付末行提供；未 submit、独立审查、验收或集成。

## 裁定来源与历史保留

已只读核对 main `0e92f78ec6824265cdfcbb9387ba4b454d7eee7f` 上 `.project-map/tickets/T-095-worker-awaiting-controller-answer-state.md` 的“裁定（2026-10-18）”，以及收件箱 `20261018T140451Z-ideation-answer-001`。执行授权来自本会话主控 #120 / 主控 #10，逐字转达用户选择 B：红态改为修前没有独立等待状态；回落为离开等待，skip 后 unknown 满足；再用 1 个 fast 根提示回合测已回答，累计最多 5，之后不得追加。

本 worktree 地图和票不改写。旧合同的 INCOMPLETE / NO_GO 报告逐字保存在 [FROZEN-4a227114.md](FROZEN-4a227114.md)，旧审查请求见 [REVIEW-4a227114.md](REVIEW-4a227114.md)；更早失败与原件保持原样。当前结论变化来自用户改了验收口径，产品没有根据新证据再修改。2026-10-17 T-094 的 working 仍只有主控 / 用户报告；2026-10-18 四次受控运行面板阶段实测都是 blocked，不能补称复现了旧 working 红态。

## 新口径红态：修前缺少独立等待状态

[before-status-B.json](before-status-B.json)：**PASS，0 模型回合**。起点 3c9016d02 的 `scripts/agent-status` 不存在；对该版本 scripts 的状态值与中文标签查询也没有匹配。修前原有路径直接读取 Herdr，未区分等待主控回答。

使用未修改的 [red-probe-source-20261018.py](red-probe-source-20261018.py) 回放其在起点采集的真实 run：`/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-095/red-20261018T110936Z-f4d263d1`。版本检查和 Herdr 子进程被明确替换为原始回复，原命令顺序、目标身份、读屏 stdout 字节和原始状态保留；不连接 Herdr、不调用模型。只替换临时目录和假凭据来源。

| 修前形态 | 原始命令 | 回放原值 | 独立等待状态 |
| --- | --- | --- | --- |
| 折叠 | 020–025 | blocked / blocked | 不存在 |
| 展开 | 026–031 | blocked / blocked | 不存在 |

原采集器 38 个命令顺序完成、两形态 stdout 与原件逐字节一致，没有新投影状态。基线没有新入口，因此回放其原有采集器，不虚构一个修前转换器，也不以“找不到文件”的进程失败充当完整回放。复现：

```sh
PYTHONDONTWRITEBYTECODE=1 python3 evidence/2026-10-16-batch16/T-095/replay-before-status.py --report <新临时目录>/reports/before-status.json
```

报告父目录 `reports` 与其上级临时目录须预先存在；工具在该临时目录内保留回放原件，拒绝覆盖报告。

## 第 4 回合与新回落判据

原件：`/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-095/green-anchor-independent-20261018T135446Z-2626001e`；225 文件、196,652 字节；代码 faa2b9b3；Codex 0.163.0、Herdr 0.9.4。worker `t095-probe-71d17066e9`，launch `launch-t095-probe-32ee664e4b1b45249a3a9b8bcde50904`，pane `wF:p6M`，native UUID `01a14f4b-a96a-7cb0-b480-a697871a66f7`。

操作者 #118：首次 COLLAPSED 前只观察、没有展开；之后 Shift+← 展开，Ctrl+] skip；后续 30 秒、60 秒无输入。这与第 2 回合曾先展开再折叠的操作分别保留。

| 阶段 | 实际投影命令 | 原值 → 投影 | 按新裁定 |
| --- | --- | --- | --- |
| 默认折叠 | 026 | blocked → 等待主控回答 | PASS；底部计数含年龄后缀，身份正确。 |
| 展开 | 033 | blocked → 等待主控回答 | PASS；同条 skip / main prompt，身份正确。 |
| skip 即时 | 040 | working → unknown | PASS；离开等待，仍记录 screen_native_conflict。 |
| skip 后 30 秒 | 047 | working → unknown | PASS；离开等待。 |
| skip 后 60 秒 | 054 | working → unknown | PASS；离开等待。 |

[skip-B-readback.json](skip-B-readback.json) 使用同一实际 `scripts/agent-status` 回放五阶段，状态与原现场投影一致、身份及只读检查通过。新判据明确接受 working / idle / unknown，拒绝 waiting_controller_answer；本次进程退出 0、回放 PASS。新判据来自用户裁定，不是从实现输出推导。旧 [anchor-live-readback.json](anchor-live-readback.json) 的退出 1 / NO_GO 不修改；它执行的是旧的“必须 working”判据。

已知坏输入检查：将真实仍展开的画面作为“答后仍卡住”的元变换输入，实际入口仍输出等待，回放判据以 NO_GO / exit 1 拒绝。它只验证判据，不能算真实已回答证据。

## 第 5 回合：已回答探针

当前累计真实探针 **4 / 5，剩余 1**；本 worker 本轮实际使用 **0**。新脚本只接受 `--phase answered`，旧阶段不再作运行入口。单次最多发送一条根提示，不重投、不 resume、不重试、不自动回答。模型配置 gpt-6.1-sol / xhigh / 请求 fast；只复制 auth.json 到隔离 CODEX_HOME，不写全局配置。固定提示只请求一个 A/B 问题，禁止命令、读写文件、联网和子 agent，收到答案后只回复 ANSWER_RECEIVED 并结束。配置请求不证明供应商实际 tier。

在本 worktree 的沙箱外 Herdr shell 执行，先归档，PASS 后运行：

```sh
python3 evidence/2026-10-16-batch16/T-095/archive-offline-evidence.py --manifest answered-preparation.archive.json --apply
python3 evidence/2026-10-16-batch16/T-095/controlled-panel-probe.py --approve-one-root-turn --phase answered
```

1. `SHELL_READY`：只看自建 pane，确认 -zsh 的真实命令提示符、没有初始化或更新提问，然后回脚本输入 SHELL_READY。
2. `CODEX_IDLE`：确认 Codex 0.163.0 空闲输入框，再回脚本输入 CODEX_IDLE。登录、信任或更新阻断时终止，不按 Enter 放行。
3. `COLLAPSED`：提交提示后只观察默认折叠；不先展开，不按方向键或答案。就绪后回脚本输入 COLLAPSED。
4. `CAPTURED collapsed` 后，按 Shift+← 展开同一问题，再回脚本输入 EXPANDED。此时不要提交答案。CAPTURED 提示在读屏和状态投影都完成后才打印。
5. 收到 `CAPTURED expanded` 及步骤 3 提示后，确认面板显示 `› 1. A` 和 `enter submit`，**直接按一次 Enter 提交 A，不按数字键 1**。若光标在 B / Other，用 ↑ / ↓ 移到 A 后再按一次 Enter。不按 Ctrl+] skip、Shift+→ 或 Esc，不在主输入框另发 A，不发送第二条提示。
6. 提交一次后回脚本输入 ANSWERED。若提交后仍显示问题，也输入 ANSWERED 采集失败，不再次提交。没有 A / enter submit、无法确认提交时输入其他内容终止。
7. 脚本即时采集；即时采集完成后计时，在 30 秒、60 秒两个截止点继续只读采集。期间不要输入或关闭 pane。脚本最后关闭自己创建的 pane、保存绑定原生记录、删除隔离 HOME；非空夹具保留诊断。

真实判定：两形态应为等待且身份正确；提交 A 后仍是等待即失败，离开等待即满足，unknown 允许。身份、来源不可核对或传输超时不能靠“不是等待”冒充有效已回答证据。原生日志有无答案、跳过或解决事件分别照实记录；不因屏幕退出就写成已解决。采集器继续保留 INCOMPLETE，不自动判验收；运行后由主控交原件读回。此轮用完累计 5，之后不得追加。

## 已知限制与检查

- **skip 没有解决事件。** 第 4 回合前三投影读取 89,498 字节 / 20 条，后两项 96,693 字节 / 27 条。问题 call `call_a8a2609be80f4580a6f7b262d2758984` 只有 accepted 收件回执；尾部仅 sleep 返回、Extension / Reasoning item 完成、再次 sleep 和 token 记录，没有问题解决、新 turn 或整个 turn 完成。因此 unknown 满足“离开等待”，仍不能证明“已解决”。产品的保守冲突行为不改。
- **两次并发 herdr_timeout 根因未定。** `offline-native-anchor-repair-20261018T134759Z/reports/contract-final.json` 的 working-command-context（13:41:32.542819Z）与 archives-final.json 的 archive-red-expanded（13:41:32.547032Z）都在第一个假 Herdr get 超过 3 秒，返回 unknown / herdr_timeout / exit 2。完整失败及夹具保留；接近同时发生不能证明原因。生产默认每次 Herdr get/read 3 秒，Herdr 繁忙或延迟超限时会返回 unknown，暂时遮住真实等待；调用方须保留诊断、之后再读，不能当 working 或已解决。未增重试、调高期限或改 server。串行 85 项 PASS 不证明根因已解决或负载可靠性改善。
- **已回答尚未实测。** 不能用 skip 原件或离线替身补称 PASS；真实第 5 回合及独立审查均待完成。

[answered-checks.json](answered-checks.json)：零模型接线、卡住结果如实保留、凭据来源误绑拒绝与清理检查均 PASS；旧探针不支持 answered（exit 2），新计划为单次根提示 / 累计 5 / fast / 手工 A+Enter；卡住元变换被实际入口判据拒绝。产品及原合同测试未变，未重复原 85 项大套件；先前三原件回归 11 项、串行 85 项 PASS 和并发两份 FAIL 原样保留。`answered-map-status.txt`：0 problems / 0 stale living docs。

## 归档和冻结

前轮 732 文件 / 6,886,506 字节归档已核对 PASS。上次新增的 57 文件 / 602,404 字节读回包尚未在外置盘找到，已连同本次准备原件复制进新暂存包；没有覆盖旧暂存。新 [answered-preparation.archive.json](answered-preparation.archive.json) 共 **300 文件、1,439,478 字节**，等待主控沙箱外复制。真实 run 主原件一直位于外置盘；新的包只复制、不删除、0 模型回合，缺盘或目标存在均停止。

本次 READY 只交付冻结脚本与证据，不代表已回答验证或整票通过。[REVIEW-REQUEST.md](REVIEW-REQUEST.md) 明确补测前不派审；取得真实已回答原件后再针对最终冻结 SHA 更新请求。
