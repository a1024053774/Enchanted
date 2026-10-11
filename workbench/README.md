# a2a 门禁（T-075-2）

用 Node 26.5 及其原生 TypeScript 类型剥离直接运行，无 Bun、打包或编译步骤：

```sh
node workbench/src/gates/cli.ts --state /绝对路径/隔离状态目录 status --task 任务编号
```

`acceptance/entry/a2a_gates.py` 将参数原样交给这里的 CLI。门禁核心仍由
`A2AGates.call` 独占写入；保留操作锁、fence、CAS、attempt 绑定和中断恢复。
受管任务通过 JSON 任务卡注册；交付按卡检查路径、完成条件与提交尾注，
通过后以 CAS 推进项目工作分支。普通会话的 `attach --instructions` 仍是提示文本，
不参与受管任务注册。
旧 HTTP 转接经本次对话确认后删除；本入口只接受本地门禁命令。

## 任务卡与交付

使用同一个 CLI 生成模板，填写目标、非目标、路径、argv 完成条件等字段后校验并保存：

```sh
node workbench/src/gates/cli.ts --state /绝对路径/state card_template --task T-080-1 --repo /绝对路径/repo --ticket /绝对路径/T-080.md
node workbench/src/gates/cli.ts --state /绝对路径/state card_validate --task T-080-1 --card /绝对路径/card.json
node workbench/src/gates/cli.ts --state /绝对路径/state card_save --task T-080-1 --card /绝对路径/card.json --expected-version 0
node workbench/src/gates/cli.ts --state /绝对路径/state create --task T-080-1 --repo /绝对路径/repo --branch refs/heads/main --card-version 1
```

模板含 13 个字段。CLI 值精确为 `Claude Code` 或 `Codex`；任务类型为规格中的八个值。
完成条件格式为 `{"argv":["python3","acceptance/check.py","{worktree}"]}`，
`{worktree}` 只能占据完整的一个参数，在独立 M worktree 中运行。完成条件非零退出仍
返回 `oracle_failed`，这个名字只为保持已有公开错误预期，不存在旧 oracle 注册入口。
create 不再接受 `--base`、`--oracle` 或 `--instructions`。

版本与快照存入同一 SQLite 库，旧记录不修改；`card_show --card-version N` 读指定版本。
注册冻结选定版本，认领时再追加包含当时工作分支起点和唯一写入者的绑定快照。
源文件或后续卡版本不会改变已注册合同。显式采用新卡用
`revise --spec-rev N --card-version V`，会使旧 attempt 与候选失效。

路径用仓库相对文件名、末尾 `/` 的目录或 `.`，禁止项优先，不解释 glob。
门禁检查候选相对起点的净改动，以及 M 相对 G 的净改动。
尾注归属按 Task、Attempt、Session、Role 四项核对；外来任务或坏尾注被拒。
完全无 A2A 尾注的提交产生来源为“推断：缺尾注”的 action 用户输入和派生人工介入，
不阻止集成，同 attempt 同 commit 重验不重复记录。

工作分支必须是已存在的 `refs/heads/*`。门禁不再读写 `refs/a2a/integration`，历史引用保留。
Git 事务先锁住 G，在实际检出目录用双树快进保护本地修改，再 CAS 到 M；覆盖型修改被拒，
无冲突修改保留。未知副作用保留原 integration intent 待核对。没有 push、stash 或用户目录 reset。
验收仍由 verify 完成，integrate 只接受与该 attempt、卡快照和候选绑定的通过记录。

## 安装

```sh
cd workbench
python3 -c 'import os; assert os.path.ismount("/Volumes/WD-Elements"), "外置盘未挂载"'
npm ci --cache /Volumes/WD-Elements/a2a-t075-npm-cache
npm ls --depth=0
```

缓存由本目录 `.npmrc` 指向外置盘；安装前检查挂载与缓存位置，失败就退出。
`node_modules` 是本目录中的普通目录。依赖锁定 `effect@4.0.0-beta.25`；来源预览包
改为 npm 官方包是执行主控的决定，记录见本批证据 `controller-decision-01.md`。

## 运行时边界

`GateRuntime` 是宿主提供的生命周期接口。`dispatch`、`attach`、`run` 保留原门禁语义；
未传入运行时时拒绝需要它的操作。这里没有 provider、MCP 网关、PTY 或后台服务实现。
编排验收的 `native-runtime.ts` 只替代这个外部边界，不执行模型、不写门禁 SQLite。
真实窗格宿主由 T-075-3 接入；18 项编排验收仅是隔离证据。
来源版本的 dispatch 交付提示词仍随该边界保留；T-075-3 接入宿主时须将其中的
交付接口文本换成实际后台 CLI 命令，本卡不据此声称可以派发真实 worker。

## 来源与改动

来源固定为 Synara 提交 `49cae984f22924de006e0f8358cb447eb881aaf6`。
迁入 `core`、`cli`、`membership`、`rolePermissions`；MIT 版权与完整许可保留在源码及
[LICENSE.synara](LICENSE.synara)。只提取门禁及其请求校验实际需要的 schema、类型与依赖，
其中模型选择的已有解码规则保持原样，不代表本工作台支持这些模型运行时。

进程执行直接使用 Node 的 `child_process.execFile`；本卡面向 macOS，不带原平台适配层。
本地 import 补 `.ts` 后缀，构造器参数属性展开为等价字段与赋值。
验收入口只调用本仓库门禁；旧 fork 的实现不再由这些入口加载。

重现命令与完整证据见
[T-075-1 迁移记录](../evidence/2026-10-10-batch12/T-075/RESULTS.md) 和
[T-075-2 当前结果](../evidence/2026-10-10-batch12/T-075/card-2/RESULTS.md)。
