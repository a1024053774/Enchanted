# T-077 S3 结果：真实冲突与两条受控尾注证明

## 最新合流状态：主控 #118

**INCOMPLETE。** final-03 已通过 driver-readiness、审查清理四条反事实及候选四项、三条 joint 反事实与候选、七条冲突反事实、S3 全量 25、coop 8、recovery 9。随后 run 的第 11 项因 adapter 缺少 overlap_reason 参数而 ERROR；已收集全部 18 项，但 failfast=True 使其余 7 项未运行，后续阶段也未运行。原始失败与控制台输出不变。

本轮仅修夹具，提交为 `30ebf967573be231daa142f1b09f98d18e508295`：手工 claim 经父级将理由传到真实 CLI，受管 dispatch 同样传 `--overlap-reason`；runner 关闭 failfast 并记录实际执行名单，仍要求完整数量和全部通过。局部反事实修前 2 errors/1 failure，修后 4 项通过；它们只证明参数传递与调度修复。产品仍为 `5d0bf1e8`，acceptance 业务文件不变。诊断和再生成命令见 `DIAGNOSIS-rebase-final-03.md`。

新的全量 39 子阶段为 `outside-sandbox.sh rebase-final-04`，输出 `outside-rebase-final-04/`，尚待主控运行。准备检查已通过，见 `rebase-final-04-preparation-01/static-checks.json`；产品冻结版本与修复后的夹具版本分别锁定，不能用局部检查替代 run 18 项或后续真实入口检查。完整命令和结果读回要求见 `HANDOFF-rebase-final-04.md`。本轮真实模型回合 0；独立审查尚未开始，ticket 保持 open。

## 最新合流状态：主控 #110

主控 #114/#115 更新：final-02 仍 **INCOMPLETE**，只通过 driver-readiness，随后因 runner 不接受 Git archive 中的 26 个 `workbench/hooks/* -> hook.py` 符号链接而停止，产品业务阶段未运行。不是 pax 全局头：tarfile 可见条目中没有该头。原 final-02 输出保持原样。只修 runner 后，局部实际归档解包检查通过（26 个链接重建、普通文件字节/权限不变、9 类非法条目仍拒绝）；产品仍为 `5d0bf1e8`。新的 39 阶段为 `outside-sandbox.sh rebase-final-03`，结果写 `outside-rebase-final-03/`，尚待主控运行；本轮真实模型回合 0。

**INCOMPLETE。** final-01 的三条 joint 变体均命中各自断言、七条冲突红态成立、候选 joint 三项通过；S3 全量 24/25 通过，run 清理例因 fixture driver 把 reviewing/null 提前判为绑定不同而 ERROR，后续阶段未运行。原 `outside-rebase-final-01/run.json` 与失败现场保持不变。

两项修复分别提交：`7b3463c4a55381d0fb97f782e69cc0029522f6da` 修夹具就绪判断，修前局部反例 1 failure/0 errors，修后 5 项通过；`5d0bf1e84c02fbcb4b7699cdd9a48c4f6582c6b4` 接入审查目录的用途/序号与已存结果后的结束清理。审查清理先对 final-01 原受控真实入口场景作独立读回，结果/回收事件已存而目录、Git 登记仍在：1 failure/0 errors，见 `review-lifecycle-recorded-red-01/`。新入口的修前反例与修后四项绿态尚未运行，均在 final-02 中，详见 `DIAGNOSIS-rebase-final-01.md`、`REVIEW-WORKTREE-IMPLEMENTATION-01.md` 与 `HANDOFF-rebase-final-02.md`。

重新运行的阶段命令为 `bash /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-sandbox.sh rebase-final-02`，输出新目录 `outside-rebase-final-02/`。共 39 个子阶段，保留原 33 项编排，增加 driver 局部检查、修前四条 review 生命周期反例及候选四项。冻结候选为 `5d0bf1e8`；准备和语法检查通过不代替业务绿态。新增真实模型回合 0；独立审查尚未启动；ticket 仍 open，待主控关闭。

## 用户选 C 的历史证明

2026-10-14。**PASS：用户选 C 要求的两条受控证明及证据整理；ticket 保持 open，待主控关闭。** 原 r1–r3 失败仍保持各自的 INCOMPLETE，不回填为真实完整闭环通过。

依据：用户 answer `20261014T011612Z-ideation-answer-001` 选“C 受控证明后关票，并改角色卡”；主控 #96 派发两条受控证明，#100 确认沙箱外运行 PASS 并要求提交。产品版本为 `2e2291acfee0e9b4f20c7ff952a5484c4262e20b`，包含 S3、relay 作用域修复及显式 default。本轮只新增测试、脚本和证据，没有产品代码变化。

## 两条受控证明

真实入口是 `workbench/src/gates/cli.ts`，经请求文件、Stop signal、Unix socket、daemon 和生产门禁。Git、尾注 hook、SQLite、验收及 CAS 集成均真实；PTY 回调和进程事实由隔离夹具提供，没有调用模型、读取 auth 或写全局配置。

每例都复现 r3 的 C1/G 真正文本冲突、旧受控会话结束、fence 2 新 attempt 及 C2 重交。C2 使用 r3 Git 对象保存的源代码，两例文件字节相同；各自创建隔离身份，避免替换已冻结候选。独立功能 oracle 检查空列表、正数、负数、零值的 count/total/mean/unit 及 host-policy 原字节。

| 检查 | 结果 | 主要产物 |
| --- | --- | --- |
| 先取得反事实红态 | 只在 `/tmp/t077-trailer-mutant-syrgp0jn` 移除多余尾注数量检查。变体 verify 返回 ok=true，拒收断言失败：1 failure、0 errors、red_confirmed=true | `outside-controlled-trailer-proofs-01/known-bad/run.json`、unittest.txt、verify-reply.json |
| (a) 十一项尾注被拒 | 九项正确尾注加 A2A-Fence/A2A-Spec-Rev。verify 返回 invalid_trailers；trailer_check 158 为 false、rejected 172 记录原因，task 仍 submitted；integrate 以 not_verified 拒绝，夹具 main 仍为 G | `candidate/test_extra_trailers_refused/proof.json`、bad-a2-commit.json |
| (b) 九项 hook 尾注可集成 | Git commit 只传普通 subject，没有手写 A2A 字段；生产 hook 生成九项。verify passed，integrate 210，task accepted；回收后实际 Git HEAD/main=C2 | `candidate/test_hook_trailers_integrate/proof.json`、hook-a2-commit.json |
| 汇总 | exit 0、candidate 2 tests/0 failures/0 errors/0 skipped，same_C2_code=true，新增真实模型回合 0 | `outside-controlled-trailer-proofs-01/run.json` |

拒收例 C2=`2de3c6db46be79e77bc0369a8d3865fc16511416`，G=`fb04d484da3124e60c11bbef9f5df0e651a1c11e`。绿例 G=`be0aa7b56cd5f7028afd3b37c5719016a0aac732`，C2/M/main=`feaec0b72720c2ce49e88858bc75937f7ca867c9`；独立 Git 读回与报告相符，C2 源码和 host-policy 字节正确，隔离 daemon PID/socket 均已移除。

变体源码仅在 /tmp，**不提交**。提交的 sources.tar.gz 保存原候选及测试；逐文件核对 src/hooks 与产品版本一致。变异配方与误放行输出保留，证明断言能检出坏实现。

## r1–r3 的原始结果与归因

| 场景 | 实际结果与归因 | 本次保留方式 |
| --- | --- | --- |
| r1 | 4 回合。真实冲突及新 attempt 已形成，新 worker 写了 C2 和 delivery；relay 的 state 全局 request_id 键误拒新 launch。归为产品缺陷，已先红后修复、绿态及变异体，并保留旧失败 | `real-conflict-01/`、REAL-APPROVAL-01.md、real-relay-diagnosis-01.json；已在 da44c673 进入 Git |
| r2 | 观察 1、保守预留 2。交付成功，回执被近额换模弹窗干扰，设置改为 luna/medium、没有新原生回合，最终超时。限流/交互协议未决，不能仅凭 99% 证明硬额度耗尽 | `real-conflict-02-evidence.tar.gz`、REAL-R2-DIAGNOSIS-01.md |
| r3 | 4 回合。真实文本冲突、旧 worker 结束、新 attempt 建立、真实 worker 整理 C2 并重交、relay 处理和回执均到达。九项身份值全部正确；worker 自己在 git commit --trailer 加 Fence/Spec-Rev，使十一项断言失败。C2 verify/integrate 未到达 | `real-conflict-03-evidence.tar.gz`、REAL-R3-DIAGNOSIS-01.md、real-r3-diagnosis-02/ |

**r3 归为模型行为：被测 worker 手写了不受支持的尾注。** 原 rollout ordinal 73 的工具输入直接包含两个多余 --trailer；不是新 attempt/launch/native 身份串错，不是本轮夹具九项预期写错。用户选择用受控证明补验收与集成，不再追加模型回合；主控负责的新角色卡已提示不要手写尾注，本 worker 未改角色卡。

证据组合的界线明确：冲突写回背景、会话结束后开新 attempt、真实 worker 整理并重交由真实 Codex r3 证明；正确重交后的 verify/integrate 由本次受控证明覆盖。受控结果不冒称为 r3 原运行继续通过，也不证明新的模型可靠性或成本收益。

## S3 与回归证据索引

| 合同 | 已有证据 |
| --- | --- |
| 命名、清理表、隐藏引用、脏/未知不删并上报 | S3 25 项合同；`outside-relay-regression-01-contracts/run.json` |
| 路径交集拒绝、理由放行并记录 | 同一 25 项合同，包含 claim 路径与理由检查 |
| 文本冲突回写、已结束会话新 attempt、未知结果不重发 | 冲突 7 项、Panes 4 项、真实 r3；最终重交尾注与集成见本次两例 |
| R8 第四次停止、机械重验、审查身份绑定 | 合同中的 R8/CAS 场景；审查复用/重审接口已预留，T-076 质量串不归本卡实现，不冒称新增 reviewer 会话 |
| 检出工作区未提交改动保护 | 合同中的 staged/unstaged 字节保护与 system issue |
| 8/9/18、CAS、cards 等 | relay 修复后的 16 阶段回归全部 PASS：coop 8、recovery 9、run 18、cas 1、cards 15、panes 4、identity 4、shutdown 4、原生记录及 relay 正反例；`outside-relay-regression-01-summary.json`（产品 da44c673） |
| 普通速度覆盖 | 显式 default 的最小检查先红后绿 4 项；default-tier-red/green-01.json、主控 tier 探针副本；后续产品 2e2291ac |

本次没有新增独立模型审查会话，也没有重跑最新 main 合流后的全套检查。用户已选择当前证据组合；后续合流与关票由执行主控处理，不借旧通过记录替未运行的合流结论背书。

## 模型回合与隔离

被测 CLI 固定 codex-cli 0.162.1，真实 worker 为 gpt-6.1-sol / xhigh。r1 请求 Fast，r2 无 tier 参数，r3 显式 default，启动 argv 与实际上下文分别保存；不把请求档位当作供应商实际速度证明。

真实观察累计 **9**：r1 4、r2 1、r3 4；保守占位累计 **10**：4+2+4。本次受控证明 **0**。旧 journal 不释放或改写。每次真实 home 只复制 auth.json、只信任夹具 Git 根、只有 git add/commit 两条 allow，hook 逐次审批；结束后的 home 均已删除，auth 未进归档。旧角色、任务卡、审批、事件、失败与原生日志保留。

## 再生成命令与提交

重跑整个受控证明（执行主控在沙箱外，新输出目录不得存在）：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/run-controlled-trailer-proofs.py --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-controlled-trailer-proofs-replay
```

单独再生成两条证明（同样在沙箱外，仍经真实 CLI；source 在本交付提交，产品必须与 2e2291ac 相同）：

```sh
python3 -B workbench/tests/test_conflict_trailer_proofs.py --source /Users/luckye/Documents/Code/a2a-wt-t077 --input evidence/2026-10-11-batch13/T-077/controlled-trailer-input.json --output evidence/2026-10-11-batch13/T-077/proof-red-replay --case red
python3 -B workbench/tests/test_conflict_trailer_proofs.py --source /Users/luckye/Documents/Code/a2a-wt-t077 --input evidence/2026-10-11-batch13/T-077/controlled-trailer-input.json --output evidence/2026-10-11-batch13/T-077/proof-green-replay --case green
```

工作目录均为本 worker worktree。执行时原 runner 保存为 `outside-controlled-trailer-proofs-01/orchestrator-at-run.py`；交付脚本只调整版本保护，使后续证据提交可重放，仍强制产品 src/hooks 与 2e2291ac 零差异，业务断言未改。

原真实失败的只读诊断可用 diagnose-real-r2.py / diagnose-real-r3.py，具体命令在各 DIAGNOSIS；恢复完整现场的命令见 REAL-EVIDENCE-PACKAGING.md。历史真实启动命令仅留档，outside-sandbox.sh 已拒绝所有真实启动入口。

r1 已提交；r2/r3 原始目录未删改，逐文件比较一致后压缩提交（1,477,465 与 2,621,147 字节，均低于 5 MB），索引为 real-evidence-archive-index.json。遗留真实证据提交：`ae33ae6cfcfd422f0d8cab9cb5180d93c7b8c479`。本次证明、脚本、结果和 Resolution 另作一组提交，完整号见终端回报。

差异空白检查提示来自两个原始 C2-message.txt 及六份 Git show 的 stdout.bin 末尾空行，均为原始命令字节，保留不规范化；其他新文本 UTF-8/LF、无 BOM 或替换字符。无超 5 MB 文件，变体源码未进入暂存区，产品及 acceptance/test_*.py 未改。ISSUE-dispatch-tier-record 正文随交付，inbox 的既有投递错误由主控处理。
