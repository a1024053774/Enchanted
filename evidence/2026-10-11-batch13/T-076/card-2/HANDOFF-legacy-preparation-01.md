# T-076-2 legacy-green准备（F13待批，当前不要运行）

状态：**INCOMPLETE**。决定03批准的F05–F11/W07已实施到候选测试与runner，尚未运行动态验收。F08清单遗漏一个需要合法来源前置的旧Git反例，已按边界上报F13，批准前不修改该方法，不能宣布完整legacy-green可执行。真实回合0/8。

## 已准备内容

- `legacy_quality_driver.py`只经真实CLI执行外部reviewer/执行主控动作，单独记录命令、评分输入及逐attempt准备方式；不补写生产状态。
- 旧线程服务保持外部受控边界，dispatch产生受控创建账本，submit从该来源取事实。reviewer走真实Panes、独立home、B/relay，PTY/进程观察提取为共享测试模块；报告明确无真实模型/进程证明。
- Coop指定准备改dispatch，W07直到verified/C的原claim检查保留；Run指定成功场景增加显式主控driver，首拒保留worker；Recovery源码逐字不改，adapter按method＋owner精确选择准备方式。
- F10新增`MANUAL-CLAIM-SOURCE`，W07新增`W07-MANUAL-SOURCE`。唯一变异为删除integrate的来源前置；两个测试都检查Git未变，后续仍报错不能掩盖已写Git。候选补充`managed_frozen_candidate_integrates_original`完整保留dirty/head/冻结C/C2拒绝/原C集成证据。
- 受管冻结场景将短SHA、非HEAD以及同C重放作为同一真实B批次，避免为受控回执耗用过多turn；dirty和后来的C2另行交付，仍全部经过原relay/门禁。其四项身份/交付拒绝计数按独立输入预先固定，不取实现输出作预期。

## 红态优先与一次合并阶段

F13批准并完成其准备后，拟运行：

```sh
zsh evidence/2026-10-11-batch13/T-076/card-2/outside-sandbox.sh legacy-green legacy-green-01
```

顺序为：F10来源变异体红态 → W07原方法来源变异体红态 → F10候选及受管冻结补充 → 完整8/9/18 → T-075任务卡15项与relay → 尾注/环境、多回合4项及一致性诊断 → 启动/停止4＋4及顺序反事实 → 五类变异体与两项对照。第一处非预期失败停止，不重试；不重复wide-green/reviewer-green。

当前runner在启动任何后台之前检查F13准备是否完成，未完成即退出INCOMPLETE，不能把这个准备拒绝记作业务红态。新F10/W07断言尚未取得运行红态，报告没有提前填PASS；不需要为它们修改产品逻辑。

8/9/18因原runner依赖主checkout的Git历史，会使用冻结期间的主checkout测试入口；开始保存源码，结束逐字节核对所有捕获源文件未变。新正反例、PTY/模型相关回归和变异体使用/tmp源码副本。每组来源清楚标明，不把主checkout运行写成副本运行。

沙箱外动作只含自建socket、后台、ps/信号、Git屏障、测试文件锁及原离线窗口/卷检查，无真实Codex/auth/hook安装，无正式工作台操作。只使用已存在的依赖，缺外置盘即停止。

## F13最小待批项

[ISSUE-non-fast-forward-fixture.md](ISSUE-non-fast-forward-fixture.md)，收件箱`20261011T185808Z-worker:s13-t076-2-issue-001`。

仅请求把`test_non_fast_forward_git_result_cannot_integrate`中的`a = self.create()`改成`a = self.create_managed()`。其review和score由已批准helper提供；原Git wrapper、真实输出记录、v.M=B、`integration_not_fast_forward`及ref=G断言都不改。决定03/F08只批准6个调用点，不能借已有总体授权加入第7个。

## 范围与静态检查

验收具体diff在[legacy-acceptance-hunks.diff](legacy-acceptance-hunks.diff)。`audit_legacy_scope.py`先核对批准的method范围，再核对W07保护前缀、未列方法、Recovery完整文件，最后逐字比较交接diff；它只证明修改范围，不替代行为验收。

静态收据生成命令：

```sh
python3 -B evidence/2026-10-11-batch13/T-076/card-2/check-legacy-preparation.py --output evidence/2026-10-11-batch13/T-076/card-2/legacy-preparation-checks.json
```

diff再生成命令（新输出文件名，不覆盖本次已交hunk）：

```sh
git diff a7f4cc3033c16d5888de50d8352da516c941f8e9 -- acceptance/test_coop_e2e.py acceptance/test_recovery_e2e.py acceptance/test_run_e2e.py
```

F13决定到达后，仅落实批准的准备调用点，重新冻结静态收据，再交OUTSIDE-SANDBOX READY；当前停在决定边界。
