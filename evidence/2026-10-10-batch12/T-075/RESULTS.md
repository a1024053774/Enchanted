# T-075-1 门禁迁移记录

状态：INCOMPLETE（门禁迁移与验收已完成；独立审查、收尾检查和提交尚待完成）。T-075 保持 open，待后续卡、待主控关闭。

## 范围与来源

- 起点：`e133c23b964eb5ffea7dfe8ce2147bdc1c0f3c32`；ticket `ready_rev: 2`。
- 来源：`49cae984f22924de006e0f8358cb447eb881aaf6`，仅以 `git show` 读取；未切换或修改 fork，未搬其未审查的 T-066 改动。
- 执行身份：`s12-t075-1`、attempt `a1`、session `650e7298-416b-47fb-abd7-67af2618596e`；launch `launch-6ab977309f01499c86916171f316675a`。启动请求模型为 `gpt-6-astra`、xhigh、Fast；请求配置不代表供应商实际 tier 证明。版本与起点见 `start.json`，完整启动记录仍在项目的 `records/launches.jsonl`。
- 只搬门禁及必要 schema；保留 MIT 声明。不做后台、窗格、Electron 或三项新契约。
- 保留 `GateRuntime` 生命周期与调用者身份边界；编排证据是隔离边界替身，不证明真实 CLI 或窗格可用。

## 替换清单

| 位置 | 替换 |
| --- | --- |
| `workbench/src/gates/` | 从固定来源提取 core、cli、membership、rolePermissions |
| `workbench/src/contracts/` | 门禁实际使用的 schema、类型及其依赖；模型选择的既有解码规则保留，没有 provider 执行代码 |
| 进程边界 | 原 processRuntime 替换为 Node `child_process.execFile`，保留 cwd、env、timeout、maxBuffer 与回调处理 |
| TypeScript | 本地 import 显式 `.ts`，四处构造器参数属性展开为等价字段赋值，Node 26.5 原生类型剥离 |
| `acceptance/entry/` | 两个 Python 入口均启动 Node；编排 submit 将同样的 thread、turn、assertActive 交给新 `gates.call`，不再经过 MCP handler |

最终核心源差异在 `source-adaptation-final.patch`（`source-adaptation.patch` 保留 HTTP 删除前的记录）；`extract-source.py` 只重现首次来源提取，不含后续 Node 调整或主控依赖决定，不可覆盖现有目录。最终代码以交付提交为准。

## 人工介入与环境

主控中断了第一次 npm 提权申请，并按 `controller-decision-01.md` 把预览包改为 npm 官方源的精确版本 `effect@4.0.0-beta.25`，由主控完成安装。两者版本号相同，不假定内容等价；以本次验收为准。安装输出为 `npm-install-by-executor.txt`。

缓存：`/Volumes/WD-Elements/a2a-t075-npm-cache`。`node_modules` 在 `workbench/` 内，为普通目录。`.npmrc` 固定缓存，preinstall 检查外置盘和缓存位置，不设置内置盘回退。已挂载检查输出为 `npm-cache-check.txt`，`npm ls --depth=0` 输出为 `npm-ls.txt`；未卸载用户磁盘做测试。

首轮系统 Python 环境失败原样保留：`green-recovery-01` 的进程身份核对被沙箱拒绝（`ps`）；系统 Python 的 SQLite 3.54.0 对 Node 3.53.3 创建并关闭的 WAL 数据库，`mode=ro` 打开失败。隔离探针 `sqlite-probe.py` 在已有 Python 3.11／SQLite 3.53.3 下通过。没有改变数据库 WAL 模式、修改只读快照或绕过进程身份检查。SQLite 官方说明了只读 WAL 对 WAL／共享内存文件的要求；这里仅报告实测的环境差异，不将其原因扩称为已确认的 SQLite 缺陷：[SQLite WAL 官方说明](https://www.sqlite.org/wal.html)。

## 验收与重现

主控已同意 `run-acceptance.py` 加载原测试、只重定向 `EVIDENCE`、调用原 main。断言和预期没有修改。原 main 再调用原 `--run-suite`；runner 记录真实命令、解释器、环境、退出码，并归档嵌套 repo/worktree，原目录仍留在本机。

| 检查 | 结果 | 产物 |
| --- | --- | --- |
| 起点入口指向不存在的新实现 | 三套分别跑 8、9、18 项，均因缺新 cli.ts 失败 | `red-coop`、`red-recovery`、`red-run` |
| 交付候选 | PASS，8/8，0 失败 0 错误 | `outside-executor.K2MrEb-green-coop` |
| 恢复候选 | PASS，9/9，0 失败 0 错误 | `outside-executor.K2MrEb-green-recovery` |
| 编排候选 | PASS，18/18，0 失败 0 错误，隔离边界替身 | `outside-executor.K2MrEb-green-run` |
| fence 变异体 | 2 个断言失败（fence 与其后的 spec-rev 状态检查），0 错误 | `outside-executor.K2MrEb-mutant-fence` |
| CAS 变异体运行旧交付套 | 8/8 误过，覆盖缺口已上报 | `mutant-cas-existing-01` |
| CAS 竞争补充场景 | 变异体 1 项业务失败、0 错误；候选 1/1 通过；外部写者 X 必须保留 | `outside-executor.K2MrEb-mutant-cas`、`outside-executor.K2MrEb-green-cas` |
| 操作锁变异体 | 2 项业务失败（live verify / integrate 互斥），0 错误 | `outside-executor.K2MrEb-mutant-lock` |

重现绿态（每次换一个未使用的 label；失败目录不得覆盖）：

```sh
python3 -B evidence/2026-10-10-batch12/T-075/run-acceptance.py coop green-coop-next
/opt/homebrew/bin/python3.11 -B evidence/2026-10-10-batch12/T-075/run-acceptance.py recovery green-recovery-next
/opt/homebrew/bin/python3.11 -B evidence/2026-10-10-batch12/T-075/run-acceptance.py run green-run-next
```

恢复验收需要允许 `ps` 读取夹具所建 CLI 子进程。反例命令：

```sh
python3 -B evidence/2026-10-10-batch12/T-075/run-acceptance.py coop mutant-fence-next --mutant fence --mutant-dir mutants-final
/opt/homebrew/bin/python3.11 -B evidence/2026-10-10-batch12/T-075/run-cas.py mutant-cas-race-next --mutant --mutant-dir mutants-final
/opt/homebrew/bin/python3.11 -B evidence/2026-10-10-batch12/T-075/run-cas.py green-cas-race-next
/opt/homebrew/bin/python3.11 -B evidence/2026-10-10-batch12/T-075/run-acceptance.py recovery mutant-lock-next --mutant lock --mutant-dir mutants-final
```

`mutants-final/*/mutation.patch` 是每个变异体的单点差异；副本只改模块寻址以复用候选依赖，未改生产源码。变异体生成命令为 `python3 -B evidence/2026-10-10-batch12/T-075/make-mutants.py --output mutants-next`，它拒绝覆盖已存在的目录。删除 fence、CAS 期望旧值、操作锁的条件来自任务卡，不从实现输出生成预期。

红态重现：在起点的独立 checkout 应用 `red-entry.patch`，保持 `workbench/` 不存在；按 `red-*/command.json` 设置产物变量并运行各自原 `--run-suite`。红态属于迁移契约缺失，不是既有产品缺陷。

每次套件的 `run.json`、`check-*.json`、stdout/stderr 与 `artifacts.tar.gz` 提供命令及现场。原编排测试仍将旧 fork HEAD 写入名为 `fork_head` 的历史字段；它不是候选门禁版本，本卡以 `run.json` 的新 gate 路径和交付提交为准，没有改写原证据。

## 尚待完成

- 旧 HTTP 转接已按本次用户答复及 `controller-decision-02.md` 删除，同时删除其唯一使用的 A2ARequest schema。最终候选的三套绿态已复验。
- fresh-context 只读独立审查；若发现问题，先红再修，不追审。
- `project_map.py status` 收尾检查；CONTEXT.md 的 stale 由主控处理。
- 交付提交及自动 A2A 尾注核对。

## 沙箱外验收交接（决定 02）

第二次沙箱外申请由执行主控以 Esc 拒绝，未运行。主控要求将所需命令写成脚本后停下；脚本为 `outside-sandbox.sh`，运行命令：

```sh
bash evidence/2026-10-10-batch12/T-075/outside-sandbox.sh
```

已用 `bash -n` 检查语法，执行主控随后在沙箱外完成该脚本，退出 0。原始收据为 `outside-executor.K2MrEb/summary.tsv`，7 项退出码全部与预期相符；worker 已逐项回读 trace，确认三套绿态 8／9／18 及 CAS 正例均无失败、无错误，三个变异体均为业务失败、无夹具错误。它为三套绿态、三个变异体及 CAS 正例分别生成新标签，保存 stdout、stderr、退出码和精确命令；临时夹具限定在 `/tmp`，证据限定本目录，不联网。`mutants-final/` 从删除 HTTP 后的候选生成，并冻结所需的本地 schema 与辅助模块；旧变异体与旧输出保留。主控 #14 已派发继续独立审查与交付。
