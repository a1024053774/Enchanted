# T-073-1：Herdr 期任务卡、提交尾注与验收打分

状态：**INCOMPLETE，待主控关闭**。三项实现已交付，当前代码完成条件 1～5 与 7 项本地场景均通过；唯一一次独立审查为 FAIL，两项 P2 已修复并重验，按任务卡不追审，由主控审新增 diff。最终项目状态为 0 problems、0 stale；不把未经主控审查的修复写成 PASS。

依据：T-073 ready_rev: 1、本批任务卡、[执行主控决定 01](controller-decision-01.md)。决定 01 撤销默认 KEY 过滤及放行要求；实现没有 shell_environment_policy 覆盖。

开工 a2a main：5d9f03c669c1ded777524adc76a3f3834ae785cb；恢复执行时：39c067092c3dbaa570bf7456cef085dafe473fbc。首次独立审查目标：76e71f86f895e64f3eb5b7abedcfc08c7a62c98f。修复后的代码：93eb5ab2a63fad5fc80a59882755e99a2d9982e7；green03 启动记录的 launcher_commit 为该版本。主实现为 3cf85f4；真实 pane-run 返回值修复为 76e71f8；审查修复为 93eb5ab。

执行会话：Herdr s12-t073 / pane wF:p21，原生会话 01a12758-be0b-7e63-aa49-1c6beeb3ed6d。验证使用单独的 fixture task/attempt/session；本票按卡提交 a2a 版本、证据与 DONE 行，不冒称已完成本票的门禁 submit、验收或集成。

## 交付

- 任务卡模板对应 spec 第 2 节的 13 个字段，写明责任人与填法；Herdr 期手填，不提供生成/校验脚本。AGENTS.md 与三张角色卡仅增加模板链接，未改规则。
- scripts/launch-worker 创建自己的 Herdr pane、注入会话环境与三个 GIT_CONFIG_*、启动交互 Codex，追加 prepared、started/failed 记录。首次提交从 CODEX_THREAD_ID 取得原生会话号后追加绑定；完整 CLI argv、版本、模型、强度、角色卡版本、项目提交与启动器提交可读回，不改写旧记录。
- Git prepare-commit-msg 写入唯一一组 9 项尾注，再调用原钩子并传递失败。hooksPath 替换整个目录，因此其他标准 hook 名称共用转发实现，保留项目原 pre-commit 等检查。没有原可执行钩子时跳过，不重试或吞异常。
- scripts/score 追加 records/scores.jsonl。身份/CLI/模型/强度取启动记录，时间由脚本生成；Herdr 期的类型、复杂度与计数来自执行主控提供的事实 JSON，未添加门禁事件自动汇总。通过/升级必须有两项 0–3 分、各自理由、显式备注和七项检查计数；放弃的内容只有结果与理由，关联身份在外层保留。用户分另存，不覆盖执行主控分。
- scripts/dispatch 保持不变，继续只发文本。未增加依赖或构建；未使用内部盘替代构建缓存。

## 完成条件与当前证据

| 条件 | 结果 |
| --- | --- |
| 1：9 项尾注，启动记录和值一致 | PASS。green03 普通提交 73407e9f7750ddc3b6370a49fb8056cb2f85e2b6；normal-message.txt、env-probe.json、launch-records.jsonl、verification.json。 |
| 2：同会话 no-verify 仍为 9 项，原钩子多一行 | PASS。提交 db8a622ef649963fe4677aba83384c9762e5f6f4；no-verify-message.txt、completion-count.txt（主控精确命令输出 9）、original-hook-trace.txt（两行）。 |
| 3：普通终端无尾注且成功 | PASS。green03/plain-message.txt 无 A2A 行；真实 shell/Git 命令与退出码见 commands.jsonl。 |
| 4：完整打分、缺项拒收且文件不变、放弃无分 | PASS。当前代码的 score02-review-fixes 与 local04-review-fixes；此前首次放弃记录在 score01。新本地套件重新创建放弃夹具；实际 JSONL 的旧放弃记录不重复写入，重用情况在 verification.json 明示。 |
| 5：项目状态 | PASS。最终全仓 status 退出 0，0 problems、0 stale，见 status-final.txt；此前 T-074 索引 stale 的现场仍保留在 status-before-review.txt。 |
| 模板与路径 | PASS。13 字段、责任人及所有链接核对；独立审查也确认模板与链接通过。 |

真实边界：Herdr client/server 0.9.3，Codex 0.162.1，交互 CLI、Git 与文件。请求 gpt-6.1-sol / xhigh / service_tier="fast" / check_for_update_on_startup=false；供应商实际服务 tier 未核实。

## 红态、反事实与保留的失败

- red02：旧入口真实 Codex 提交 63b5b67d9fe1e66e888814e7a5d2e1f9777ac6e2 无尾注，红态成立。无害 KEY 变量默认保留的事实见 env-probe.json。初次 BLOCKED 报告保留在 RESULTS-blocked-01.md。
- red01：macOS 路径别名使信任项未匹配，停在启动确认；未批准、未进入模型回合。改用 /tmp 的真实路径，失败现场不覆盖。
- green01：产品把成功但空输出的 herdr pane run 当作 JSON，CLI 启动前失败；保留失败记录和夹具，0 个 turn，没有重试旧 attempt。red-pane-run-parent01 把修订后的测试放到 3cf85f4 的隔离副本，因相同错误失败；当前入口按该命令的真实空输出契约处理。
- local01：空提交的 amend 夹具漏 --allow-empty，Git 拒绝，这是测试缺陷，现场保留。local02 5/5，但其 Herdr 替身错误返回 pane-run JSON，不能证明真实启动。local03 修正替身后 5/5，green02 取得真实 Codex 绿态。
- mutant-missing-effort 首次因隔离源码缺 Git 根而失败，不算反事实。有效的当前修复前反事实在 mutant-missing-effort03：仅删 A2A-Effort，提交只有 8 项，断言拒绝。
- 唯一独立审查原文见 INDEPENDENT-REVIEW.md。它发现重复旧 A2A-Task 留下 10 项，以及 rejections 任意非空对象可被接受。review-red-duplicates01 与 review-red-checks01 通过公开 CLI/真实 Git 在冻结旧代码上复现，分别在 10≠9、错误接受 not_a_gate_check 处失败。
- 修复后 local04-review-fixes 7/7。钩子让 Git 识别并逐次删除既有受管尾注，再写唯一一组；打分核对七个固定检查项，缺项/未知项拒收。green03 用一个真实回合重新验证新代码，并证明重复旧身份被清除、Signed-off-by 保留。没有第二次审查，不借旧审查的局部 PASS 为修复背书。
- green02 首次写中文 prompt 的 stdin 编码错误与随后发文本前的拒绝也保留；改用 UTF-8 文件后只发送一次，未多耗模型 turn。

本地套件只替换 Herdr；Git、文件和产品 CLI 真实，不能替代真实 Codex/Herdr 证据。独立随机 task/session/native 输入与外部事实 JSON 进入公共入口，预期不从生产常量导入。

## Ticket 失败方式清单

| 失败方式 | 处理 |
| --- | --- |
| 默认过滤 KEY/SECRET/TOKEN | 前提由 red02 推翻，按决定 01 不加覆盖。未来过滤使尾注缺失时，完成条件的数量与启动记录核对会失败；后续门禁应拒收，不替未来门禁宣称通过。 |
| Git 元数据沙箱、钩子读写 | 真实隔离 home 只有 git add/commit 两条 allow 规则；Git 触发钩子，green03 两次提交成功。没有额外可写目录或替代工具绕过沙箱。 |
| 无原钩子、原钩子失败 | 无可执行原钩子则跳过；原 prepare 钩子 exit 19 时提交失败、HEAD 不变，local04 有证据。真实原钩子两次留下痕迹。 |
| 手动 unset | 缺 A2A_SESSION、身份不符时钩子拒绝。若移除整个 GIT_CONFIG_* 使钩子不执行，靠完成条件/后续门禁检出缺尾注；不声称环境不可被人修改。 |
| amend、rebase、merge | local04 通过真实 Git 三种场景，消息仍为 9 项且身份一致；重复旧尾注另有红绿与真实 Codex 证明。 |
| 打分并发、文件损坏 | 复用 record_io 的锁、校验和 fsync 追加；5 个并发写入保留，截断 JSONL 拒收且字节不变，local04 可重放。完整对象缺七项检查也被拒收。 |

## 用量、清理与范围

真实 Codex 共 **3 个模型 turn**：red02、green02、green03 各 1。red01、green01 0。原生事件累计 input 447,472（cached input 415,488）、output 2,234（含 reasoning 544）、total 449,706，见 usage-total.json 与各 run 的 usage.json。这是多次请求累计，不是单次输入长度，不换算费用。独立 reviewer 为 fresh-context 协作工具的 gpt-6.1-sol / xhigh，其用量未暴露，不计入上述 CLI 汇总。

五个隔离 CODEX_HOME 均已删除；只复制 auth.json，只信任本次夹具真实根，只有 git add/commit 两条规则，无 Codex hook。失败现场保留；成功 agent 确认 done 和提交已存在才关闭。只关闭自己的 pane，不改/重启 Herdr server，不写 ~/.codex、~/.claude、全局或仓库级 Git 配置，不碰 Synara fork 或工作台数据，不 push。

原生副本在本机 Git 忽略的 sessions 目录，认证副本不入证据或 Git。Git 夹具保留 /tmp 原目录及完整 tar.gz，不登记 gitlink。主控日志、T-074 文件及本批 dispatch/controller 日志未纳入本候选。

## 交主控的剩余事项

1. 按卡片要求审查 76e71f8 → 93eb5ab 的修复 diff；已有红绿与当前真实入口证据，但未经第二次独立审查。
2. 范围外 T-074 索引 stale 已上报（20261010T200034Z-worker:s12-t073-issue-001），由其他写入者核对后最终状态恢复为 0 stale；本 worker 未改他人文件。原环境 blocking issue 已由决定 01 解除。
3. 本 ticket 保持 open，待主控关闭与后续交付处理；不把当前 INCOMPLETE 上调。

原始命令、stdout/stderr、退出码在各 commands.jsonl；完整重放见 [REPLAY.md](REPLAY.md)。每次使用新 label/attempt，不覆盖失败或重复打分。

格式检查：源码/本报告及交付文档的范围检查通过。全量 staged diff 的 whitespace 检查返回 2，原因是原始 Git 消息自带末尾空行，以及冻结 patch 的空白上下文行；输出见 whitespace-raw-outputs.txt。这些证据按原字节保留，没有为通过格式检查删改现场。
