STATUS: INCOMPLETE
SUMMARY: 宿主级独立内容与边界证据成立；真实用户入口和新增窗口检测能力尚未运行。按任务卡为 worker 自查，不冒充独立审查。
TARGET: scoped-repair.patch，相对 18c108fcaed1c4ecf51831f2272578a3b09427be；冻结验收未改。
EVIDENCE:
- 需求来自任务卡“点击未跟踪普通文本显示内容 diff”，包括有 HEAD 与 unborn，不以旧占位说明为期望。
- 实现前 host-red-C.txt 两个业务断言明确拒绝旧 C。local-01/host.txt 的 27 场景通过，随机内容预期来自原始文件，diff 全文来自独立 Git，不从产品模型生成答案。
- 实际 git-dir/common-dir 通过 git rev-parse 读取；linked worktree 的两处目录路径和文件原始字节前后核对，不计算 checksum。
- local-01/acceptance.txt 与 outside-safety.txt 通过，证明原有机械路径保持；它们不证明新的 UI 内容。
- 能力范围：文件读取与 Git 边界为 L2 已运行；异步选择、桌面交互为 L3 待运行；角色、编排门禁、模型判断、发布与外部写操作未改，不扩审这些轴。
FINDINGS:
- 无已复现的新产品缺陷。首轮空文件测试预期有误，已按独立 Git 实测改正，原失败保留。
COUNTEREXAMPLE:
- 旧 C 的未跟踪文本返回空 diff，拒绝于内容断言；空/二进制路径抛 Invalid diff base，拒绝于实际读取路径而非启动。
- unsafe-options 模拟接受多余参数，被拒于 Missing expected rejection；unsafe-paths 移除主进程文件边界，在真实夹具的越界目录符号链接处被断言抓住；force-text 强行输出二进制 hunk，被非文本断言抓住。见 local-01/summary.json 与各 mutation.json。
- 新窗口 no-untracked、no-resize、no-reset、stale-diff 和旧五项反例都已登记于 run_windows.py；尚未实跑，不能写成已拒绝。
LIMITATIONS:
- external-01 尚未生成；需主控从 HANDOFF.md 的单一命令运行旧 C、完整候选、所有限定反例和适用旧窗口回归。
- 鼠标事件通过 CDP Input，断言是实际可见表头/行几何；在运行成功前，源码中的事件调用与断言不构成交互证据。
- deferred 模式只控制真实读取结果的返回次序，不伪造文件结果；候选正常模式与该插桩模式分别记录，仍需实际运行来验证。
- 主控还须新 Test 包、新 Terra Computer Use 和常规测试、绑定最终候选的独立审查；旧通过报告不补这些缺口。
RULE:
- 未跟踪 diff 必须核对原始内容与独立 Git hunk，不能把说明文字当成内容成功；每个窗口反例必须命中指定业务断言，启动/CDP/清理失败记 INCOMPLETE。
