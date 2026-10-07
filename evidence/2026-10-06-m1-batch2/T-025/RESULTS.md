# T-025 交付记录（2026-10-06）

结论：**INCOMPLETE**。自动范围已核实；系统拼音、跨应用复制和玻璃观感尚未由真人测试。T-025 保持 `status: open`，不能据此关闭 ticket 或宣布 M1 通过。

主控为 Claude Code（`wF:pM`），worker 为 Codex（`wF:pR`）。本次为任务书指定的 research 探针，没有分配 `coop.py` attempt/session/fence；不能冒充受管任务验收。原生会话、请求模型配置、CLI、系统与 Herdr 版本在 [metadata.json](metadata.json)。Fast 仅为请求配置，供应商实际 tier 未知。任务与规格快照为 [input-brief.md](input-brief.md)、[spec-used.md](spec-used.md)。全部 skill 正文快照保留在 `skills/`。

## 已自动核实

| 范围 | 结果 | 证据与限制 |
| --- | --- | --- |
| 独立包与锁定版本 | PASS | `probes/t025-gpui/` 不加入 Muster workspace；Cargo.lock 锁定 gpui-kit/component/base 0.7.1、gpui-pre 家族 0.3.8，见 [locked-versions.json](locked-versions.json) |
| 构建 | PASS | 本机 Rust 1.96.1、macOS 27.0、仅 Command Line Tools；真实窗口版本 `build-01` 退出 0；所有 Cargo 调用经 `scripts/build`，slot 固定为 worker-t025 |
| 状态到视图 | PASS（限无头范围） | [green-03](green-03/) 通过真实窗口与 Render 入口：切换玻璃范围、35% 不透明度、多行换行、第二框输入后第一框文本保留、正文区域布局；读取组件原生无障碍值和布局，不证明实际像素透明度 |
| 已知坏实现 | PASS（拒绝符合预期） | [red-03](red-03/) 的空视图缺控件而失败；最终测试对 [mutant-01](mutant-01/) 中“整窗按钮忽略切换”的实现退出 101，实际仍显示仅侧栏而期望整窗；恢复后 green-03 再通过，未改测试答案 |
| 原生窗口出现 | PASS | 两次真实进程均被 macOS 窗口清单观测到，标题、PID、窗口编号与尺寸在各自 `window.json`；screencapture 均退出 0，截图回读可见两个输入框及中文、代码、emoji 正文 |
| 启动参数 | PASS（本轮输入） | 实际启动 `sidebar / 0.75` 与 `window / 0.35`；`--help` 退出 0；`--opacity NaN` 按参数合同拒绝并退出 2 |
| 探针回收 | PASS（仅进程回收） | 截图后核对完整进程 argv，只向对应探针 PID 发 SIGTERM；保留退出 -15、cleanup.json 与进程不存在的回读。未把 SIGTERM 当作正常关窗行为验收 |

真实截图：[仅侧栏 75%](runtime-sidebar/window.png)、[整窗 35%](runtime-window/window.png)。两张都是窗口截图，没有受控的背景图案或真人观感判断；不能证明玻璃模糊程度、候选窗位置或跨应用剪贴板保真。本轮没有录制真人操作视频，没有用程序粘贴中文来冒充 IME 输入。

## 构建耗时与占用

所有耗时为包装器墙钟时间，包含入口检查、Cargo 元数据、共享包缓存等待、编译和测试；不是纯编译 CPU 时间，也不是性能收益对照实验。每个目录保留精确 argv/cwd、原始 stdout/stderr、退出码和耗时，失败未覆盖。

| 运行 | 秒 | 退出码 | 解释 |
| --- | ---: | ---: | --- |
| fetch-01 | 69.44 | 0 | 下载并生成锁文件 |
| red-01 | 403.37 | 101 | 首次依赖编译后，关窗回调参数个数错误；不是合同红态 |
| red-02 | 101.74 | 101 | 回调参数顺序错误；不是合同红态 |
| red-03 | 159.84 | 101 | 编译成功，空视图因缺少 glass-status 失败，属于合同红态 |
| green-01 | 91.25 | 101 | 测试模块遗漏 AppContext trait 导入；不是行为失败 |
| green-02 | 111.96 | 0 | 完整无头行为检查通过 |
| mutant-01 | 51.81 | 101 | 已知坏实现被最终测试拒绝 |
| green-03 | 71.36 | 0 | 恢复正确源码后同一测试通过，1 项、0 跳过 |
| build-01 | 243.13 | 0 | 首次构建真实窗口版本，复用已有公共依赖；无 test-support 的 GPUI 依赖重新编译 |

编译修错共 **3 轮**：关窗回调参数个数、参数顺序、测试 trait 导入。它们是探针接线错误，没有证据把它们归为 GPUI 缺陷。多行 API 在编码前已核对：此版本使用 `Textarea / TextareaState`，第二框使用单行 `Input / InputState`。组件 Root 默认绘制不透明主题背景，探针在根节点清除该背景，再用面板 alpha 区分整窗与仅侧栏。来源见 [API-NOTES.md](API-NOTES.md)。

结束 target 占用 **1,897,528 KiB（约 1.81 GiB）**，包含测试和窗口版本；可执行文件 **28,941,552 字节（约 27.60 MiB）**。未测峰值、release 或 `.app` 打包体积。原始 `du -sk`、Rust 版本与仓库内没有 target 的检查见 [measurements.json](measurements.json)。未迁移或删除用户已有缓存。依赖 `block 0.1.6` 的未来 Rust 兼容警告保留在日志，本轮没有升级锁定依赖。

源码抽取辅助脚本遇到一次 Python 3.9 不支持 tarfile `filter=` 的问题，改用路径与链接检查后读取源码，见 setup-anomalies.txt；它不计入 Rust 编译修错。初期 runner 位于证据目录，随后移到 `probes/t025-gpui/run-command.py`；早期 command.json 保留当时路径，复现时使用现位置，不改历史记录。

## 复现与真人手测

从仓库根目录运行：

```sh
MUSTER_BUILD_SLOT=worker-t025 ./scripts/build test --locked --manifest-path probes/t025-gpui/Cargo.toml -- --nocapture
MUSTER_BUILD_SLOT=worker-t025 ./scripts/build build --locked --manifest-path probes/t025-gpui/Cargo.toml
MUSTER_BUILD_SLOT=worker-t025 ./scripts/build run --locked --manifest-path probes/t025-gpui/Cargo.toml -- --glass sidebar --opacity 0.75
```

另一模式改为 `--glass window --opacity 0.35`。每次生成新的证据目录；无头测试可用 probe 中的 run-command.py 包装，保存可复现输出。截图查询使用 `python3 probes/t025-gpui/observe-window.py <探针 PID>`，随后 `screencapture -x -l<返回的窗口编号> <新的截图路径>`。本轮精确命令保留在两个 runtime 目录的 command.json、window-query.json、screenshot-command.json。

真人按 [MANUAL-CHECK.md](../../../probes/t025-gpui/MANUAL-CHECK.md) 使用系统拼音：连续组词、取消候选、删除、撤销、切换输入框；再从 Markdown 跨中文、代码与 emoji 拖选，粘贴到文本编辑的纯文本文件。步骤、预写期望和实际结果位置均已提供；期望复制文本另存为 `expected-copy.txt`，不能拿它冒充实际结果。录屏和实际文本保存到新的 manual 子目录。

代码候选为 `frozen-candidate-01`，源码快照在 [归档](frozen-candidate-01.tar.gz)，当前源码与快照逐文件字节核对结果见 [source-freeze-check.json](source-freeze-check.json)。完整 Git 代码版本由本次本地提交和终端交接行中的完整 SHA 绑定；初始基线见 metadata.json。[独立只读审查](acceptance-review.md) 对本次范围与诚实的 INCOMPLETE 交付返回 PASS；该 PASS 不表示 T-025 已完成，不替代真人操作。

本 worker 仅改自己的 probe、T-025 ticket 和 T-025 证据；未修改 Muster、MAP.md、AGENTS.md、根 README.md 或 CONTEXT.md。地图 Notes 与 intent.md 角色表仍写旧主控名称，本次以用户指定和 AGENTS.md 的 Claude Code 为准，请主控在单独的文档范围中同步。未 push，未修改或重启用户 Herdr server。

结束前 `project_map.py status` 返回 1：结构问题 0，stale living doc 1，为并行 T-027 的未提交 `muster/` 改动尚未同步根 README。原始输出见 [project-map-status-final.txt](project-map-status-final.txt)。本任务书禁止本 worker 改根 README；该项交由主控与 T-027 在各自范围内处理，不能报告地图整体 PASS。T-025 自己没有触及该 covers 路径。

交付检查保留了两类检查异常：规格快照中的相对链接按原始目录解释，不能按证据目录误判后改写原文；全量 staged diff 的空白检查发现四份原始 Cargo stdout 的末尾空行，按原样保留。源码、ticket 与本次起草文档单独检查，原始记录见 delivery-check-anomalies.json。
