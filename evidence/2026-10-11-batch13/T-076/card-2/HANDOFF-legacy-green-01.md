# T-076-2 legacy-green单阶段交接

状态：**INCOMPLETE**，已完成阶段准备，动态结果待主控沙箱外执行。F13按主控 #56及决定03补充获批，指定方法只改`create()`为`create_managed()`；原Git wrapper、M/实际输出及最终拒绝/ref断言不变。真实回合仍 **0/8**。

从主checkout执行一次：

```sh
zsh evidence/2026-10-11-batch13/T-076/card-2/outside-sandbox.sh legacy-green legacy-green-01
```

输出为本卡`outside-legacy-green-01/`，目录已存在则拒绝覆盖。不要先运行旧的分组脚本。

顺序：

1. F10的来源守卫变异体命中`MANUAL-CLAIM-SOURCE`；W07原方法在同一变异体命中`W07-MANUAL-SOURCE`，另读回实际Git已变。环境/导入/usage错误不计业务红态。
2. 候选的手工claim来源拒绝与受管冻结C完整场景。
3. 完整coop8、recovery9、run18；每套首次失败即停。
4. T-075任务卡15项、relay；尾注/环境、多回合4项并记录一致性；启动/停止4＋4项及停止顺序反事实；五类变异体及两项对照。

每组结束保存命令、结果与读回，第一处非预期失败停止，不重试。不重复已通过的wide-green和reviewer-green。F10/W07新断言先跑红态再跑候选，当前尚无其动态结果。

范围审计在启动前核对批准的acceptance方法、W07保护前缀、Recovery文件逐字不变，以及[legacy-acceptance-hunks.diff](legacy-acceptance-hunks.diff)与当前diff一致。F13另核对完整方法仅这一行改变。旧回归沿主checkout入口执行并捕获/逐字读回源文件；新场景和变异体用/tmp冻结副本。证据明确标为真实后台/Git/门禁加受控外部会话。

沙箱外动作仅自建socket、后台与PID观察/信号、Git屏障、夹具文件锁、原离线窗口/卷检查。没有真实Codex、auth复制或真实hook安装，不操作正式工作台；缺外置盘即退出。完整产品仍待真实P-review/交付、T-077联验及本卡独立交付审查。

静态检查收据：[legacy-ready-checks-01.json](legacy-ready-checks-01.json)。确切再生成命令（再次运行换新输出文件）：

```sh
python3 -B evidence/2026-10-11-batch13/T-076/card-2/check-legacy-preparation.py --output evidence/2026-10-11-batch13/T-076/card-2/legacy-ready-checks-01.json
```

此前`legacy-preparation-checks.json`及`HANDOFF-legacy-preparation-01.md`保留为F13待批时的记录，不覆盖。详细迁移与断言对应见`assertion-hunks.md`第10–11节。
