# T-102 / a2 macOS 应用打包

状态：**INCOMPLETE**。新签名候选等待真实入口复验；未宣布整票通过。a1 的 `RESULTS.md` 与失败现场均保留。

## 绑定与范围

- 日期：2026-10-19；task / attempt：T-102 / a2；ticket ready_rev：1，T-103、T-104 已合入。
- 分支：`exec/t102`；起点：`18f943d81e1bbf290a363bf312b479a43f9fec9a`。
- session：`f6caedda-1ea1-4345-84df-efc8e4ed1d94`；launch：`launch-8343ffbef3274434ab0d956e8c0beb80`；原生身份环境值：`01a15354-f762-73e3-aa78-c8c1c909260e`。
- 完整启动 argv 见 `launch-a2.json`。记录为 Codex CLI 0.163.0、gpt-6.1-sol、xhigh、请求 default；请求配置不证明供应商实际 tier。记录中的 native_session 仍为 unknown，未用环境值改写启动记录。
- 授权：当前派发逐字引用用户“打包吧,打完包我在体验”和“A 先补功能再打包”，并要求安装到 `/Applications`。Herdr 期不调用门禁 submit，无任务卡或 oracle_paths；提交由既有 hook 自动追加尾注，不 push。
- 目标：**Tracer bullet** 为 LaunchServices 打开安装包 → 自动启动编排后台 → 项目／任务选择页 → 普通 zsh → 关界面后仍运行 → 重开原终端。
- 非目标：模型调用、公证、更新器、安装器、跨平台、任务领域设计、用户全局配置与门禁语义改造。
- **Deep modules**：复用 transport 的启动与死端点恢复、原凭据校验、daemon、PTY 和门禁 CLI，不另造门禁入口。**Ubiquitous language**：沿用项目、任务、窗格、编排后台、launch、attempt。

## 运行时与工具选择

REALITY GATE：**PASS（运行时方向）**。主控运行 `RUN-OUTSIDE-02-RUNTIME.sh`，`runtime-20261019T084700.445238Z.json` 退出 0：内置盘 Electron 43.4.1、Node v24.18.1、ABI 148、SQLite 3.53.1，实际导入 `store.ts` 并完成事件写入与读回。此探针支持薄启动层，不能代替完整后台或 PTY 验证。

- `@electron/packager@20.0.4` 只生成应用目录；相比覆盖安装器与更新的 electron-builder，符合本票最小范围。[Packager 官方选项与类型](https://raw.githubusercontent.com/electron/packager/v20.0.4/src/types.ts)。
- Electron 官方支持 `ELECTRON_RUN_AS_NODE=1`；本包复用自己的可执行文件运行原后台源码，无外部 Node 运行时或外置盘运行依赖。[官方环境变量文档](https://www.electronjs.org/docs/latest/api/environment-variables#electron_run_as_node)。
- node-pty 用 `node-gyp@12.1.0`，以 Electron 43.4.1 的 headers 重建；`--devdir` 显式指向外置盘。未采用 `@electron/rebuild@4.0.1`，因为其 constants 将头文件目录固定到 `~/.electron-gyp`。[Electron 原生模块文档](https://www.electronjs.org/docs/latest/tutorial/using-native-node-modules)、[node-gyp 官方选项](https://github.com/nodejs/node-gyp/tree/v12.1.0#command-options)。

## 最小实现

`app/desktop.mjs` 为应用入口，缺省 task 进入已有选择页。首次调用现有 `startDaemon`，仅在 transport 的子进程环境加 `ELECTRON_RUN_AS_NODE=1`，仍 detached、独立日志与 IPC 握手。关界面退出 UI 进程，不停止后台；重开用原凭据认证。

数据默认在内置盘 `~/Library/Application Support/a2a-orchestrator`，UI 在其 `ui/`。每次启动产生 0600、独有文件名的 operator 凭据；`desktop-connection.json` 只保存路径。只有端点不存在才尝试调用 transport 恢复；拒绝、超时或未知所有者不接管、不重放。旧凭据保留，不进入证据或 Git。

应用源码、hooks、原 `src/gates/cli.ts` 保持路径；UI 由原 Vite 构建产生。中间产物、npm 缓存、Electron 下载、headers 和临时文件均在 `/Volumes/WD-Elements`，无盘先失败。node-pty 使用重建的 `build/Release`，helper 在打包时设为 755；运行时仍只检查，不修权限。

远程调试**默认关闭**。产品只解析可选的标准 `--remote-debugging-port` 参数，没有默认端口或开启端口的代码。真实验收脚本显式传 `--remote-debugging-port=0`，用随机 loopback 端口点击和观察真实 renderer；未注入产品模块、替换 IPC 或替应用启动后台。调试端口随 UI 退出。

## 已保留的失败与反事实

| 现场 | 结果与原因 | 处理 |
| --- | --- | --- |
| `desktop-red-02.json` | 新应用入口尚不存在，合同红态 | 实现入口后同一检查绿态；省略后台启动的变异版本被拒 |
| `desktop-green-02.json` | 测试 credential 路径不符合真实 UUID 格式 | 修正夹具路径，没有放宽产品校验；`desktop-green-03.json` 四场景 PASS |
| `transport-regression-02.json` | 既有 VM 的假 process 缺 versions，新运行时判断触发 TypeError | 仅补夹具 `versions: {}`；`transport-regression-03.json` 七场景 PASS，原坏版本仍被拒 |
| `a2-build-01` | node-pty 重建通过；提前移除 electron npm 包，packager 裁剪前遍历失败 | 保留完整暂存依赖树，交 packager 裁剪；a2-build-02 构建通过 |
| `a2-e2e-01` | 签名结构校验通过，但安装包实际 `-p` 被 dyld 拒绝加载，尚无窗口或后台 | `signature-diagnosis-02.json` 证明主程序与 Framework 都是 ad-hoc，但仍带 runtime 标志。当前 osx-sign 的每文件设置从 optionsForFile 取值，顶层 hardenedRuntime=false 没有生效；修为每文件明确 false 与签名 flags=0，新候选须重跑实际入口 |

失败日志、源码快照和完整构建场所在外置盘；仓库只留摘要与 `*.archive.json`。未覆盖旧 run，未把 npm／构建／codesign 通过上调为界面验收通过。

## 验收逐项

| ticket 条件 | 当前状态 | 证据 |
| --- | --- | --- |
| 红态无应用；绿态双击、zsh、关闭 UI 后后台在 | INCOMPLETE | a1 `baseline-01.json` 与本轮起始无安装；新包真实旅程待复验 |
| 用打包产物开项目、任务、终端、关界面再开，截图 | INCOMPLETE | 只使用 `/Applications/a2a.app` 的 05 脚本已准备；01 在实际 runtime 探针处失败，截图 0 张 |
| 无外置盘构建拒绝；缺 task 不崩溃 | 部分 PASS | a2-e2e-01 的假挂载点反例退出 1，匹配挂载诊断且无新文件；无 task 真实窗口待复验 |
| 体积、构建、签名、限制 | 部分 PASS | a2-build-02 外置盘 du 413,380 KiB；首次安装为 3,274 文件、399,642,258 逻辑字节，内置盘 du 398,372 KiB。该包实际加载失败，不能作为可用交付 |
| project_map status 0 问题 | PASS（当前工作目录） | `static-map-03.json` 为 0 problems、0 stale。仅补全 HEAD 中 6 个已有受控文件，字节一致；见 `map-materialized-02.json`；没有修改地图或稀疏配置 |

`ipc-regression-02.json` 检查原 main/preload 合同及其坏版本；`transport-regression-03.json` 检查原死端点恢复边界；都是供应外部边界的局部检查，不作为真实 GUI／后台证明。

## 主控执行命令

```sh
bash evidence/2026-10-19-batch17/T-102/RUN-OUTSIDE-03-BUILD.sh a2-build-03
bash evidence/2026-10-19-batch17/T-102/RUN-OUTSIDE-04-INSTALL.sh evidence/2026-10-19-batch17/T-102/a2-build-03-summary.json evidence/2026-10-19-batch17/T-102/install-20261019T085846.823773Z.json
bash evidence/2026-10-19-batch17/T-102/RUN-OUTSIDE-05-E2E.sh a2-e2e-02
```

04 原本遇到已有应用就停止。主控针对本轮坏安装明确授权后，增加仅限该安装记录的替换：先确认无应用进程、文件数与字节数完全一致，复制到外置盘 `replaced-<时间>/a2a.app`，再次核对，再清出旧路径并安装；不一致就停。归档保留旧包，不能直接运行 USB 上的归档包。新安装后必须通过 `codesign --verify --deep --strict` 与实际 `-p` 探针。

05 使用 `/private/tmp` 下的新状态目录与 UI 数据，后台由应用启动。通过原门禁 CLI 在隔离 Git repo 建两个项目与任务；点击 UI 新建 zsh，经 xterm 输入独立 nonce、pwd、zsh 版本，并写独立 proof 文件。关掉整个 UI 后核对原 PID，再重开并核对原 launch。成功时停止自建后台／shell，删除测试凭据，归档夹具并核对文件数与字节数，再移除临时夹具；失败保留进程身份与现场，不猜测回收。

## 已知限制与交接

- 只支持本机 macOS arm64，自用 ad-hoc，不公证、不开 hardened runtime、无更新器、无安装器；不能据此宣称可对外发行。
- 选择页只列已有项目／任务；创建仍经原门禁 CLI。桌面缺省后台配置为空，本票只验普通 zsh，不调用或证明模型／受管任务完整流程。
- 旧手工后台没有桌面连接描述时，应用拒绝接管同一状态目录，须由原启动者按原入口收尾。
- Node 24 的支持范围由本轮探针与真实 tracer 限定；不能用它替原 Node 26 下所有门禁验收背书。
- 当前 worker 不调用模型或新 reviewer。收尾依 `behavioral-acceptance-review` 准备冻结候选与证据，由主控另开干净只读会话独立审查；实现会话不自称独立审查。
- 尚未提交；最终提交与完整候选版本待 06 提交脚本和主控回传。没有 push、submit 或修改用户全局配置。
