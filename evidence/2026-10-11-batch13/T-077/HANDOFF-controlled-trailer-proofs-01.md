# T-077 两条受控尾注证明待运行

2026-10-14，回应主控 #96 与用户选 C 的 answer `20261014T011612Z-ideation-answer-001`。**INCOMPLETE：代码与脚本已准备，行为证明尚未运行**。产品固定 `2e2291acfee0e9b4f20c7ff952a5484c4262e20b`，不改产品；不调用真实模型。

## 本次执行命令

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-sandbox.sh controlled-trailer-proofs-01
```

新输出：`outside-controlled-trailer-proofs-01/`。Unix socket、隔离后台及自建进程清理由执行主控在沙箱外运行，本 worker 不申请提权。原真实运行入口已按本次决定关闭；旧版本和原始失败仍保留。

顺序固定为：

1. 在 `/tmp/t077-trailer-mutant-*` 复制产品，唯一改动为删掉 verify 的“只允许九种 A2A 尾注”数量检查，保留必需字段与身份检查。只运行拒收断言，必须出现 1 个业务 failure、0 errors，red_confirmed=true；否则停止，候选不运行。变体不改本分支，不提交其源码；仓库只保留原候选源码、生成变体的脚本与变异记录。
2. 在原候选运行两例：(a) 九个正确字段外加 Fence/Spec-Rev 的 C2 被 verify 以 invalid_trailers 拒收，记录 trailer_check/rejected，integrate 也拒绝且 main 不变；(b) 相同 C2 文件内容、只由生产 Git hook 生成九项尾注，verify 通过、integrate 到夹具 main、reclaim 后读回结果和隐藏引用。

预期结果文件：

- 反事实：`known-bad/run.json`、`known-bad/unittest.txt`、`known-bad/test_extra_trailers_refused/verify-reply.json`。
- 拒收证明：`candidate/test_extra_trailers_refused/proof.json`、`bad-a2-commit.json`、`verify-reply.json`；包含完整提交信息、拒收原因、门禁事件与 task 状态。
- 集成证明：`candidate/test_hook_trailers_integrate/proof.json`、`hook-a2-commit.json`；包含 verify、集成事件、最终 HEAD、正确代码与保留 host-policy 的读回。
- 汇总：顶层 `run.json`，只有反事实成立、两例均通过、C2 源码一致且无超 5 MB 文件才为 PASS。

## 场景与独立预期

`controlled-trailer-input.json` 从 r3 保留下来的 Git 对象只读提取 base/C1/G/C2 的 src/summary.py 原文及 G 的 host-policy.txt。两例均经生产门禁先形成真实 Git 内容冲突、确认受控旧运行时结束并创建 fence 2 的新 attempt，再提交该 C2 代码。

“同一份重交”指两例的 C2 文件字节相同；两套隔离 repo/state 分别生成自己的有效身份。不能在第一例拒收后直接替换已经冻结的候选，因此没有改库、移除冻结限制或复用过期身份。每例都有自己的完整冲突→新 attempt 结构，符合 r3 的现场形态。

九项字段名单来自 spec 第 8 节，不读取生产 required 常量。功能 oracle 独立检查空列表、正数、负数、零值的 count/total/mean/unit，以及禁止 worker 修改的 host-policy 字节。提交只写普通 subject；生产 prepare-commit-msg 从受控原生日志读取当前模型/强度和身份生成九项。拒收例只额外传两条 `--trailer`，绿例不手写任何 A2A 字段。

真实入口为 `workbench/src/gates/cli.ts`，经 CLI 请求文件→Stop signal→真实 socket/daemon→生产门禁；Git、尾注 hook、SQLite 与 CAS 集成均真实。只替换 PTY 回调及进程事实，原生日志为独立夹具输入，没有 Codex、认证或模型服务。复用既有 `RelayConflict` 的 CLI/运行时夹具，新增 host 仅补 hook 所需的独立 turn_context。其结果不能冒称为新的真实 Codex 证据。

任一步失败即停，保留原输出，不自动重试。若候选出现真实产品缺陷，先交主控，不修产品。任一新证据超过 5 MB 也停止，交主控归档。通过后再整理提交 r1–r3 证据与本次测试/结果，回报实际 commit；此时不提前称证明 PASS。

## 准备检查

TS/Python/shell 语法与字段用法检查通过，记录见 `controlled-trailer-preparation-01.json`。尚未启动后台或运行断言。两例的预期保持不变，不放宽原 r3 失败，不改 acceptance/test_*.py。

另有非阻塞合流核对项：本候选 core 的 dispatch_intent 速度标签仍为 fast，实际 Panes 启动请求已为 default；正文 `ISSUE-dispatch-tier-record.md`。本轮不改产品或扩大证明范围。inbox 上报被既有悬空 reply_to 校验错误拒绝，原错误保存为 `issue-send-error-02.txt`，交执行主控处理。
