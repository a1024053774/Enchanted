# a2a 门禁（T-075-1）

用 Node 26.5 及其原生 TypeScript 类型剥离直接运行，无 Bun、打包或编译步骤：

```sh
node workbench/src/gates/cli.ts --state /绝对路径/隔离状态目录 status --task 任务编号
```

`acceptance/entry/a2a_gates.py` 将参数原样交给这里的 CLI。门禁核心仍由
`A2AGates.call` 独占写入；保留操作锁、fence、CAS、attempt 绑定和中断恢复。
本卡未改变集成目标、路径检查、提交尾注或任务卡契约。
旧 HTTP 转接经本次对话确认后删除；本入口只接受本地门禁命令。

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
真实窗格宿主由 T-075-3 接入；本卡的 18 项编排验收仅是隔离证据。
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
[RESULTS.md](../evidence/2026-10-10-batch12/T-075/RESULTS.md)。
