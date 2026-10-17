# 排练与操作现场的检查差异清单

状态：**扫描/现状红态已保存；补齐绿态 INCOMPLETE**。不把分支覆盖扫描当作业务通过。以下行号对应本次未修改的运行源码（dc15dc3f0）；历史副本保持原样。

扫描入口 `audit-rehearsal-guards.py` 实跑了 `workbench/tests` 与整个 `evidence` 的 rg 可见 Python/TS/JS/MJS：**2716** 份文本。`guard-audit-01/literal-REHEARSAL-all-text-copies.json` 保存31处字面命中；`scene-and-mode-branches.json` 保存167处 Python 条件候选。另检查284份 `*sources.tar.gz`，其中52处同一 raw-retention guard 的冻结别名逐个记在 `frozen-source-guard-aliases.json`（archive/member/行号）；不解包改写旧冻结。任意其他现场 tar/SQLite/二进制不是可执行源码搜索对象。下面按实际执行路径归并，不把 dry-run 的零副作用约束误当作业务成功。

## 直接以 REHEARSAL 跳过的检查

| 位置 | 实际跳过内容 | 纳入新排练的方法与已知坏反例 |
| --- | --- | --- |
| `workbench/tests/t078_raw_retention.py:420–421` | 整个 `validate_owner_receipts` | 去掉场景豁免；用真实 Stage A/两角色 B1 收据共同构造 owner，不填假字段。改错原 claim/target/版本/manifest/API ready 任一字段必须在签名前拒绝。 |
| 同上 `:422–423` | 恰九种进程标签 | 排练真正启动两组 shell→确定性 peer，连同 daemon、target shell/leader、两 API 共九个持久进程；不能把一个 PID 同时写成 shell/CLI。少一个/重复 PID 拒绝。 |
| 同上 `:430` → `:380–397` | 完整拓扑读取、原九节点 PPID/PGID/TPGID、daemon 后代集合 | 使用真实 ps 的同一函数与原 graph 收据；无 scene 豁免。实际派生合法/非法子进程走同一检查；合法描述必须先由 #364 原证据确认。未知子进程、错误父节点、原节点改变、PID 复用均拒绝。 |

第一行连带跳过的子检查，逐个原表达式另见 `skipped-owner-receipt-checks.json`：

| 原函数位置 | 检查 |
| --- | --- |
| `t078_raw_retention.py:65` → `:51–60` | 真实 root/不经 symlink、`/private/tmp/t078-*`、允许场景、八个非空 target 字段（finish/capture 本身另有 owned_root，不能据此声称许可前也做过） |
| `:66–67` | operational scene 及完整40位 source revision |
| `:69` | 原 Stage A root 与 claim 对象完全相等 |
| `:71–73` | task/attempt/session/fence/spec/thread/workspace/target launch 与原 claim 逐项相等 |
| `:76–78` | 原 identity_receipt root/完整 processes，原 daemon 与 target 两 PID |
| `:83` | 各角色 API PID 与 ready 原件相等 |
| `:84–86` | API role、stage A、protocol、model0、完整 argv 尾部 |
| `:88–91` | 每角色原 B1 manifest launch/session/shell/CLI PID/lstart |
| `:93–94` | 原角色 argv 可执行文件、`--session-id` 与该角色 debug 路径 |

`check_identities:424–429` 的重复 PID、两次 argv/lstart 检查在 REHEARSAL 中仍执行。`:430` 同时用列表相等决定是否做全图检查；未来应按“核对全部原标签”识别全量调用，不能靠标签顺序逃过拓扑。停机后只核对单个 API 的子集调用不应再要求已退出 daemon 存在；这是停机生命周期阶段，不是 REHEARSAL 豁免。

## 没写成 scene 条件、但由排练入口绕过的路径

| 排练入口位置 | 被代替/未执行的操作现场检查 | 补齐边界 |
| --- | --- | --- |
| `test_t078_09c_real_chain.py:112–119`；09B `test_t078_a14_rehearsal.py:188–193` | 排练手写部分 readiness/static packet；不经 `evidence/.../T-078/run-09b.py:13–72,78–120` 的签字、完整静态 root/源版本/回归组合/派发前材料预检 | 调用同一预检函数并用完整真实生成的收据，明确标记确定性 provider；错批准/源版本/原收据/不完整卡片零 root/进程反例。现有 card_save/create/dispatch 是真实入口，不能混称卡片完全没检查。 |
| `test_t078_09c_real_chain.py:121–130`；09B `test_t078_a14_rehearsal.py:207–218` | 直接 controller_start 与手写 readiness，不经 `run-09b-stage-b.py:30–51,73–97,140–151` 和 `run_t078_p1.py:90–145` 的原 Stage A 活身份、签字/屏幕计划、复用 API 解析、launch 前逐文件、实际 binary/version/help等 | 将确定性 provider 作为明确的测试输入，经相同收据/解析/批准入口；只替换供应商执行文件。无供应商会话。peer实际接收同一session/debug参数并写真实manifest，argv[0]记录Python而非冒充Claude；version/help如实标为测试provider。首启真实 Claude 的字面语义仍单独靠实际首启证据。 |
| `t078_09b_rehearsal_host.ts:29–46,54–70` | 原 controller zsh→Claude 被直接 Python peer 替换；processInfo 返回同一个真实 PID 作为 shell/leader。只做 peer argv/lstart，不具有九进程拓扑 | 改为真实 shell→peer，保留对应 PGID/TPGID/PPID，manifest 记录真正的两个 PID 与 provider 种类。关键业务身份/Stop 仍走产品，不自造成功 relay。 |
| `test_t078_09c_real_chain.py:139–159` | owner scene=REHEARSAL、仅七进程，缺 stage_a、identity_receipt、roles manifest、process_graph | 走共用 owner producer 与完整 receipt validator；不允许换 scene 名称逃过。以上三项直接 guard 红态已证实该缺口。 |
| `test_t078_09c_real_chain.py:308–348`；协调器 `test_t078_09c_coordinator_chain.py` 继承该 cleanup | 只做一致 DB backup/目录复制→直接 daemon_stop/Popen stop→删 root，未走标准 capture→逐成员 tar 读回→独立签字→finish 的完整 gate/稳定性/topology/持久 shutdown-intent | 新排练真实执行标准 archive/finish 流程；预先提供明确排练签名。坏 tar/源集合增长/未签独立读回/错误 owner 均在 stop 前拒绝。停后不读 SQLite。局部 Popen 清理不能冒称同一路径。 |
| `t078_rev2_tools_cases.py:51`；`test_t078_rev2_rehearsal.py:270–305` | unit owner 用 REHEARSAL、daemon 为本进程和 Lifecycle.normal_stop spy；offline276–278 再用虚构 API PID | 保留为明确的 unit/HTTP handler 反例，不能计作真实拓扑或全链绿态。拓扑/停止必须另用上述九个真实进程、真实 daemon_stop 的共同链证明。 |
| `test_t078_rev2_rehearsal.py:92–119,141,184,264–265,276–302` | `offline` 用 Handler 字节流/注入时钟/fixture rows/window，省真实 socket/进程/Electron/时钟等待 | 保持 unit 范围标注；09C 新完整排练必须用真实 HTTP、系统时钟、Electron 与 daemon/relay。不能用 offline PASS 替代120秒和生命周期证据。 |

协调器排练的 `test_t078_09c_coordinator_chain.py:24` 额外要求签名含 `REHEARSAL ONLY`，不是豁免；但仍继承上面 setup/bind_owner/cleanup 的绕过。`run-09b-stage-b.py:54–59,140` 的 dry-run 用 static_process_probe，只可用于“零 spawn 材料校验”，不能视作 ps 身份/拓扑绿态。

## 已逐项检查、属于场景/只读模式而非排练豁免的条件

| 位置 | 结论 |
| --- | --- |
| `t078_09b_phase_registry.py:102,136,158,168`；`t078_09b_phase_driver.py:43` | 根据 plan.scene 选09C业务/预算；排练 plan 本来就是09C，实际执行这些检查。 |
| `t078_09b_i1_permission.py:41` | 仅C-I2需要<120秒早停门；09C排练已运行，不能在09B上套不同协议。 |
| `t078_09b_rehearsal_peer.py:57,147,164` | 09C特定工具/输出行为；真实C分支已跑。`:90` 限定自建scratch，是附加限制。 |
| `evidence/.../T-078/prepare-a14.py:55,143` | 09B executor 上线必须有 pending/零I2、首启每键后observe队列；09C先两角色就绪没有这个pending前置。09B等价夹具须保留六键queued/无delivered/无I2反例，不以09C排练替代。 |
| `evidence/.../T-078/prepare-rev2-owner.py:18,58` | 09B/A16与09C标签、C的target绑定，并非REHEARSAL跳过；真正问题是排练没调用该producer。 |
| `evidence/.../T-078/run-09b.py:56`、`c2-revalidation.py:24`、`rebind-stage-a-readbacks.py:61`、`freeze-rev2-materials.py:48`、`prepare-09b-executable.py:55` | C特定收据/冻结闭包增加检查，不是放宽；未来排练要走同一预检而非手写static。 |
| `t078_raw_retention.py:445,517`、`t078_09b_i1_permission.py:105`、各排练main的check_only、`run_t078_frozen_harness.py:62`、`archive_t078_evidence.py:36` | dry-run/check-only故意在副作用前停止；仍只证明预检，不冒充完整场景。不能为了“排练覆盖”让dry-run开始按键/停机。 |
| 本目录诊断/审计脚本与历史 known-bad、source/*.py、source tar 别名 | 只读重放/冻结原件，不是当前角色执行入口；逐个保留扫描位置。新候选重冻共同闭包，旧原件不改。 |

## 实际已跑的红态与未完成的绿态

`guard-audit-01/bypass-red.json` 为本地实际调用 **原 `check_identities`** 的分支探针：操作场景用原收据会调用 receipt/topology；仅改 scene 为 REHEARSAL 后，receipt 与 topology 均不调用，删至八进程也被接受。三条是对应合同的**现状红态**，不是“候选PASS”。process transport 是明确 spy，没有启动现场或读取真实 ps。

绿态尚未实现。必须先取得 #364 的实际额外进程证据；再去除直接 scene 豁免，让新等价真实九进程夹具运行原收据与全拓扑检查；新增真实 fork 的未知子进程反例，并完整跑协调器 >120/<150秒、7/1 POST、4/1 roots、目标单Esc/无ack、归档→读回→正常停机。去掉receipt/数量/拓扑/归档读回任一检查的变异均须在对应新断言失败。**这一步不能由本次spy红态或旧7进程PASS替代，也没有声称已经完成。**
