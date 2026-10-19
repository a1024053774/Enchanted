# T-101 / a1 准备交付结果（2026-10-19）

**INCOMPLETE**。README、GPL-3.0、分阶段脚本及本地验证已交付；真正的备份、历史改写、全历史扫描、随机哈希映射核对、主仓库替换与 push 尚未运行。执行主控的顺序和每条命令见 [HANDOFF.md](HANDOFF.md)。

## 范围与依据

- 目标：把 T-097/T-101 的瘦身发布操作准备成主控可审查、分阶段运行的脚本，保留 T-088 的摘要、小输入、原始证据与无校验值归档清单。
- 非目标：worker 不写外置盘、不安装 filter-repo、不替换真实 `.git`、不修改 workbench/测试/地图、不 push、不调用模型、不使用问题面板。
- 验收条件：实际历史瘦身、保留输入、相关测试、映射、扫描与发布均取得真实证据，才能把整票上调为 PASS。脚本存在不等于操作完成。
- 重要未知：全历史实际凭据命中情况、构造路径的小输入保留是否完整、旧哈希调用的迁移、实际 filter-repo 版本与行为、真实替换和发布结果。
- Ubiquitous language 沿用 ticket 的“备份、原始副本、候选、归档清单、映射表”；没有创造另一套门禁。Deep modules 的阶段边界为只读计划/核对、独立副本改写、本地替换、单次外部发布。完整 Tracer bullet 尚待主控在真实边界运行。

## 逐项验收对照

| T-101 条目 | 红态 | 绿态 / 反例 | 证据与结论 |
| --- | --- | --- | --- |
| `.git` 体积和 evidence 文件数 | 已保存瘦身前 du/count-objects、175,528 个 tracked evidence 文件；根目录 LICENSE 缺失，README 仍指旧门禁 | LICENSE 与中文 README 已补；瘦身后真实体积/文件数未产生 | [baseline.json](baseline.json)；整体 INCOMPLETE |
| 摘要和引用小输入保留、相关测试、project_map status | 动态 evidence 路径不能仅靠字面量证明；旧测试含直接 `git show OLD:PATH` | 派发 8 项、收件箱 17 项通过；原始失败也保留。完整候选和完整输入保留未验证 | [existing-checks-01.json](existing-checks-01.json)、[existing-checks-02.json](existing-checks-02.json)；INCOMPLETE |
| 外置盘未挂载不改写 | 隔离入口把普通 `/tmp` 目录作为未挂载盘 | 正常保护拒绝且文件树不变；删除 mount 检查的 mutant 被反例检出 | [local-checks-07.json](local-checks-07.json)；隔离反例 PASS，真实卸载/重挂未做 |
| 备份对象数不一致不替换 | 实际临时 Git 库，备份计数故意多 1 | 替换前拒绝、未产生 install intent；删除计数检查的 mutant 会走到安装，被反例检出 | 同上；隔离反例 PASS，真实备份核对未做 |
| 全保留历史凭据 0 命中 | 合成 key 与 auth.json 仅出现在旧提交、当前 tree 已删 | 扫描检出历史 key/auth 副本；空扫描器 mutant 被拒；清洁临时库为 0。报告无 key 原文 | 同上；真实全历史扫描未做，INCOMPLETE |
| 映射随机抽 5 个 | 尚未改写，无真实映射表 | 脚本在实际 filter-repo 后保存 commit/ref map 并随机抽 5 个；不伪造结果 | `slim_history.py verify`；INCOMPLETE |
| push 前后远端对比 | 执行主控给定远端完整旧 SHA；用户已批准固定 lease | 单独脚本核对 gh api/ls-remote，执行唯一指定 push，再核对；worker 未运行 | `install_publish.py publish`；INCOMPLETE |
| 凭据和全局配置 | 全历史风险尚未知 | 本次交付文件的固定模式检查 0 命中；未写用户 ~/.claude、~/.codex，也未读取其认证文件；未运行真实发布 | 本次局部检查不替代全历史；INCOMPLETE |

## 隔离场景与失败保留

最新本地入口：

```sh
python3 -B evidence/2026-10-19-batch17/T-101/run_local_checks.py --report NEW_REPORT.json
```

最终记录 [local-checks-07.json](local-checks-07.json) 覆盖缺盘、备份对象数不一致、旧提交凭据、merge-only blob、保留 dirty/untracked 与并行 worktree、同路径多个历史版本、旧清单保护、CRLF/带标题/参考式 Markdown 链接。五个已知坏实现分别移除 mount 检查、移除对象数核对、恒空扫描、漏掉 merge diff、把归档替换成等长坏字节，均被反例检出。临时 Git 和文件系统是真实的；安装场景的候选和收据是夹具，不能据此宣称真实 filter-repo 或发布通过。

`local-checks-01`～`04` 为较早候选的独立记录。`local-checks-05.json` 保留了新增 CRLF 链接场景的失败：参考式链接的匹配包含末尾 CR，目标未改写。已改为在 CR/LF 前结束匹配，`local-checks-06`、`07` 为后续绿态；05 的原始 fixture 保留，路径在该 JSON 的 artifact_root 中。另一次聚焦诊断现场为 `/private/tmp/a2a-t101-debug-q08_fsab`，未删除。

现有派发套件首轮 [existing-checks-01.json](existing-checks-01.json) 有 1 个 ERROR：`git init` 继承了调用者会话的 `core.hooksPath`，在 fixture 引用事务中找不到原 hooks 路径。没有把这个环境错误算作产品红态，也没有改测试。后续只在套件子进程移除 `GIT_CONFIG_*`，[existing-checks-02.json](existing-checks-02.json) 的派发 8 项与收件箱 17 项通过。精确 argv、输出位置和临时目录均在记录中；失败现场未覆盖。

原始 fixture 目前在本 session 新建的 `/tmp` 目录。执行主控先运行 `RUN-OUTSIDE-07-archive-local.sh`，按 T-088 归档到外置盘并把生成清单入库。仓库不含整个 fixture、数据库、bundle 或 tar 包。

## 状态检查与审查

[project-map-final.json](project-map-final.json) 与初始基线一样，均为 8 problems、0 stale living docs；缺的是稀疏 worktree 未检出的 findings 与 `.grilling` 文件，Git tree 中存在。没有修改地图或这些范围外文件，也没有把本地 status 写成通过。04 要求完整候选 status 真正通过。

Python 3.9.6 解析、所有 shell 脚本语法、UTF-8 无 BOM/无替换字符和 `git diff --check` 已检查。GPL 正文与下载的官方原件按字节一致；Synara 声明未改。

独立 behavioral-acceptance-review 为 **INCOMPLETE**：该 skill 要求新的只读审查上下文，用户本次明确禁止 worker 调用额外模型，因此由执行主控按其答复另派审查。本 worker 的自查不冒称独立审查。代码版本绑定以本目录与根 LICENSE/README 的最终提交及自动追加尾注为准。

替换前仍须处理的范围冲突和最小选项已逐项写入 HANDOFF；不使用问题面板。执行主控收到的是准备交付，不是已发布结论。
