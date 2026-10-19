# T-101 / a1 执行交接（2026-10-19）

状态：**INCOMPLETE**。本次交付准备脚本、中文 README、GPL-3.0 正文和隔离验证。未写外置盘，未安装工具，未实际瘦身/替换，未 push，未调用模型。真实全历史扫描与旧→新映射尚未产生，不提供占位映射表。

身份：task `T-101`，attempt `a1`，session `8465b431-08a5-4077-a6b5-1d43761650e3`，launch `launch-7389a5e942e54c0b994eff30a502e972`，起点 `803e6cf69abbd7727c3694a446a52eb5940ddf2e`。按执行主控本 session 的答复，本票在 Herdr 期以 `exec/t101` 带钩子尾注的提交交付，没有门禁 state/fence/spec_rev，不调用新工作台 submit。

## 执行前提

1. 执行主控审查本候选并派独立只读审查。本 worker 没有启动额外模型，不能代称独立审查通过。
2. T-101 与 T-102 的交付先经当前流程集成到旧 main，回收旧 worker，暂停所有会写仓库/records/inbox 的进程。备份、核对和替换期间保持静止；不修改/重启用户 Herdr server。
3. 确认 `/Volumes/WD-Elements` 挂载；大文件、工具、缓存和副本只写外置盘。内置盘仅暂存瘦身后的新 Git，必须另有至少该 Git 体积加 256 MiB 的空间。旧 Git 保留在主仓库旁，不会立即回收原占用。
4. 本次启动观察到 main 已前进到 force 裁定提交 `73f40bd04`。脚本在执行时重新备份当前 refs，不固化旧起点来覆盖新 main。

## 当前阻断项

**测试直接执行旧哈希，需要主控另行处理，worker 不改测试源码。** 例如：

- `workbench/tests/test_t096_restart_cleanup.py:129`、`:145`：`git show 10c0168db:...`、`git show da6a095fc:...`。
- `workbench/tests/test_t096_process_probe.py:54`、`:62`：`git show 958ede25f:...`、`git show da6a095fc:...`。
- 还有动态拼接 revision 的测试，静态探针不声称能穷尽。

映射表可查阅旧引用，但不让这些命令自动解析旧提交。`verify` 会保存已检出的调用并停止，不用旧对象、replace refs 或旧备份引用把旧历史带回新仓库。最小选项是另给调用方迁移的写入范围，让其按 records 中的表查新提交；然后复验。若决定排除某些现有检查，那属于验收条件变化，不能由本 worker 自行决定。

构造路径读取的小输入也须主控审查：`plan.json` 的 `possible_inputs_to_review` 专门列出可能遗漏的输入。`keep-paths.txt` 明确保留 T-088 点名的三个文件，另保留小 Markdown、摘要、命令脚本与静态字面量直接引用的小文件。静态分析不能证明动态路径都被覆盖；不得把 plan 生成成功当作小输入保留验收通过。必要时补 `keep-paths.txt`，使用全新 run id 重新走备份/清单，保留旧 run。

## 依次运行

从已合入本交付的完整主仓库运行，以下变量只用于当前 shell。脚本不申请权限升级，不自触发下一阶段。

```sh
cd /Users/luckye/Documents/Code/a2a
t101=evidence/2026-10-19-batch17/T-101
sh "$t101/RUN-OUTSIDE-07-archive-local.sh"
```

07 把 worker 留在 `/tmp` 的小型真实 Git/文件系统夹具和首轮失败现场复制到外置盘，核对文件数/字节数，不删原件；仓库只新增 sidecar 清单。先审查并提交这些清单，再开始备份。07 已有任一目标时拒绝覆盖，不要自动重复运行。

```sh
sh "$t101/RUN-OUTSIDE-00-tools.sh"
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

03 立即扫描全部保留历史；有任何命中就停止并上报，报告只有路径/对象位置、类型和 offset，没有凭据原文，也不自动豁免假 token。模式扫描不保证识别加密或任意编码的秘密。扫描通过后，候选工作区为：

```text
/Volumes/WD-Elements/a2a-backup-pre-slim/run-20261019-01/prepared
```

候选新增 `records/T-101-<run>-commit-map.txt` 与 `ref-map.txt`、归档清单及 Markdown 链接更新。脚本没有替主控提交生成物。由主控审查差异、处理上面的范围冲突后，在候选中正常提交生成物；不手写 A2A 尾注。若更改了源 main，旧 snapshot 不能用于替换，须用新 run 重做。

```sh
sh "$t101/RUN-OUTSIDE-04-verify.sh" run-20261019-01
```

04 要求候选干净、移出路径在全部保留历史中消失、摘要/输入仍在、非 evidence 源码保持、随机 5 个映射有效、两并行分支精确对应映射、凭据 0 命中、旧哈希执行引用已处理、完整 checkout 的 project_map status 通过，以及派发/收件箱现有套件通过。该套件子进程移除继承的 `GIT_CONFIG_*`，原因和首轮失败证据见 RESULTS；不改全局配置。任何失败均不产生 verified 收据。

只有 04 和独立审查均通过、原仓库仍停在 snapshot、旧 worker 已回收时运行：

```sh
A2A_T101_QUIESCENT=1 sh "$t101/RUN-OUTSIDE-05-replace.sh" run-20261019-01
```

05 再核对备份对象数、当前 refs 和工作区；T-101/T-102 均须已集成旧 main。已暂存内容或任何与候选变更相冲突的未提交文件都会阻止替换。脚本保留原 `.git` 至相邻 `.a2a-git-pre-slim-<run>`，只修改已核对的 tracked 差异；未受影响的 dirty/untracked 文件保留。linked worktree 的文件和 index 留在原历史，并指回保留的旧 Git，**这些旧 worktree 不再用于后续开发**；新主仓库的 `exec/t101`、`exec/t102` 引用已经按映射移动，需继续工作时从新仓库另建 worktree。

替换意图一旦写出，脚本拒绝自动重试；中途失败由主控核对旧 Git、暂存 Git、工作区和 intent，不使用 reset 或自动回滚掩盖未知结果。替换后先核对 `installed.json` 和实际工作区，再执行单独发布脚本：

```sh
sh "$t101/RUN-OUTSIDE-06-publish.sh" run-20261019-01
```

06 再扫实际新仓库；先通过 `gh api repos/a1024053774/a2a/git/ref/heads/main --jq .object.sha` 和 `git ls-remote origin refs/heads/main` 核对远端仍是完整 `a96a040d3d87e43e7fc882da9e574bed2dbcd2d4`。不符就停。唯一 push 命令为：

```sh
git push --force-with-lease=main:a96a040d3d87e43e7fc882da9e574bed2dbcd2d4 origin main
```

通过子进程 `GIT_CONFIG_*` 的 URL rewrite 和 `!gh auth git-credential` 一次性走 HTTPS，不读取/输出 token，不写全局 Git 配置。只推 main，不推 backup/*，不改变仓库可见性。push 前写 intent；失败或结果未知时禁止自动重试。成功后再次通过 gh api 和 ls-remote 核对，并保存 before/after/候选 SHA。

## 资料来源与本次限制

- 已读 [git-filter-repo 官方手册](https://raw.githubusercontent.com/newren/git-filter-repo/main/Documentation/git-filter-repo.txt) 与[安装文档](https://raw.githubusercontent.com/newren/git-filter-repo/main/INSTALL.md)，2026-10-19 查阅。工具实际版本以 00 的 installed.txt 为准，worker 未安装它。
- GPL 正文取自 [GNU GPL-3.0 官方文本](https://www.gnu.org/licenses/gpl-3.0.txt)，原样保存；Synara 声明未改。
- 脚本的本地测试和 25 项现有回归不替代真实 filter-repo、全历史扫描、外置盘复制、独立审查、替换与远端发布验证。
