# T-053 独立审查原结论与修复记录

以下是一次 fresh-context、只读审查的原结论。对象为旧候选 `251ce27694d28aef54079ab8c1bc691e7d5a4b0b`，未改写其 FAIL。

STATUS: FAIL
TARGET: 251ce27694d28aef54079ab8c1bc691e7d5a4b0b — scripts/inbox、acceptance/test_inbox_e2e.py；T-053 ready_rev 1
EVIDENCE:
- 审查者依据 ticket/spec/角色卡独立推导预期，未读取实现者对话、ORACLE.md、规划或理由。
- 冻结候选原套件复跑 9/9 通过；独立探针 13 项中 10 项通过，3 项答复元数据检查失败。
- 陌生 Unicode 正文、角色卡优先打印、错误角色 ack 拒绝、正确 ack 后隐藏且原文件不变、手写 inline lists、用户状态边界、明确 reason/basis、ready 依赖通过。
- 缺少元数据的 answer 发送退出 0，但文件没有 certainty/bundle_id；显式传 --certainty relayed --bundle-id sentinel-bundle 退出 1，错误为 unrecognized arguments。
- 独立探针进程本身退出 0，业务失败以 checks.json 的三个 false 为准，未把进程退出当作通过。
- 独立原始目录：/private/var/folders/7v/58svbpnj5k91zdnm5zggb38h0000gn/T/a2a-t053-independent-277po12t；完整冻结源码、输入、夹具、命令和原始输出已保存于 independent-review-raw.tar.gz。
FINDINGS:
- [P1] scripts/inbox:202 — answer 发布缺少 certainty: relayed 和 bundle_id；参数声明无法接收。契约为 spec 第 3 节 Herdr 期、spec 第 5 节 answer 行、roles/ideation.md。修正应在同一 send 路径完成。
- [P2] scripts/inbox:125 — task/thread/turn/message/request/input/commit 合法引用会被当作本地文件并拒绝。契约为 spec 第 2 节共用信封。
- [P2] scripts/inbox:35 — created_at 的合法非零时区偏移被拒绝。契约为 spec 第 2 节；应接受带时区的 ISO 时间并归一化 UTC。
COUNTEREXAMPLE:
- 旧候选本身是答复字段反例：可通过原 9 项测试，但被独立探针捕获。
- seconds-only 和 ack-sender-ignored 两个 mutant 均被对应业务断言拒绝。
LIMITATIONS:
- 引用类型和时区发现来自静态可达分析，审查者没有扩大独立探针范围去运行它们。
- 真实只读记录使用 worker 提供的原始记录，审查者未操作生产收件箱。
- 本次验证仅为 CLI/本地文件系统；不覆盖模型理解、跨会话唤醒、Synara UI 或外部应用。
RULE:
- 没有认定这些发现属于项目已登记的重复失败类别。

## 修复后的证据

三项均在同一入口修复，代码提交为 `a4d502407e5d593300f84b2b82f899d0624f0949`。

- 先运行新增端到端用例：`review-red-01` 捕获答复元数据和引用类型失败；`review-offset-red-01` 单独捕获时区失败。
- 修复后套件 `review-green-final` 为 12/12；原独立探针的字节未改，重放为 13/13，见 independent-replay.json。
- 两个 mutant 在修复后候选上再次被拒绝；真实 ready/list 的 Git 状态和地图字节再次前后一致。
- 按任务书仅做了一次 fresh-context 审查。修复后没有重新宣布该审查 PASS，也没有第二次全面审查；修复验证来自新增用例及原独立输入的重放，最终关闭由执行主控处理。
