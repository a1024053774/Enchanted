# T-101 / a1 准备交付结果（2026-10-19）

**INCOMPLETE**。主控已完成首轮试跑，旧候选扫描原有 413 处命中；按用户裁定 B 接入精确豁免后，该固定候选复核为 413 已豁免、0 未豁免。新增假值和换对象反例均被拒绝。正式完整备份、保留全部会话后的重新改写、正式验收、替换与 push 尚未完成，命令见 [HANDOFF.md](HANDOFF.md)。

**按用户裁定 B，公开历史包含 23 份 Codex 原生会话记录的正文。** 用户逐字选项为“B 豁免包括 H005,保留会话记录”，裁定记录为 `20261019T083541Z-ideation-answer-001`。H005 仍是不明内容，用户知情选择保留并精确豁免；扫描通过不等于认定它是假值。将来 ticket Resolution 由主控写明同一句公开正文说明。

## 范围与依据

- 目标：把 T-097/T-101 的瘦身发布操作准备成主控可审查、分阶段运行的脚本，保留 T-088 的摘要、小输入、原始证据与无校验值归档清单。
- 非目标：worker 不写外置盘、不安装 filter-repo、不替换真实 `.git`、不修改 workbench/测试/地图、不 push、不调用模型、不使用问题面板。
- 验收条件：实际历史瘦身、保留输入与 23 份原生会话、相关测试、映射、扫描与发布均取得真实证据，才能把整票上调为 PASS。扫描要求未豁免命中为 0；清单外任何新命中仍停止。
- 重要未知：正式新快照/迁移后是否出现新命中、动态小输入保留、正式旧哈希调用迁移和替换/发布结果。H005 的真实性未判断，用户批准的是精确例外。
- Ubiquitous language 沿用 ticket 的“备份、原始副本、候选、归档清单、映射表”；没有创造另一套门禁。Deep modules 的阶段边界为只读计划/核对、独立副本改写、本地替换、单次外部发布。完整 Tracer bullet 尚待主控在真实边界运行。

## 逐项验收对照

| T-101 条目 | 红态 | 绿态 / 反例 | 证据与结论 |
| --- | --- | --- | --- |
| `.git` 体积和 evidence 文件数 | 已保存瘦身前 du/count-objects、175,528 个 tracked evidence 文件；根目录 LICENSE 缺失，README 仍指旧门禁 | LICENSE 与中文 README 已补；瘦身后真实体积/文件数未产生 | [baseline.json](baseline.json)；整体 INCOMPLETE |
| 摘要和引用小输入保留、相关测试、project_map status | 动态 evidence 路径不能仅靠字面量证明；旧测试含直接 `git show OLD:PATH` | 派发 8 项、收件箱 17 项通过；原始失败也保留。完整候选和完整输入保留未验证 | [existing-checks-01.json](existing-checks-01.json)、[existing-checks-02.json](existing-checks-02.json)；INCOMPLETE |
| 外置盘未挂载不改写 | 隔离入口把普通 `/tmp` 目录作为未挂载盘 | 正常保护拒绝且文件树不变；删除 mount 检查的 mutant 被反例检出 | [local-checks-07.json](local-checks-07.json)；隔离反例 PASS，真实卸载/重挂未做 |
| 备份对象数不一致不替换 | 实际临时 Git 库，备份计数故意多 1 | 替换前拒绝、未产生 install intent；删除计数检查的 mutant 会走到安装，被反例检出 | 同上；隔离反例 PASS，真实备份核对未做 |
| 全保留历史凭据未豁免命中为 0 | 真实旧试跑的 37,159 个对象检出 413 处，原扫描为 NO_GO | 用户 B 清单精确匹配全部 413 处，未豁免 0；隔离反例 415 总命中、413 豁免、2 未豁免，NO_GO | [exemptions-red-01.json](exemptions-red-01.json)、[exemptions-checks-01.json](exemptions-checks-01.json)；旧候选复核 PASS，正式新快照仍 INCOMPLETE |
| 映射随机抽 5 个 | 尚未改写，无真实映射表 | 脚本在实际 filter-repo 后保存 commit/ref map 并随机抽 5 个；不伪造结果 | `slim_history.py verify`；INCOMPLETE |
| push 前后远端对比 | 执行主控给定远端完整旧 SHA；用户已批准固定 lease | 单独脚本核对 gh api/ls-remote，执行唯一指定 push，再核对；worker 未运行 | `install_publish.py publish`；INCOMPLETE |
| 凭据和全局配置 | H005 真实性未知，用户已知情批准精确例外 | 豁免清单只有对象哈希与 offset，没有原文；未写用户 ~/.claude、~/.codex 或读取其认证文件；未运行发布 | 清单外新对象/新位置不能继承豁免；INCOMPLETE |

## 用户 B 豁免与保留边界

[credential-exemptions-01.json](credential-exemptions-01.json) 精确列出 413 个对象哈希和 offset，含全部 (a) 379、(b) 5、(c) 29 及 H005；没有原文、前缀、通配符或按值规则。`TOKEN_RULES` 与裁定前逐项相同。03、04 和 06 共用这一扫描入口；对象或 offset 改变就不匹配，旧的“总命中为 0”判断已改为“状态 PASS 且未豁免为 0”，缺少新字段的旧收据不能代替新扫描。

真实旧试跑复核见 [exemptions-checks-01.json](exemptions-checks-01.json)：413 总命中、413 豁免、0 未豁免。反例只在 `/tmp` 新建的 bare Git 中借用原候选只读对象，不复制大 pack、不 checkout 整个仓库；新增一条合成假凭据，同时给已获豁免命中的源码对象追加换行。结果 415 总命中、413 豁免、2 未豁免：新假值被抓到，同一旧值/offset 换对象后也被抓到。原候选 refs 未变；报告不含原文。

[public-native-sessions-01.json](public-native-sessions-01.json) 固定 23 个精确保留路径及原版本。旧试跑实际只有 18 份，另 5 份被旧清单移出，不能把它当成完整保留验收通过。新版 02 对这 23 个路径优先保留，不受 run/fixtures 分类和大小门槛移出；03 拒绝旧的移出清单并核对全部历史版本，04 再复核。正式仍等 T-104/T-102 合入、所有人静止后，用新 run id 从 01 重做；恢复的 5 份或任何新/迁移对象出现清单外命中仍停止，不自动扩充豁免。

小型真实 Git + filter-repo 的保留验证、精确 offset 反例、去掉对象绑定的 mutant、移除会话保留的 mutant，见 [exemptions-unit-checks-01.json](exemptions-unit-checks-01.json)，均符合预期。原有隔离保护回归见 [local-checks-09.json](local-checks-09.json)。这些不替代正式新快照的完整验收。

## 隔离场景与失败保留

最新本地入口：

```sh
python3 -B evidence/2026-10-19-batch17/T-101/run_local_checks.py --report NEW_REPORT.json
```

原始记录 [local-checks-07.json](local-checks-07.json) 覆盖缺盘、备份对象数不一致、旧提交凭据、merge-only blob、保留 dirty/untracked 与并行 worktree、同路径多个历史版本、旧清单保护、CRLF/带标题/参考式 Markdown 链接；当前契约下回归见 local-checks-09。五个已知坏实现分别移除 mount 检查、移除对象数核对、恒空扫描、漏掉 merge diff、把归档替换成等长坏字节，均被反例检出。临时 Git 和文件系统是真实的；安装场景的候选和收据是夹具，不能据此宣称真实替换或发布通过。

`local-checks-01`～`04` 为较早候选的独立记录。`local-checks-05.json` 保留了新增 CRLF 链接场景的失败：参考式链接的匹配包含末尾 CR，目标未改写。已改为在 CR/LF 前结束匹配，`local-checks-06`、`07` 为后续绿态；05 的原始 fixture 保留，路径在该 JSON 的 artifact_root 中。另一次聚焦诊断现场为 `/private/tmp/a2a-t101-debug-q08_fsab`，未删除。

现有派发套件首轮 [existing-checks-01.json](existing-checks-01.json) 有 1 个 ERROR：`git init` 继承了调用者会话的 `core.hooksPath`，在 fixture 引用事务中找不到原 hooks 路径。没有把这个环境错误算作产品红态，也没有改测试。后续只在套件子进程移除 `GIT_CONFIG_*`，[existing-checks-02.json](existing-checks-02.json) 的派发 8 项与收件箱 17 项通过。精确 argv、输出位置和临时目录均在记录中；失败现场未覆盖。

原始 fixture 目前在本 session 新建的 `/tmp` 目录。执行主控先运行 `RUN-OUTSIDE-07-archive-local.sh`，按 T-088 归档到外置盘并把生成清单入库。仓库不含整个 fixture、数据库、bundle 或 tar 包。

## 状态检查与审查

[project-map-final.json](project-map-final.json) 与初始基线一样，均为 8 problems、0 stale living docs；缺的是稀疏 worktree 未检出的 findings 与 `.grilling` 文件，Git tree 中存在。没有修改地图或这些范围外文件，也没有把本地 status 写成通过。04 要求完整候选 status 真正通过。

Python 3.9.6 解析、所有 shell 脚本语法、UTF-8 无 BOM/无替换字符和 `git diff --check` 已检查。GPL 正文与下载的官方原件按字节一致；Synara 声明未改。

独立 behavioral-acceptance-review 为 **INCOMPLETE**：该 skill 要求新的只读审查上下文，用户本次明确禁止 worker 调用额外模型，因此由执行主控按其答复另派审查。本 worker 的自查不冒称独立审查。代码版本绑定以本目录与根 LICENSE/README 的最终提交及自动追加尾注为准。

替换前仍须处理的范围冲突和最小选项已逐项写入 HANDOFF；不使用问题面板。执行主控收到的是准备交付，不是已发布结论。
