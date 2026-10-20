# T-109 / a1：首轮 Electron 失败诊断与驱动修复

状态 **INCOMPLETE**。首次实现已由执行主控提交为 `681fc0da59fe9a89252bdfae837fdd69598534bd`。真实入口首轮两项通过；键盘展开步骤失败。此次只修验收驱动，未修改产品、归属规则或门禁；第二次真实 Electron 验证待执行。

## 失败位置与归属核对

原始摘要 [outside-01.json](outside-01.json)、现场 `/private/tmp/t109-real-s30elzd2` 与执行主控提供的日志均保留，不覆盖、不清理。

确切失败是 `run_t109_hierarchy.py` 原第 194 行：发送 `toggle-keyboard` 后等待实际 worker 恢复可见。原 `expected: None` 只是通用 wait 没传诊断文字，不能说明层级预期为空。

失败前，下列断言已经通过：构思主控／执行主控／实际 worker 的层级是 0／1／2，位置逐级缩进；worker 父项是执行主控；折叠后 worker 隐藏；汇总为“子会话 4 · 未恢复 3 · 未知 1”；真实 sidebar IPC 全表/schema/trace 原值未变。

只读 SQLite 与失败 DOM 中的 launch 身份一致：

| 会话 | 父 launch／位置 | 判定 |
| --- | --- | --- |
| 实际 worker、second-worker、reviewer、monitor | 均指向执行主控 `c8c147e7-3401-44e1-a9ad-20e2de429752`，DOM level=2 | 产品层级正确；此时因父项折叠而不可见 |
| legacy | 没有父字段，DOM parent 为空 | 正确放入未归属 |
| missing | 父字段为 `nonexistent`，DOM parent 为空 | 正确放入未归属 |

两个未归属 worker 与部分正常子项都用了 `a-sentinel`，不能靠 attempt 文本区分；launch id 才是本次核对依据。5 条“未恢复”提示是原夹具触发的 T-096 恢复拒绝，没有删除或放行这些拒绝。

## 驱动根因与最小修复

`t107_sidebar_driver.mjs` 的键盘分支只调用 DOM focus 后发送 Enter `keyDown/keyUp`；缺少原生 HTML 按钮激活所需的回车 `char`，也未核对窗口、webContents、document 与目标按钮的焦点。

此处重现了 T-103 已记录的同类驱动缺陷。采用仓库现有 `t103_picker_driver.mjs` 的输入合同：聚焦本测试窗口，核对四种焦点事实，按 Enter down → CR char（13）→ Enter up 发送。焦点不符时明确拒绝发送并记录诊断，不增加重试，也不改用 click 代替键盘。原鼠标折叠步骤保留。

新合同 [keyboard-proof-02.json](keyboard-proof-02.json) 为 **PASS**：

- `681fc0da5` 的原驱动失败：未聚焦且缺 CR char。
- 修后驱动通过，四种焦点反例均拒绝，且没有发送任何原生输入。
- 单独删除 CR char 的变异失败；单独移除焦点拒绝的变异失败。

这是驱动输入合同证据，不能替代真实 Electron 的激活效果。真实入口仍要求“键盘展开后 worker 可见”；没有放宽断言，另加“键盘操作从折叠状态开始”的断言和明确的 wait 诊断文字。

## 新编号交接

先运行 [RUN-OUTSIDE-COMMIT-02.sh](RUN-OUTSIDE-COMMIT-02.sh) 提交驱动修复。脚本沿用本 worker 的启动绑定和原自动尾注钩子，带 `git add --sparse`；要求当前分支 `exec/t109`、HEAD 为 `681fc0da5` 且没有其他已暂存改动，不 push。

再运行 [RUN-OUTSIDE-02.sh](RUN-OUTSIDE-02.sh)，仍跑完整原场景，包括红态、真实派发、侧栏零写入、两层折叠状态计数、键盘展开、聚焦和窄窗。输出新文件 `outside-02.json`，不覆盖首轮。此次尚未运行，因此整体继续报告 INCOMPLETE。
