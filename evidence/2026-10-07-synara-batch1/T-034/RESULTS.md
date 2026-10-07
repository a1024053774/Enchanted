# T-034 构建与隔离运行记录（2026-10-07）

交付状态：INCOMPLETE。实现与行为验收为 PASS；[独立只读验收审查](acceptance-review.md) 对冻结候选与证据给出 PASS，所列验证限制保留。关闭 ticket 时，项目状态检查要求补 MAP 索引，而任务书禁止 worker 改 MAP；唯一剩余项及可直接应用的索引行见 [主控收尾](controller-handoff.md)。

生产 fork 提交：`0b1740fd4e385baf389095e5cfa16dd67adcd3b4`，分支 `a2a`；起点 `f176e8967aa5a4a7faf1dc4bd070360d5fceabec`（v1.0.1-beta.2）。仅新增 `a2a/scripts/bun` 与 `a2a/README.md`，上游脚本未修改。主控 Claude Code（wF:pM）；worker s1-t034（wF:pV），身份及启动参数见 [runtime.json](runtime.json)。实际供应商 service tier 未核对；没有以请求参数作为实际 tier 的证明。

## 命令与结果

下表命令均在 `/Users/luckye/Documents/Code/synara` 执行，经 `./a2a/scripts/bun`，设置 `A2A_SYNARA_SLOT=t034`；桌面使用 `t034-desktop`。每个命令的完整 argv、输出、退出码与耗时保存在同名 JSON/log 文件中。

| 执行项 | 入口参数 | 结果与证据 |
| --- | --- | --- |
| Node 准备 | `setup-node` | PASS，22.68 秒；[node-setup.json](node-setup.json)、[官方校验清单](node-official-SHASUMS256.txt) |
| 首次依赖安装 | `install --frozen-lockfile` | PASS，1635 个包，2434.25 秒；[install.json](install.json)、[install.log](install.log) |
| 冻结提交安装复验 | `install --frozen-lockfile` | PASS，6.82 秒，无依赖变更；[install-frozen.json](install-frozen.json) |
| 完整构建 | `run build` | PASS，5 个任务，89.72 秒；[build.json](build.json)、[build.log](build.log) |
| dev server | `run dev:server` | PASS；端口 4807，首次 HTTP 200 为 2.51 秒；[server-service.json](server-service.json)。后续完整 readiness 全部为 true：[server2-health-later.json](server2-health-later.json) |
| web dev | `run dev:web` | PASS；`http://localhost:6767/` 首次 HTTP 200 为 19.21 秒；[web2-service.json](web2-service.json)、[网页响应](web2-http-0.txt) |
| 桌面启动 | `run start:desktop` | PASS；独立 Cua 身份，原生 UI 与截图确认；[desktop.png](desktop.png)、[desktop-ax.txt](desktop-ax.txt) |
| 桌面暖启动计时 | `run start:desktop` | PASS；旧实例退出后出现新 PID 24997，入口到原生 AX 确认的观测上界为 6.37 秒；[desktop3-ready.json](desktop3-ready.json)、[新进程](desktop3-main-process.json) |
| 格式、lint、类型检查 | `run fmt:check`、`run lint`、`run typecheck` | PASS，类型检查覆盖 7 个 workspace；对应日志保留 |
| 相关既有测试 | desktop profile/source launcher、dev runner | PASS，18 + 21 个 Vitest 测试；[desktop-tests.log](desktop-tests.log)、[runner-tests.log](runner-tests.log) |

Node 来自 `https://nodejs.org/dist/v24.13.1/` 的官方 macOS arm64 包。下载包 SHA256 为 `8c039d59f2fec6195e4281ad5b0d02b9a940897b4df7b849c6fb48be6787bba6`，与官方清单匹配后才解压。入口子进程实际 Node 为 v24.13.1；全局 Node 前后仍为 v26.5.0。Bun 为 1.4.2；工具链与缓存来源见 [sources.json](sources.json)、fork 的 `a2a/README.md`。

首次安装使用尚未提交的入口草稿；正式提交随后调整了错误提示文字与 README 格式。冻结提交的安装复验、构建、检查、缺盘测试与运行版本绑定见 [versions.json](versions.json)。

## 缓存、隔离与缺盘反例

卷经 `is_mount`、设备号及 `diskutil` 检查：真实 APFS 挂载点、USB、External。Bun 缓存的实际打开文件位于外置盘；Electron 43.4.1 下载 ZIP 位于外置盘 `electron/`，约 117 MiB。electron-builder 下载缓存变量指向外置盘，目录本轮未产生下载文件。见 [cache-use.json](cache-use.json)、[environment.log](environment.log)。

dev home 为 `instances/t034/home`；桌面 home 为 `instances/t034-desktop/home`，SQLite 在其 `userdata/state.sqlite`，Electron profile 为 `instances/t034-desktop/electron-profile`。原生进程打开的 profile 文件都在外置盘，默认 `.synara-cua` 与 Application Support profile 未生成；已有 `.synara` 的占用与目录 mtime 未改变。见 [desktop-isolation.json](desktop-isolation.json)、[disk-before.json](disk-before.json)、[disk-final.json](disk-final.json)。worker 未执行 agent 任务或提交模型消息。

缺盘用不存在路径模拟，未卸载外置盘。不存在路径、内置普通目录和内置根目录共 3 类输入，覆盖安装、构建、dev、桌面、Node 准备 5 个命令：15 项均在 Bun 启动前退出 2，测试目录未变化，Bun 哨兵未执行。忽略指定卷的坏版本会执行 Bun 哨兵，被同一验收条件识别。冻结提交结果见 [guard-frozen-result.json](guard-frozen-result.json)。复现命令：

```sh
python3 evidence/2026-10-07-synara-batch1/T-034/guard-check.py new-result.json
SYNARA_BUILD_VOLUME=/tmp/t034-not-mounted-volume /Users/luckye/Documents/Code/synara/a2a/scripts/bun install --frozen-lockfile
```

## 磁盘测量

单位为 KiB，取 `du -sk`；GiB 仅用于便于阅读的换算。原始前后 `df`、各目录 `du` 见 [disk-before.json](disk-before.json)、[disk-final.json](disk-final.json) 与 [disk-summary.json](disk-summary.json)。

| 范围 | 前 | 后 / 新增 |
| --- | ---: | ---: |
| fork checkout 总计 | 317,464 | 3,836,356；新增 3,518,892（约 3.36 GiB） |
| 根及 workspace 的 node_modules | 安装前不存在 | 2,892,488（约 2.76 GiB） |
| checkout 其他新增 | — | 626,404（约 0.60 GiB），含桌面 bundle、构建产物、类型缓存、Git 元数据；包含保留的 `.grok/` 4 KiB |
| 外置盘 synara 缓存/工具链/运行数据总计 | 不存在 | 3,038,584（约 2.90 GiB） |
| 其中 Bun / Electron ZIP | 不存在 | 2,469,644 / 119,376 |
| 其中 toolchains / instances / Turbo | 不存在 | 245,880 / 10,924 / 72,484 |
| T-034 证据目录（收尾报告前） | 不存在 | 1,828；另保留 4 个哨兵夹具，各 8 KiB |
| 全机内置 APFS 可用空间（df） | 36,597,916 | 29,335,344；减少约 6.93 GiB |

默认 Bun 缓存仍为 143,468 KiB，默认 npm 缓存仍为 1,949,872 KiB；默认 Electron/Electron-builder 缓存目录未生成。全机 `df` 包含其他程序与系统活动，超出已测任务目录的差额不归因给 T-034；`du` 遍历期间数据不是原子快照，测量也跨越了临时分支回到 `a2a` 的操作。最终安装复验在此测量后进行。首次安装还与少量诊断读取、计时探针编译重叠；这些是探索性测量，不是性能收益或成本改善实验。

## 上游合并演练与收尾

`git fetch upstream main` 后，在 `a2a-merge-drill` 合并 `upstream/main`（`f1b2f7c7e11867eee034d11020b043dcb53f03f9`）。合并提交为 `00a856f8beb96c1db065048a98cd81b6a9be9a9a`，自动 ort 合并，无冲突、无人工解决；15 个上游文件发生变化。合并后 7 个 workspace 类型检查通过，skills catalog 的 28 个测试通过。见 [merge-summary.json](merge-summary.json)、[merge-typecheck.log](merge-typecheck.log)、[merge-server-tests.log](merge-server-tests.log)。

已切回 `a2a`，它不包含演练合并提交；临时分支保留，两仓库均未 push。所有本次启动的 dev 与桌面进程已关闭，指定端口无监听，原生 bundle 无残留进程。见 [runtime-cleanup.json](runtime-cleanup.json)、[final-state.json](final-state.json)。fork 保留未跟踪 `.grok/settings.json`，不加入交付提交，也不删除；其来源未独立核对。

## 失败与验证边界

- 组合 dev 的 stream 参数转发失败，首次参数解析错误还返回了退出码 0；最终使用既有 `dev:server` / `dev:web` 并以真实 HTTP 验证。原日志保留。
- 初次网页探针使用 IPv4，而 Vite 监听 IPv6 localhost；该尝试未通过，后续以实际地址重新验证。
- 初次桌面窗口探针超时；原生 UI 工具首次调用异常耗时 2143.54 秒，冷启动精确耗时未核对。一个重启尝试与旧实例重叠，被明确作废；6.37 秒来自旧实例退出后的独立暖启动。
- 原生工具提示 UI 状态变化，读取新状态后才确认退出。出现的界面草稿未由 worker 提交。完整失败与更正见 [failure-notes.txt](failure-notes.txt)。
- 上游缺少 `actool` 时跳过 Liquid Glass 图标；Browserslist、chunk 大小及 marketing cache 警告保留，未扩大到上游修复。
- 未运行全仓 Vitest、上游浏览器 E2E 或真实 provider turn；本轮证据支持构建、隔离启动和合并演练，不据此验收后续门禁或模型能力。
