# T-101 / a1 执行交接（2026-10-19）

状态：**INCOMPLETE**。主控已完成初次试跑；用户 B 批准旧扫描的全部 413 个精确定位，当前旧候选已复核 413 豁免、0 未豁免。worker 没有写外置盘、替换真实仓库、push 或调用模型。正式保留全部会话后的新运行、完整验收和发布仍待执行。

**按用户裁定 B，公开历史包含 23 份 Codex 原生会话记录的正文。** 用户逐字选择“B 豁免包括 H005,保留会话记录”，见 `20261019T083541Z-ideation-answer-001`；包括已知不明内容 H005。ticket Resolution 由主控写明同一句。该决定不授权清单外的新命中。

身份：task `T-101`，attempt `a1`，session `8465b431-08a5-4077-a6b5-1d43761650e3`，launch `launch-7389a5e942e54c0b994eff30a502e972`，起点 `803e6cf69abbd7727c3694a446a52eb5940ddf2e`。按执行主控本 session 的答复，本票在 Herdr 期以 `exec/t101` 带钩子尾注的提交交付，没有门禁 state/fence/spec_rev，不调用新工作台 submit。

## 执行前提

1. 执行主控审查本候选并派独立只读审查。本 worker 没有启动额外模型，不能代称独立审查通过。
2. **正式运行**须等待 T-101/T-102/T-103/T-104 及其他当前 worker 的交付集成到旧 main，回收 worker，暂停所有会写仓库/records/inbox 的进程。正式备份、核对和替换期间保持静止；不修改/重启用户 Herdr server。下文的 `--trial` 是明确受限的提交快照试跑，不是完整原仓库备份。
3. 确认 `/Volumes/WD-Elements` 挂载；大文件、工具、缓存和副本只写外置盘。08 的隔离反例借用原候选只读对象，不复制大 pack、无整仓 checkout，可显式写新建的 `/tmp` 小目录；它不是正式备份。正式替换仍须内置盘至少有新 Git 体积加 256 MiB，旧 Git 保留不立即回收占用。
4. 本次启动观察到 main 已前进到 force 裁定提交 `73f40bd04`。脚本在执行时重新备份当前 refs，不固化旧起点来覆盖新 main。

## 已授权的哈希迁移与待核对输入

执行主控 #7 已裁定：在改写后的候选里，按 commit-map 机械替换测试/脚本的哈希字面量，单独提交，不改断言和逻辑。worker 当前 worktree 不改这些调用方；迁移由 03b 在正式候选中完成。例如：

- `workbench/tests/test_t096_restart_cleanup.py:129`、`:145`：`git show 10c0168db:...`、`git show da6a095fc:...`。
- `workbench/tests/test_t096_process_probe.py:54`、`:62`：`git show 958ede25f:...`、`git show da6a095fc:...`。
- 还有动态拼接 revision 的测试，静态探针不声称能穷尽。

迁移范围为 `acceptance/`、`scripts/`、`workbench/tests/` 中的 Python/JS/TS/shell 源文件；ticket、evidence、records 里的引用不变。完整或短哈希必须在 commit-map 中唯一解析；不唯一或目标已删除时停止，不猜测。只有匹配的哈希字节可替换，换行、BOM、断言和其他字节保持。动态拼接靠同套件运行发现，失败就停止，不用旧对象或 replace refs 让旧历史重新进入候选。

迁移前后必须使用同一份相关套件清单，并显式覆盖迁移计划里的每个调用方。这里不能把 `commit_*.py` 等操作脚本直接当测试执行；脚本不会猜测未知测试入口。`hash-migration-suites.example.json` 只提供六个 T-096 入口示例，**不是完整覆盖清单**。03b 遇到未覆盖文件，在改动调用方前停止并列出它们；主控据 `hash-migration-plan.json` 配齐已核对、无模型调用的相关套件后继续。

构造路径读取的小输入也须主控审查：`plan.json` 的 `possible_inputs_to_review` 专门列出可能遗漏的输入。`keep-paths.txt` 明确保留 T-088 点名的三个文件，另保留小 Markdown、摘要、命令脚本与静态字面量直接引用的小文件。静态分析不能证明动态路径都被覆盖；不得把 plan 生成成功当作小输入保留验收通过。必要时补 `keep-paths.txt`，使用全新 run id 重新走备份/清单，保留旧 run。

## 依次运行

从已合入本交付的完整主仓库运行，以下变量只用于当前 shell。脚本不申请权限升级，不自触发下一阶段。

```sh
cd /Users/luckye/Documents/Code/a2a
t101=evidence/2026-10-19-batch17/T-101
sh "$t101/RUN-OUTSIDE-07-archive-local.sh"
```

07 把仍存在的本地夹具复制到外置盘，核对文件数/字节数，不删原件；缺失源逐项写入 `*.missing-<本次编号>.json`，没有 archive/bytes 的虚假值，也不为它生成已归档清单。其余有效源继续处理。已有合法清单及归档核对后记为 `already_archived`；已有部分目标但没有清单则停止，保留现场。每次另存 `archive-local-<本次编号>.json` 总结。**rc 0 只表示遍历完成；有缺失时状态仍为 INCOMPLETE。** 主控审查这些文本记录并入库。

## 当前已完成的旧试跑：精确豁免复核

原 03 的 NO_GO 报告保留，不覆盖。`credential-exemptions-01.json` 只有用户批准的全部 413 个 object+offset，含 H005，不保存原文，也没有宽泛目录/模式/前缀豁免。对象或 offset 变动即为未豁免新命中；扫描模式未改。03、04、06 使用同一个扫描函数，均按未豁免数量判定。

从更新后的 worker 路径可重放真实候选复核：

```sh
cd /Users/luckye/Documents/Code/a2a-wt-t101
t101=evidence/2026-10-19-batch17/T-101
sh "$t101/RUN-OUTSIDE-08-recheck-exemptions.sh" trial-20261019-01
```

默认在外置盘该 run 的 `credential-exemptions-recheck-01/` 写结果，已有目录即拒绝覆盖；需要再次重放时显式传一个全新 `--output-dir`。08 先核对原候选 413 总命中、413 豁免、0 未豁免，随后在独立 bare Git 内新增合成假值，并给已豁免对象追加换行；两者必须作为未豁免命中被拒绝。原候选不变，反例不推送。重放依赖保留的原候选对象，不能把这个共享对象反例当正式仓库。

worker 已在只读外置盘候选 + 新建 `/tmp` 小目录上取得真实结果，见 `exemptions-checks-01.json`：37,159 个对象，绿态 413/413/0；反例 415 总命中、413 豁免、2 未豁免，NO_GO，原 refs 不变。原候选仍只有 18/23 份会话，不能继续用于正式替换。另 5 份在旧移出清单中，原现场保留；新版 02/03/04 已显式保留并核对 23 个精确路径与全部版本。

## 后续若需新的探索性试跑：仍到 03 为止

00 已成功，不重复安装。`trial-20261019-01` 已使用，不再重复 01～03。若另做探索性运行，由主控选择全新 id，按 01 `<新 id> --trial`、02、审清单、03 的原流程；保留正在变化的日志、inbox 与 worker 原件。

01 的 `--trial` 不复制会变化的整个原工作区；它先创建并 verify bundle，以 bundle 实际列出的 refs 创建独立 mirror，后续 02/03 只读取该固定副本。未提交原件不动，活跃 worker 可继续提交；前后观察到的变化写入 `trial-observations.json`，不要求它们相等。`backup.json` 明确为 `mode=trial,status=INCOMPLETE`，不声称完成正式目录/对象备份验收。此模式不因**仅存在** dirty/inbox/活跃 worktree 而拒绝，也不把其未提交内容混进试跑历史。实际 Git/I/O 错误仍须停止。

03 如有任何未豁免命中即停止，报告只含位置/类型及是否精确豁免；不会因值相同或带 fake 字样自动放过。未豁免为 0 才生成 prepared 及映射/清单。试跑**不运行 03b、04、05、06**；这些入口拒绝 trial marker。正式运行仍必须等 T-104/T-102 合入、全员静止，以全新 run id、不加 `--trial` 从 01 重做。

## 正式运行后续

顺序保持不变。先合入本交付及 T-104/T-102、确认所有人静止，再用全新 run id 从 01 开始。以下示例 `run-20261019-01` 若已存在须换新 id，不复用旧 trial：

```sh
cd /Users/luckye/Documents/Code/a2a
t101=evidence/2026-10-19-batch17/T-101
sh "$t101/RUN-OUTSIDE-01-backup.sh" run-20261019-01
sh "$t101/RUN-OUTSIDE-02-plan.sh" run-20261019-01
```

00 只在工具尚不存在时运行一次：独立 venv 为 `/Volumes/WD-Elements/a2a-backup-pre-slim/tools`，版本、已安装帮助与官方文档保存于同根 `tool-docs/`。失败现场不覆盖，主控诊断后再定如何继续；已成功安装则核对 `installed.txt` 后跳过 00。

01 保存 `all.bundle`、主仓库整体副本、每个 linked worktree 的整体副本、对象数与 refs/工作区状态。源与目录副本核对所有对象数；bundle 检查所有 refs 可达对象数，另做 bundle verify。目录复制核对文件名、文件数、字节数和链接目标；不计算校验值。原始备份不作改写目标，后续只读保留到用户同意删除。

02 生成外置盘上的 `plan.json`、`remove.txt` 和摘要。**审查 remove、keep、possible_inputs_to_review 后**，再执行：

```sh
sh "$t101/RUN-OUTSIDE-03-rewrite.sh" run-20261019-01
```

03 先归档移出路径的每个历史 blob 版本（包括 merge resolution），核对归档文件数和字节数，再用 `--mirror --no-local` 创建独立副本并运行 filter-repo；不加 `--force`、不做 partial rewrite。所有 refs 均改写，保留空提交及退化 merge，提交消息中的旧哈希保持原样，通过映射追溯。归档位于 `/Volumes/WD-Elements/a2a-evidence/2026-10-19-batch17/T-101/<run>/`，新清单按 run 命名，不覆盖旧清单。

03 立即扫描全部保留历史；只按批准的 object+offset 豁免 413 个旧位置，任何未豁免命中都停止。报告保留总命中、豁免、未豁免数量及逐项定位，没有原文。相同假值进入新对象也不会继承豁免。模式扫描不保证识别加密或任意编码的秘密。扫描通过后，候选工作区为：

```text
/Volumes/WD-Elements/a2a-backup-pre-slim/run-20261019-01/prepared
```

候选新增 `records/T-101-<run>-commit-map.txt` 与 `ref-map.txt`、归档清单及 Markdown 链接更新。由主控审查并正常提交这些生成物，使候选干净；不手写 A2A 尾注。随后先列出机械迁移计划：

```sh
sh "$t101/RUN-OUTSIDE-03b-migrate-hashes.sh" run-20261019-01 --plan-only
```

据 `hash-migration-plan.json` 补齐无模型的相关套件清单。每项包含 `argv`、精确 `covers` 路径列表、`timeout_seconds`；顶层显式 `no_models=true`。`{worktree}` 和 `{output}` 由脚本展开为当前候选及各自全新输出目录。套件清单由主控核对，不自动执行不明操作脚本。然后运行：

```sh
sh "$t101/RUN-OUTSIDE-03b-migrate-hashes.sh" run-20261019-01 --suites /Volumes/WD-Elements/a2a-backup-pre-slim/run-20261019-01/hash-migration-suites.json
```

03b 保存迁移前输出，机械替换，再用同一套件模板保存迁移后输出；后者必须全通过。检查无计划外改动后只把哈希调用方做独立提交，记录 parent/commit/精确替换与前后对照。失败不回退、不改断言、不自动重试，保留候选与日志。若源 main 在正式备份后改变，仍须用新 run 重做。

```sh
sh "$t101/RUN-OUTSIDE-04-verify.sh" run-20261019-01
```

04 要求候选干净、03b 对照通过、移出路径在全部保留历史中消失、摘要/输入及 23 份原生会话正文/历史版本都在；代码仅允许精确哈希迁移，其余字节/模式不变。还核对随机 5 个映射、所有 exec/* 分支、未豁免命中 0、旧哈希调用、完整 checkout status 及现有套件。03b 或任何新改动产生的新对象即使含同一假值也须重新裁定，不能自动继承原清单。失败不产生 verified 收据。

只有 04 和独立审查均通过、原仓库仍停在 snapshot、旧 worker 已回收时运行：

```sh
A2A_T101_QUIESCENT=1 sh "$t101/RUN-OUTSIDE-05-replace.sh" run-20261019-01
```

05 再核对正式备份对象数、当前 refs 和工作区；snapshot 中所有已注册 exec/* worktree 分支（含仍存在的 T-103/T-104）均须已集成旧 main。已暂存内容或冲突的未提交文件会阻止替换。脚本保留原 `.git` 至相邻 `.a2a-git-pre-slim-<run>`，只修改已核对的 tracked 差异；其余 dirty/untracked 文件保留。linked worktree 文件和 index 留在原历史，并指回保留的旧 Git，**不再用于后续开发**；新主仓库的对应 exec/* refs 已按映射移动，需要时另建 worktree。

替换意图一旦写出，脚本拒绝自动重试；中途失败由主控核对旧 Git、暂存 Git、工作区和 intent，不使用 reset 或自动回滚掩盖未知结果。替换后先核对 `installed.json` 和实际工作区，再执行单独发布脚本：

```sh
sh "$t101/RUN-OUTSIDE-06-publish.sh" run-20261019-01
```

06 再扫实际新仓库，使用同一精确清单；未豁免命中必须为 0，缺少该字段的旧扫描收据不接受。再通过 `gh api repos/a1024053774/a2a/git/ref/heads/main --jq .object.sha` 和 `git ls-remote origin refs/heads/main` 核对远端仍是完整 `a96a040d3d87e43e7fc882da9e574bed2dbcd2d4`。不符就停。唯一 push 命令为：

```sh
git push --force-with-lease=main:a96a040d3d87e43e7fc882da9e574bed2dbcd2d4 origin main
```

通过子进程 `GIT_CONFIG_*` 的 URL rewrite 和 `!gh auth git-credential` 一次性走 HTTPS，不读取/输出 token，不写全局 Git 配置。只推 main，不推 backup/*，不改变仓库可见性。push 前写 intent；失败或结果未知时禁止自动重试。成功后再次通过 gh api 和 ls-remote 核对，并保存 before/after/候选 SHA。

## 资料来源与本次限制

- 已读 [git-filter-repo 官方手册](https://raw.githubusercontent.com/newren/git-filter-repo/main/Documentation/git-filter-repo.txt) 与[安装文档](https://raw.githubusercontent.com/newren/git-filter-repo/main/INSTALL.md)，2026-10-19 查阅。工具实际版本以 00 的 installed.txt 为准，worker 未安装它。
- GPL 正文取自 [GNU GPL-3.0 官方文本](https://www.gnu.org/licenses/gpl-3.0.txt)，原样保存；Synara 声明未改。
- followup 检查已能使用主控安装的 2.47.0，在 `/tmp` 小夹具执行真实 filter-repo 和迁移前后同套件；它不替代真实项目试跑、全历史扫描、完整备份、独立审查、替换与远端验证。
