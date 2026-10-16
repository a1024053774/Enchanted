# T-082 审查结果协议修复

状态：离线解析与 relay 红绿 **PASS**；完整受控门禁回归已由主控运行 `OUTSIDE-COMMANDS-09.sh`，`outside-command-09-01` 三组全 **PASS**。随后新增报告节键检查的红绿也 **PASS**，证据 `protocol-section-01/`。本轮没有启动真实 Codex。

## 根因

真实回合 `real-codex-round-1-03` 的 `events-last.json` 中，唯一 `review_protocol_failed` 的 `details.details.raw` 是完整 JSON。身份字段齐全；`report` 是对象。原解析器在字段集合检查处要求恰好 12 个字段，本次输出还有 `review_requirements` 和 `report`，因此报 `review_request`，尚未运行 verdict、report 或身份值检查。

这是 T-082 的输出契约缺陷：`core.ts` 将 `review_requirements` 放进最终消息模板，原 `qualityProtocol.ts`/relay 没有接入它；模板要求报告，却没有给报告正文留字段。旧模板的原样回传本身也会触发拒收。不是 reviewer 缺身份，也不是对象型 report 本身无效。

## 修复

- 最终消息明确使用 14 个顶层字段，`review_requirements` 原样返回，`report` 为非空 JSON 对象。模板、解析器、relay、门禁请求类型和 `review.result` 使用同一契约。
- 解析器继续拒绝未知字段、缺身份、Markdown 包裹，以及字符串、数组、null 型 report。没有剥字段、抽取 JSON 或接受旧格式的兼容路径。
- 门禁保存原始结构化报告，只校验容器和请求格式，不验证模型判断正确、变异数量或变异是否理应失败。
- 两处受控 reviewer packet 生成器同步提供新字段；产品身份/候选/新会话核对没有放宽。

## 离线红绿

输入：`protocol-red-green-01/real-review-submit.json`，从上述 `raw` 逐字取出；来源 event seq 见 `source.json`。

命令（仓库根目录执行）：

```sh
node workbench/tests/test_t082_review_protocol.ts . evidence/2026-10-15-batch15/T-082/protocol-red-green-01/real-review-submit.json evidence/2026-10-15-batch15/T-082/protocol-red-green-01/red.json
```

修复前退出 1，`Error: review_request`。修复后同一入口/输入使用新输出名 `green.json`，退出 0。完整测试再使用 `green-relay.json`，10 项通过，包括真实 payload 原样保存、容器反例、严格 JSON 和真实 RequestRelay 的报告传递；relay 回调仅观察传入数据，不冒充业务验收。

完整测试对 `0dd00d09` 的原解析器再次运行，`red-full-test.json` 仍以 `review_request` 退出 1；`known-bad/` 只保存该解析器，不解全仓。

补充（主控 #47）：报告必须有“完成条件与变异检查”这一节属于机械事实，`reviewEvidence` 增加 `Object.hasOwn` 检查。缺节反例修前失败于 `T082-REPORT-SECTION`（未抛异常），修后按 `report.section` 拒收。键值为 null 的正例仍接受，证明只查存在、不判内容。完整离线协议/relay 测试现为 12 项，`protocol-section-01/green.json` 退出 0。

受控门禁回归命令：

```sh
bash evidence/2026-10-15-batch15/T-082/OUTSIDE-COMMANDS-09.sh
```

该脚本已通过，0 个真实回合；检查真实报告结构经 Stop→严格解析→relay→门禁入库→副本清理，以及 T-076 三项性质、严格 JSON 和 T-077 reviewer worktree 生命周期。真实历史回合仍是协议失败，离线绿态不能回填为历史门禁通过。
