# 第三次变基到 main：T-082 合入后重验 T-078

2026-10-16，执行主控 #316。**材料准备 PASS；变基、冲突处理和变基后回归 INCOMPLETE／尚未执行。** 本轮只准备文件及运行只读预检，没有操作保留中的 A-14。

固定起点 `cd8ca713e1ef0ef62b1bc53c4cc33fd5fcf4e246`，固定目标 `0e6c2b833f6da64243f71d670ea45bb9116fda4d`，共同基点 `490de67d05a08ccf8a453a78694a106288579b47`。当前有 120 个分支提交，另需先增加一条本次交接提交。准备时 main 为 `ad917ef54e5f2f1868ba8af023eb34f0c5e91ec6`；目标之后只追加本票的 controller-decision-04.md，详见 main-since-target.txt。执行仍用固定目标，不随 main 移动；两阶段都会要求目标仍是 main 祖先，并检查目标到 main 的提交与最终差异没有 workbench/、acceptance/、scripts/ 改动。

交接提交覆盖现有未跟踪的 `09b-startup-receipt-entry-01/`（主控运行的候选与 M5 原件）、刚开始准备的 `09b-a14-cleanup-owner.json`、`redact-a14-scene.py`，以及 RESULTS 和本目录。前者已由独立审查第二轮读回：候选 14/14、六次 release 前真实收据刷新，M5 在首键后的新 queued 断言失败；不是变基后新证据。两份 A-14 文件尚未运行、清理脚本尚未完成，不把它们作为可执行回收包。变基前只保留其工作进度，不继续填 A-15 材料。

主控以原 worker 启动身份运行：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/rebase-main-3/prepare-and-rebase.py --check-only
python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/rebase-main-3/prepare-and-rebase.py
```

第一行执行第二行在 git add 之前的全部断言，不写文件、不 add、不 commit、不 rebase。检查固定 HEAD／分支／共同基点、main 的有界前进、原启动身份、无进行中的 rebase、暂存区为空、归属清单、每个 git add 路径存在且未忽略、模拟提交后没有剩余路径，以及证据结构与 Python 语法。已实际运行的完整输出保存在 check-only-01.stdout.txt／stderr.txt。所有预检输出、RESULTS 均在交接前写好，脚本提交后不再生成仓库内报告。

第二行先正常 add/commit，保留会话的 Git hooks 和九项自动尾注，不手写尾注、不跳 hooks。只有提交后全工作树干净才创建新的 `/private/tmp/t078-rebase-main-3-*` 日志目录。随后从该交接提交导出 rebase.py 的字节到日志目录运行，避免正在执行的脚本被历史重放替换；建立 `backup/t078-before-main-3-<交接提交前12位>`，再执行 `git rebase <固定目标>`。

变基子进程沿用上次的会话环境隔离：移除 A2A_*、CODEX_THREAD_ID 和 GIT_CONFIG_COUNT／PARAMETERS／KEY／VALUE 会话配置变量，仓库与全局配置不改，不设置 hooksPath、不加 no-verify。只记移除变量名，不记环境值。重放保留历史提交尾注，不把当前身份套到全部历史提交。

成功返回 PASS 和新 HEAD；冲突时返回 INCOMPLETE，保留 HEAD、REBASE_HEAD、冲突清单、stdout/stderr、提交顺序及备份。没有自动 ours/theirs、add/continue/abort、stash/reset/clean、fetch/push 或任何服务启动。主控将日志目录与停止位置交回；worker 先把关键日志拷入 evidence，只编辑冲突文件，再交固定预期的 continue 脚本。对语义交叉拿不准时停止上报，不自行裁掉任一方逻辑。

## 冲突与回归边界

T-082 的 reviewer 副本、candidate_workspace、启动 sandbox／网络／临时目录边界、review_requirements/report、结束检查与 review_reclaimed 集成前置均保留；不拿 T-078 旧版 reviewer 逻辑覆盖。T-078 的主控 caller／Stop 转交、离线 pending／延后原 I2、daemon settle、收据刷新与首启键守卫也保留。main 的实际相关差异已保存 main-code-diff.patch，作为解冲突上下文，不作为自动套用补丁。

变基后先读新规范与相关调用者，然后在新源码上重跑：

- pending 真实 gate CLI／daemon／relay／Stop 链、在线与歧义反例；核对 created_at 不变，pending 零反馈，实际 turn_submitted 后 delivered、原 I2 恰一次。
- startup 15 项与真实入口复验；六个首启键后、release 前逐次刷新原条目，仍 queued、无 delivered 历史、无 I2；精确 M5 必须在该新断言失败。
- worker 收件箱真实入口 14 项；以及冲突影响到的必要边界检查。

沙箱外测试会在变基完成后交新的阶段脚本，绑定实际重放后的提交，使用全新输出目录；本次未运行。**Tracer bullet** 仍为 pending → unknown 入队 → 首启六键 → initial release → turn_submitted → delivered → 原 I2。**Deep modules** 保持 screenKey 只负责控制键，drain 负责业务提交，review 启动与结束核对由门禁负责。**Ubiquitous language** 沿用 pending、queued、delivered、control action，不把键写出收据当作消息送达。

关键回归通过之后才继续主控 #315 的 A-14 脱敏归档、owner-bound 回收材料与 A-15 准备；A-15 使用变基后的源码，protocol 与预算不变。A-14 本轮不发键、不 release、不 Stop、不发信号、不回收。整张 T-078 仍 INCOMPLETE，本包不构成 launch 批准。
