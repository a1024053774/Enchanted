# T-095-1：锚点规则候选与第 4 回合交接

**INCOMPLETE。** 按主控 #115 / 主控 #8 的新规则，三份真实原件的 11 个阶段回归和串行 85 项入口检查通过；新的第 4 个独立真实探针尚未运行。skip 后缺少解决事件的已知限制仍在，不把 unknown 写成已解决或正常回落成功。未 submit、独立审查、验收或集成。

本候选提交后冻结，完整 SHA 见交付末行。task T-095 / attempt a1 / session `983db526-dfe8-473a-857b-b3f2af0af582` / launch `launch-4b1abba18e87460da9cbacec04905c78` / ready_rev 1；基线 `3c9016d0230223945f0e16543b230a047c2ad032`。上一冻结的真实 INCOMPLETE / NO_GO 报告逐字保存在 [FROZEN-866166b6.md](FROZEN-866166b6.md)；原始 run、投影 JSON、退出码和人工操作均未修改。

## 当前规则

完整合同见 [UI-STRUCTURE.md](UI-STRUCTURE.md)。等待正判只使用屏幕锚点与 Herdr blocked，原生会话身份、记录完整性和读取前后稳定性仍先核对；原生日志不再作为额外的等待正判条件，也不比较问题数量。

- 折叠：最后 12 个非空可见行内，忽略行首空白，存在 `? N question` 或 `? N questions` 的正整数计数前缀。前缀后任何内容均忽略，包括年龄后缀；不校验标题、队列行、回答快捷键、输入框或底栏。
- 展开：同一可见行同时出现 `⌃] skip` 和 `⇧→ main prompt`。上方残留输出、标题、enter、选项列表和后续无关文本均不参与判定，两标记不能分处两行。
- visible 与 detection 都存在任一锚点，且读取前后 Herdr `agent_status=blocked`，才输出 `waiting_controller_answer` / “等待主控回答”，附 worker / launch / pane / native session。两次的形态、计数和无关内容可以不同。
- 只有锚点、只有 blocked，或两份读屏对锚点存在与否不一致，均 unknown；`conflicts` 记录各屏幕是否有锚点、Herdr 原值和保守决定。blocked 配空屏也记录缺少屏幕印证。

原生日志仍只读启动记录绑定的 native UUID，不按文件名猜；身份或原生记录不可核对、不完整、读取中状态改变时仍 unknown。两边均无等待信号时，普通 working / idle 使用原有活动行、输入框、底栏和原生无 pending 的依据；原生 pending 时仍 unknown。`accepted:true` 不解决问题，普通同 turn 输出、新 turn 或 item 完成都不猜作答案。

旧的标题 / 整屏 / 选择编号校验，以及“原生 pending + blocked + 普通活动画面就判等待”的路径已删除。唯一入口仍是 `scripts/agent-status`；未改 dispatch、launcher、Herdr、工作台、gates、地图或全局配置，原生读取模块也未改。没有新增产品状态存储或自动回答。

## 三份原件回归

输入参与了修改，以下只算离线回归，不能替代新独立真实验证。索引只在临时夹具中重建，原始 worker / launch / native UUID / cwd 保留，原生日志按各投影字节截止点复制；没有补入合成答案。

| 原始 run | 折叠 / 展开 | skip 后 | 范围与判断 |
| --- | --- | --- | --- |
| red-20261018T110936Z-f4d263d1 | unknown / 等待 | unknown | 折叠屏幕只有 Working、没有锚点；按新规则是 blocked 单边成立，必须 unknown 并留冲突。展开有同条双标记。原 run 未保存 launches，夹具从归档 start 回复及已核对的 native header 重建绑定；不补称当时已有该启动记录。 |
| green-20261018T125458Z-76e72ee1 | 等待 / 等待 | unknown | 两形态都有锚点且 blocked；关闭无解决事件，保守 unknown。 |
| green-independent-20261018T131803Z-9e55a235 | 等待 / 等待 | 即时、30 秒、60 秒均 unknown | 年龄后缀与前置输出不再影响锚点识别；延后日志仅有 sleep 返回和继续执行，没有问题解决信号。 |

这不是把 red 折叠强判成等待。主控明确要求两来源印证，缺少锚点时不能用原生 pending 补足。2026-10-17 T-094 的 working 仍只有执行主控 / 用户报告；2026-10-18 三次真实运行的面板阶段均为 blocked，原 ticket 的 working 红态仍未复现。

实际历史投影保持原样：首轮 green 和 green-independent 的现场状态分别仍是三个 unknown、五个 unknown。新表是当前代码对原件的回归结果，不能改写原版本的失败结论。

## 检查与保留的失败

详情见 `anchor-checks.json`，完整输出与夹具见 `anchor-repair.archive.json` 的源目录。所有报告均新建；旧失败没有覆盖。

| 范围 | 结果 |
| --- | --- |
| 新合同下的修前原件回放 | **FAIL，11 项中 3 项失败**：red 无锚点折叠被旧路径错判等待；green-independent 两形态仍 unknown。源码固定为上一冻结 866166b6；这是新合同反例，不补称原始 working 红态。 |
| 修后原件回归 | **PASS，11 项**；最终串行报告也覆盖全部 11 项，矩阵如上。 |
| 最终入口合同 | **PASS，85 项，串行**，`contract-serial.json`。覆盖双来源组合、任意后缀、无标题 / 无选项 / 无底栏、残留输出、不同计数、同条控制标记、历史计数不在底部、读取与身份异常、普通 working 和保守回落。 |
| 单边放行坏副本 | **被拒绝**。把锚点 AND blocked 改成 OR，只有锚点和只有 blocked 两例都错判等待，被业务状态断言拒绝；`one-sided-mutant.json` 保留代码和原件。 |
| 空屏冲突记录 | 修前已返回 unknown 但缺少冲突，专项 FAIL 保留；修后补齐，专项与最终合同 PASS。没有改普通 working 的不可读保护。 |
| 第 4 回合脚本接线与凭据隔离 | **PASS，0 个真实探针根回合**。显式假 Herdr / Codex，核对总预算 4、单次提示、无代按键、延后只读采集、关闭自建 pane、删除隔离 HOME，及假凭据 canary 不入归档。 |
| 新的独立真实验证 | **NOT_RUN**。只能由主控在冻结后运行第 4 个根回合，不能用上述回归上调。 |
| 项目地图 | `anchor-map-status.txt`：0 problems / 0 stale living docs。 |

并发末轮有两份额外 FAIL：`contract-final.json` 的 working-command-context 与 `archives-final.json` 的 red-expanded，在同一时刻的第一个假 Herdr get 超过原有 3 秒期限，实际按保护规则返回 `herdr_timeout` / unknown。根因未确定，完整失败与夹具保留；未改生产期限、未改 Herdr。随后同期限串行 85 项全部通过，不把此前 FAIL 改成 PASS，也不宣称测试环境抖动已解决。

零模型复现（报告路径必须新建）：

```sh
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_agent_status.py --archives-only --report <新报告路径>
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_agent_status.py --report <新报告路径>
```

## 归档与第 4 个独立探针

主控 #115 指定再运行 1 个根回合，累计最多 **4 个**。前三个已经用完，本轮 worker 没有启动真实探针。第 4 回合沿用固定提示、Codex 0.163.0、gpt-6.1-sol / xhigh / 请求 fast、240 秒总期限；只复制 auth.json 到隔离 HOME，不写全局配置，不让模型跑命令或改文件，不重试、不 resume、不自动回答。完整计划见 `anchor-probe-plan.json`。

本次详细输出与失败夹具共 **732 文件、6,886,506 字节**，尚待沙箱外复制。包中也包含前轮尚未复制的 56 文件派生读回，原路径仍保留；原始真实 run 本来就在外置盘。外置盘未挂载、源变化或目标存在均停止，不覆盖。主控在本 worktree 的沙箱外 Herdr 终端先归档，PASS 后运行探针：

```sh
python3 evidence/2026-10-16-batch16/T-095/archive-offline-evidence.py --manifest anchor-repair.archive.json --apply
python3 evidence/2026-10-16-batch16/T-095/controlled-panel-probe.py --approve-one-root-turn --phase green-anchor-independent
```

操作与上轮相同：SHELL_READY、CODEX_IDLE 后，只观察默认折叠并输入 COLLAPSED，**此前不展开或先展开再折叠**；CAPTURED collapsed 后 Shift+← 展开并输入 EXPANDED；CAPTURED expanded 后仅按界面提供的 Ctrl+] skip，再输入 CANCELLED。即时采集结束后，脚本在 30 秒和 60 秒目标点只读采集，不需任何人工输入，最后关闭自建 pane、保存绑定原生记录、删除隔离 HOME 与空 scratch。

脚本采集完成仍打印 INCOMPLETE，不自动宣布功能通过。新数据读回后再冻结并发独立审查；当前 `REVIEW-REQUEST.md` 明确为上次失败冻结的历史请求。`T-095 READY <sha>` 只交付当前冻结代码与脚本，不表示整票 PASS。
