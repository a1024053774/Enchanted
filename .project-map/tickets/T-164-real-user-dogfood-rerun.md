---
id: T-164
title: T-155 重跑：修复后走到集成，并补 Codex worker 覆盖
type: build
status: closed
blocked_by: [T-157, T-158, T-159, T-160, T-161, T-162, T-163]
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

来源：用户 2026-10-23 逐字：“全部 7 条 + 3 条模型行为对策”（选项：切全部修复票）；报告 findings/2026-10-23-real-user-dogfood.md，执行主控 needs-decision 20261023T222913Z。

用户 2026-10-23 逐字：“重跑到集成走通,并补 Codex worker (Recommended)”（选项：修完后再跑一轮）。
沿用 T-155 的场景、边界与交付（Codex gpt-6.1-sol high 用 Computer Use，隔离 Electron，真实 Claude 用 claude-haiku-5-5），本轮目标：走到集成，且 worker 至少一个用 Codex。报告写入 findings/ 新文件，并与上轮逐条对照 F01～F07、M01～M04 是否消失。仍只报告，新缺陷经执行主控建缺陷级票并列出。完成后关闭 T-155 与本票。

通用要求：先在真实 Electron（隔离实例）复现并留红态证据，再修最小根因层；不加自动重试掩盖未知；使用 `CONTEXT.md` 术语；修改界面文案前读 `frontend-less-ai-tone`。

## Acceptance

- [x] 走到审查通过并集成（经门禁），含 Codex worker。
- [x] 上轮 7 条发现逐条复验结果。
- [x] 新发现的 Herdr 对照小结。

## 不做

范围外的问题经问题上报，不顺手改。

## 阶段记录（2026-10-24，票保持 open，INCOMPLETE）

- 用户 2026-10-24 选“B 现在开跑,应用内只用 1 个 Codex worker”（构思主控 answer 20261024T061431Z-001）。执行主控写好隔离生命周期（`evidence/2026-10-23-batch24/T-164/app_lifecycle.py`，应用内 Codex worker 用实例内隔离 CODEX_HOME），外层测试员 b24-t164（Codex gpt-6.1-sol high，Computer Use）。执行主控解释：用户限制的是 worker；产品规定 reviewer 与 worker 同 CLI 同模型，所以唯一 Codex worker 的独立审查也用 Codex，其余 Haiku（#82，已列给构思主控）。
- 外层测试员会话日志显示 Codex 周额度已用 97% 时执行主控叫停（周窗口 2026-10-30 14:15 EDT 重置）。走到：角色申请与批准、混合 CLI 并行派发（A Haiku、B 唯一 Codex、C Haiku）、人工介入、面板答复、任务视图分屏、C 交付与真实独审打回、B Codex 独审打回、手动 Reflect；**没有可合并审查、没有集成**。验收第 1 条未满足。
- 复验（`findings/2026-10-24-real-user-dogfood-rerun.md`）：F02、F03、F04、F06、F07、M03、M04 本轮已走范围内消失；F01、M02 仍在；F05、M01 未能复验（额度停点）。新发现 N01、N02。
- 执行主控事后只读核对实例事件，建缺陷级票：T-166（F01 残余：普通工作回合中输入，UPS 复用 prompt_id 被判重复、原 Stop 被拒）、T-167（N01：Codex 回执粘贴后提交未生效）、T-168（N02：只读审查窗格重叠）。
- 独立审查 agy INCOMPLETE（报告如实、未越界）。合并 4ec08032e。实例按 T-088 归档（`evidence/2026-10-23-batch24/T-164/t164-dogfood-xn9_oslt.archive.json`）；隔离 CODEX_HOME（含 auth.json 副本与应用内 Codex 原生会话）与 operator.json 按规则删除未归档。

## 阶段记录 2（2026-10-24 第二轮，票保持 open，INCOMPLETE）

- 用户换 5 小时限额的新 Codex 号（构思主控 answer 20261024T072734Z-001）；T-166～T-168 修完并经 agy 审查合入后直接开跑（实例基线 5380ebb28，任务卡 `evidence/2026-10-23-batch24/T-164/card-2.md`）。开跑前 `/status` 两窗口 100% left（`rerun-2/quota-start.md`）。执行主控答复测试员三问（`rerun-2/controller-answers.md`）：允许 B 同票回收后重派、任何时刻 1 个活跃 Codex worker。
- 09:02:52Z 外层测试员会话日志 5h 窗口已用 90%（周 14%），按卡停止；执行主控停掉实例 UI 与 daemon。走到：混合 CLI 并行、真实机械打回与修复重交、两种独审、面板答复、人工介入（工作中与交付后）、分屏、同后台重开、B 四次 revise→reclaim→重派、手动 Reflect。B 五次独审均需修复，A 回收被拒，C 未派发；**没有集成**。验收第 1 条仍未满足。
- 复验（`findings/2026-10-24-real-user-dogfood-rerun-2.md`）：T-167 真实 Codex 复验 17 次后续消息全部自行开始回合（0.098～0.188 秒），27 个 Codex 回合均 gpt-6.1-sol/high；N02（T-168）消失；F05、M01 本轮复验为消失；F01、M02、M03 仍在。新发现 N03（工作中输入被 CLI 并入当前回合后 worker 停在等待）、N04（应用内主控写的检查器依赖 Git，独审副本无法原样运行；属模型行为，主控 v3 起已改）。
- 执行主控核对归档实例与原生转录，建缺陷级票 T-169（N03：Claude Code 记 `absorbed_mid_turn`，T-166 仍等单独回合）。
- 独立审查 agy INCOMPLETE（报告有证据支撑、未越界；INCOMPLETE 指运行未集成）。合并 73b7e7873。实例按 T-088 归档（`t164-dogfood-x339g6dx.archive.json`）；隔离 CODEX_HOME 与 operator.json 删除未归档；测试员采集错误目录归档（`rerun-2/capture-error.archive.json`）。

## 阶段记录 3（2026-10-24 第三轮，票保持 open，INCOMPLETE）

- 应用内 Codex 类 worker 改用 `zcode/GLM-5.3-Flash` max（构思主控 answer 20261024T100325Z-001，用户：“我给里面接了zcode/GLM-5.3-Flash max, 你用他先替代 6.1sol 吧”）；GLM 做外层测试员没有走到第一条主控提示，用户选“等 09:11 换回 6.1-sol”，外层测试员 b24-t164d 为 gpt-6.1-sol high（任务卡 `evidence/2026-10-23-batch24/T-164/card-3.md`，实例基线 e3b14d27b）。GLM worker 表现与前两轮不可直接比较。
- 走到：A（Haiku）真实机械打回、T-169 双输入、三次 attempt、四次独审（一次 review_protocol_failed 后经界面重开干净审查），最后经门禁集成到实例 `dogfood` 分支 547b261a1（门禁库有 integration_intent、integrated 事件，执行主控独立核对）。B（GLM）首个 attempt 6 个实际回合均 GLM/max，修卡（N06：主控写出 allow/deny 交集）后重派的 B a2 因 Codex 账号路由超时启动即退出，reclaim 报 identity_conflict（N05），执行主控裁定为产品缺陷建 T-170，B 保留现场；C 未派发。**验收第 1 条“含 Codex worker 走到集成”仍未满足。**
- 复验（`findings/2026-10-24-real-user-dogfood-rerun-3.md`）：F01、F02、F03、F04、F05（已建会话）、F06、F07、M04、N02、N03（T-169）、N04 本轮走到范围内消失；M02、M03 仍在；M01 部分消失；N01 未单独复验。Claude 原生根回合 31，未到 60 上限；收尾时 5h 已用 51%、周 23%，未触发停线。
- 独立审查 agy INCOMPLETE（与交付自评一致；P3：界面重开的审查在 Reflect 显示“未归属”、主控终端 `MCP server 'lcu' not connected` Stop-hook 报错，来源均未查）。合并 7189f6437。实例按 T-088 归档（`t164-dogfood-0zw8tib0.archive.json`）；隔离 CODEX_HOME 与 operator.json 删除未归档。

## 阶段记录 4（2026-10-24 第四轮，PASS）

- GLM 上游（ZCode）封本机 IP 返回 405（`rerun-4/glm-route-probe.md`），构思主控 answer 20261024T162332Z-ideation-answer-001 选 A：应用内 Codex worker 与同 CLI 审查员用 gpt-6.1-sol high；外层测试员按用户“codex 只用于需要的地方”“用 sonnet 去做 computer use”改为执行主控起的 Claude Sonnet 子代理（lcu Computer Use）。任务卡 `card-4.md`，实例基线 aacc1bb81（含 T-170）。
- 走到：项目终端启动应用内主控（haiku）→ 界面批准角色申请 → 建卡派给 Codex worker → a1 交付被 oracle_failed 拒（主控把完成条件写成主仓库绝对路径，N08）→ revise、普通 reclaim、重派 a2 → 交付、verify 通过、新开同 CLI 独立审查“可合并”→ 打分 → 经门禁集成，demo-repo main 前进到 7ce91a867（尾注 codex-cli 0.164.0 / gpt-6.1-sol / high）。
- 执行主控独立核对：门禁库 demo-repo+T-1 有 review_result #208、integration_intent #247、integrated #281、score_recorded #282；隔离 CODEX_HOME 原生日志 7 个 turn_context 全为 gpt-6.1-sol/high；Claude 应用内回合 6（haiku）。结束读数 5h 已用 54%、周 24%，未到 70% 线。N05/T-170 的启动失败路径本轮没有出现，未在真实环境复验。
- 新发现 N07（worker 的 blocking 问题在主控修订重派后仍悬在问题页，没有关联提示）留构思主控判断是否属体验问题；N08 为主控卡错误（模型行为）。
- 独立审查 agy PASS（P3：RESULTS 交叉引用把 N07 误写成 N01）。合并 ebb0e4725。实例按 T-088 归档（`t164-dogfood-dc_5rakx.archive.json`）；隔离 CODEX_HOME 与 operator.json 删除未归档。

## Resolution

2026-10-24 PASS。验收第 1 条由第四轮满足（Codex worker 任务经同 CLI 独立审查通过并经门禁集成）；第 2 条见第一至三轮逐条复验（F01～F07、M01～M04 及 N01～N06）；第 3 条见各轮报告的 Herdr 对照。四轮报告：`findings/2026-10-24-real-user-dogfood-rerun.md`、`-rerun-2.md`、`-rerun-3.md`、`-rerun-4.md`。按本票“完成后关闭 T-155 与本票”一并关闭 T-155。
