# T-042 合并后复验（2026-10-08）

总体 **BLOCKED**。本轮执行 agent 的构建环境准备错误破坏了测试环境，不能据此认定产品回归。已停止后续验收，未启动 Electron，没有本轮截图或人工介入事件证据。

| 项目 | 结论 | 证据与边界 |
| --- | --- | --- |
| lint | PASS | `lint.log`、`lint-result.json`，退出码 0；发生在环境事故之前 |
| 18 项编排 | INCOMPLETE | `orchestration.log`、`orchestration-trace.json`、`orchestration-result.json`；18 项运行，14 项通过、4 项失败，退出码 1，65.915 秒。失败命令均找不到门禁 CLI 模块，本轮不支持候选通过或产品回归结论 |
| 17 项交付/恢复 | INCOMPLETE | 未运行；按任务书的复验失败停止条件暂停 |
| membership HTTP 场景 | INCOMPLETE | 未运行 |
| observer healthy / 受管消息 / events 回读 / 非受管反例 | INCOMPLETE | 未启动 Electron，未执行 Computer Use，未发送消息；没有截图，不以旧截图或夹具代替 |
| 当前环境恢复 | INCOMPLETE | Git 受控文件已恢复、原 server dist 已放回；依赖目录缺失尚未恢复，未执行安装或再次构建 |

## 环境事故与恢复

候选 checkout 为 `/Users/luckye/Documents/Code/synara`，分支 `a2a`，提交 `3566ef4eb34b18c480c7a49e4b5d741681b72426`。开始检查只有原有未跟踪 `.grok/`，没有受控文件改动。本轮没有修改 `synara-t038`，没有 push、调用模型、启用 provider 或操作用户 Synara、浏览器、Codex home、Herdr。

新隔离目录为 `/Volumes/WD-Elements/dev-cache/synara/instances/t042-verify`。测试 HOME、XDG、CODEX_HOME、CLAUDE_CONFIG_DIR、临时目录均在其中；Bun 命令经 fork 的 `a2a/scripts/bun`，slot 为 `t042-verify`。编排仍使用 T-037 原测试和原生入口；仅证据记录器改为向本 verify 目录写出，临时夹具放新外置目录，没有改断言或 oracle。

为避免使用合并前 server bundle，执行 agent 将原 `apps/server/dist` 移到外置盘 `original-server-dist`，把新输出目录链接回该路径，随后在输出目录内放入指向 `apps/server/node_modules` 的链接。这个安排是错误的：tsdown 清理输出时沿依赖链接清理了工作区 package 文件及依赖；测试同时运行，后四项因 `packages/a2a-gates/src/cli.ts` 缺失而失败。构建本身也退出 1，日志包含大量 unresolved import，最后报告缺少 client/favicon.ico。`build-paths.json`、`build-server-command.json`、`build-server.log` 和 `unexpected-worktree-state.txt` 保留现场。

发现后停止推进，没有修产品逻辑。只对删除清单中的 6,186 个受控文件执行从上述完整候选版本恢复，未覆盖其他文件；详情见 `tracked-source-restoration.json`。随后撤销本轮 dist 链接，从外置备份复制回原 server dist。`post-restoration-status.txt` 显示仅原有 `.grok/`。外置原 bundle 备份和失败构建输出继续保留。

Git 状态恢复不能证明依赖恢复。`dependency-presence-after-incident.json` 检查 package.json 的存在：server 30、desktop 7、web 61、contracts 6、shared 6、a2a-gates 4 个依赖声明在可解析目录中找不到 package.json；不同包可能重复计数，也不是所有损坏文件的完整清单。没有事故前依赖逐文件清单，因此不能完整界定被清理的忽略文件。没有继续安装或用其他 checkout 补依赖。

测试 trace 中自动分类的 `business-red` 原样保留；它对应 CLI 模块缺失，不能作为产品业务缺陷。四个直接模块缺失命令另提取到 `module-missing-failures.json`。旧通过记录不为本轮背书。首次记录脚本的根路径索引也曾在执行 lint 前出错，单独记录于 `runner-setup-failure.txt`，修正后才执行了有效 lint。

## 命令、证据与收尾

从 a2a 根目录执行的入口依次为：

```sh
python3 evidence/2026-10-07-synara-batch2/T-042/verify/run-check.py lint
python3 evidence/2026-10-07-synara-batch2/T-042/verify/run-check.py orchestration
python3 evidence/2026-10-07-synara-batch2/T-042/verify/run-check.py build-server
```

每个 `*-command.json` / `*-result.json` 保存实际 argv、cwd、隔离环境、候选、起止时间和退出码，完整 stdout/stderr 合并保存于同名 log。构建准备本身不应重做；复验必须使用新的记录名与外置目录。没有改动原验收脚本。

`retained-orchestration-fixtures.tar.gz` 归档本次测试 Git repo、worktree、门禁状态和 oracle；原目录保留，未把内嵌仓库登记为 gitlink。归档不含用户 auth 或 profile。执行身份为当前 Codex GUI agent；没有额外业务 task/attempt，测试各自的 task、attempt、session/fence 见原始 trace。本次没有真实供应商调用或实际 tier 证明。

`cleanup.json` 记录命令均已结束、没有匹配的遗留执行进程，以及 5811/7771 无监听。没有启动 Electron 或 dev server。`project-map-status.txt` 的 Problems 和 stale 均为 0。没有修改 MAP、ticket 或 AGENTS；提交范围仅本 verify 目录。

需要用户决定：是否允许先恢复 Synara 的依赖环境，再从新隔离目录重跑本任务。当前停止来自任务书的“若复验失败，保存现场后停下告诉用户，不自行修”，不是产品已被证明失败，也不是 provider 权限已被实际触发。
