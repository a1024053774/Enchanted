# T-026 外置盘构建入口与实测（2026-10-06）

状态：PASS。构建入口、要求的实测、最终入口复测及冻结候选的独立只读审查已完成；本地交付提交包含本报告与证据。

## 范围与身份

任务书全文见 [input-brief.md](input-brief.md)。主控为 Claude Code（`wF:pM`）；本次仅实施 T-026，不修改 Enchanted、`.upstream/herdr` 或现用 Herdr server。原生会话为 `01a111fe-6eb7-7723-9a9d-0b446191b3c7`。任务书未提供 `coop.py` 的受管 attempt/session/fence，本次不声称通过受管交付或运行门禁。

基线为 `5de427ee924943fbcc034feb96e8b23dd2272429`；规格为该版本的 `.project-map/specs/workbench-m1-2026-10-06.md`。Herdr 副本来自完整版本 `c4653a4f10502601ac110b12b2c45a5f7134082b`。启动 argv 请求 `gpt-6.1-sol`、xhigh、Fast，实际供应商 tier 未核对。版本、启动参数、输入和 skill 全文快照见 [environment.json](environment.json)、[skills.json](skills.json) 与 `skill-snapshots/`。本报告所在交付提交保存最终入口、测试和证据；最终入口的执行快照为 [build-entry-final.py](build-entry-final.py)。

## 构建方案

仓库内的 `scripts/build` 是统一 Cargo 入口。先确认外置盘为真实挂载点且与当前仓库所在内置文件系统不同，再设置环境、检查 Zig 版本、创建缓存目录，最后执行 Cargo。缺盘时退出 2，不创建挂载点或 fallback 目录。它覆盖继承的缓存环境，拒绝 Cargo 的路径覆盖参数；`--` 后的应用或测试参数原样转发。

默认外置盘为 `/Volumes/WD-Elements`，缓存根为 `/Volumes/WD-Elements/dev-cache/a2a/`：

| 环境变量 | 缓存根下的路径 |
| --- | --- |
| `CARGO_HOME` | `cargo-home/` |
| `CARGO_TARGET_DIR`、`CARGO_BUILD_TARGET_DIR`、`CARGO_BUILD_BUILD_DIR` | `target/<slot>/` |
| `ZIG_GLOBAL_CACHE_DIR` | `zig-cache/global/` |
| `ZIG_LOCAL_CACHE_DIR` | `zig-cache/local/<slot>/` |
| `TMPDIR` | `tmp/<slot>/` |
| `npm_config_cache` | `npm-cache/` |
| `ZIG` | `toolchains/zig-aarch64-macos-0.16.0/zig` |
| `RUSTUP_TOOLCHAIN` | 固定为已安装的 `1.96.1` |

`MUSTER_BUILD_SLOT` 默认 `default`，只接受单个目录名；`MUSTER_BUILD_VOLUME` 可显式指定另一挂载点或用于缺盘模拟。实际构建脚本读取的环境见 [entry-final-path.json](entry-final-path.json)，期望来自任务书的外置盘约束，而不是导入入口常量。

本项目迁移整个 `CARGO_HOME`：冷态下载完成后 registry/git/元数据实测占用约 144.10 MiB，不能只迁 target。未复制用户凭据、全局 Cargo 配置或已有 Rust 工具链。挂盘且依赖已缓存时可用 `--offline`；没有缓存时离线构建失败，缺盘时始终拒绝，不回退用户的 `~/.cargo`。Cargo 路径设置依据 [Cargo 官方配置文档](https://doc.rust-lang.org/cargo/reference/config.html)。

Zig 使用 [官方发布索引](https://ziglang.org/download/index.json) 中的 macOS arm64 `0.16.0` 包，直接下载、解压到外置盘，未用 Homebrew 安装其他版本。实际 `zig version` 为 `0.16.0`，完整命令和退出码见 [zig-install.log](zig-install.log)，发布信息见 [zig-release.json](zig-release.json)。

## 缺盘与路径反例

没有实际卸载外置盘。`check_missing_volume.py` 为每次运行创建一个不存在的路径和一个普通内置盘目录，向同一 Cargo 调用传入这两个 `MUSTER_BUILD_VOLUME`，要求非零退出且不出现任何 target。

- 已知坏过程 `known_bad_build.sh` 仅执行原来的直接 Cargo 调用；两个场景均退出 0 并在内置盘生成 target，oracle 为 NO_GO，检查进程退出 1。原始记录：[red-missing-volume.json](red-missing-volume.json)。
- 最终入口在两个场景均退出 2，target 列表为空，oracle 为 PASS，检查进程退出 0：[final-missing-volume.json](final-missing-volume.json)。
- 使用随机 nonce 的真实 Rust 夹具，覆盖继承的内置盘缓存环境、非法 slot、指向内置盘的 target 符号链接及 Cargo `--target-dir` 覆盖。最终入口全部通过：[entry-final-path.json](entry-final-path.json)。直接 Cargo 过程未满足这些断言：[red-path-check.json](red-path-check.json)。
- 参数转发初版误拒绝应用自己的 `--config`，失败见 [red-child-arguments.json](red-child-arguments.json)。保留的初版在包含该参数的新检查中仍被拒绝，见 [red-child-path.json](red-child-path.json)。最终入口只检查 Cargo 的 `--` 之前，随机参数实际输出包含 `--config`，同一检查通过。

精确 argv、环境和退出码汇总在 [final-check-commands.json](final-check-commands.json)。重跑时必须使用新的输出目录，例如：

```sh
python3 -B evidence/2026-10-06-m1-batch1/T-026/check_missing_volume.py \
  --entry "$PWD/scripts/build" --output "$PWD/evidence/2026-10-06-m1-batch1/T-026/recheck-missing-artifacts"
python3 -B evidence/2026-10-06-m1-batch1/T-026/check_paths.py \
  --entry "$PWD/scripts/build" --output "$PWD/evidence/2026-10-06-m1-batch1/T-026/recheck-paths-artifacts"
```

将 `--entry` 换为保留的 `known_bad_build.sh` 可复现直接 Cargo 的反例。已知坏过程会有意生成内置盘构建产物，原目录与完整归档均保留；这部分不作为新入口的输出。

## 外置盘冷编译、增量与并发

盘为 USB/APFS 的 WD Elements 2621，挂载点为 `/Volumes/WD-Elements`。任务书将它称为机械盘；`diskutil` 未提供 Solid State 判定，因此性能结论只绑定该实际卷。Rust 为 `1.96.1`，Zig 为 `0.16.0`，构建为 debug、`--locked`、`-j 4`。通过 `git archive` 复制完整固定版本到外置盘，不改上游目录；命令见 [source-copy.json](source-copy.json)。

主冷编译开始时 target、Cargo home、Zig cache、tmp 均不存在，旧缓存被保留在 `probes/T-026-20261006/initial-run-cache/`。没有清空操作系统读缓存。真实入口命令为：

```sh
MUSTER_BUILD_SLOT=t026-clean-20261006 /usr/bin/time -lp ./scripts/build \
  build --locked --manifest-path /Volumes/WD-Elements/dev-cache/a2a/probes/T-026-20261006/herdr/Cargo.toml -j 4
```

测量器精确记录这一命令。再运行相同 slot 不再是冷态；重做冷态需要保留现有缓存后使用新的空缓存和 target。当前测量可由以下命令重建同类型记录，但输出目录须为新的路径：

```sh
python3 -B evidence/2026-10-06-m1-batch1/T-026/measure_build.py \
  --entry scripts/build \
  --manifest /Volumes/WD-Elements/dev-cache/a2a/probes/T-026-20261006/herdr/Cargo.toml \
  --slot t026-clean-20261006 \
  --output evidence/2026-10-06-m1-batch1/T-026/recheck-measurement
```

增量编译前只对副本的 `src/main.rs` 追加一行注释；并发前再对同一文件追加一行。改动见 [source-changes.patch](source-changes.patch)，实际 shell 命令见 [source-mutations-executed.json](source-mutations-executed.json)；[source-mutations.json](source-mutations.json) 保存等效的 `/usr/bin/printf` 重现 argv。并发使用测量器的 `--parallel 2`，启动同一命令两次，启动间隔约 1.29 ms。

| 场景 | `/usr/bin/time` real | 最大 RSS（MiB） | target 采样峰值 / 结束（MiB） | Cargo home / Zig cache 结束（MiB） | 内置盘可用空间前 → 后（GiB） | 退出码 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 主冷编译 | 162.06 s | 1883.25 | 1319.73 / 1319.73 | 144.10 / 260.75 | 22.59747 → 22.61869 | 0 |
| 改单文件后增量 | 49.69 s | 1175.78 | 1682.49 / 1682.49 | 144.10 / 260.75 | 22.61802 → 22.61703 | 0 |
| 同 target 并发，进程 0 / 1 | 52.26 / 48.79 s | 80.23 / 1342.69 | 1682.49 / 1675.23（共享） | 144.10 / 260.75（共享） | 22.61452 → 22.61137 | 0 / 0 |

冷态与增量态的 Cargo home、Zig cache 采样峰值均等于表内结束占用；tmp 所有采样和结束占用均为 0。工具链目录另占 454.43 MiB。结束时整个 a2a 缓存根约 4.47 GiB，包含初轮产物、缓存备份及异常现场；实际 `du` 与 `df` 见 [end-occupancy.json](end-occupancy.json)。

`time` 的 real 值是命令耗时；测量器还包含 `du` 和轮询开销，不能用其结束观察时间替代 real。最大 RSS 是 `time` 的原始字段，不是所有编译子进程同时占用的总和。磁盘占用每 5 秒加扫描耗时采样，峰值是采样下界；内置盘可用空间是全局观测，包含其他进程和 APFS 活动，不能由其微小变化推断精确构建写入量。完整逐次数据与日志见 [measurements.json](measurements.json)、`cold-clean/`、`incremental/`、`concurrent/`。

并发进程 0 日志出现 `Blocking waiting for file lock on build directory`；只有进程 1 的日志出现 `Compiling herdr`。两者还短暂等待 package cache 锁。结论：同 target 的 Cargo 构建会互相阻塞，本次第二个执行者等待后复用结果，不能把两个成功退出当作独立并行编译。多 worker/worktree 使用各自稳定 slot，共享 Cargo home 与 Zig 全局缓存；同 worktree 的重复构建沿用同一 slot。更多 worker 对机械盘的 I/O 影响未测试，本次不宣称吞吐或成本改善。

最终入口另经真实 Herdr 副本的 `cargo run -- --version` 读回 `herdr 0.9.3`，见 [built-cli-version.json](built-cli-version.json)。没有启动或重启 Herdr server。

## 保留的失败、版本边界与后续

初轮 `cold/` 虽成功、real 为 172.26 s，但同时执行的直接 `zig build --help` 编译了构建脚本，并产生了默认缓存。该命令已停止，明确归档其新建内置盘 Zig 缓存和副本本地缓存；位置、出生时间、占用和进程身份见 [help-command-anomaly.json](help-command-anomaly.json)。它们没有删除，主冷编译重新使用空的外置盘缓存，初轮不用于主要结论。冻结候选打包程序曾因漏建目标 evidence 目录而失败，部分输出另存，见 [snapshot-setup-failure.json](snapshot-setup-failure.json)。这些失败不计为构建验收通过。

冷态测量的入口快照为 `build-entry-before-child-fix.py`；最终入口与它的唯一差别是在 `--` 后停止过滤 Cargo 参数，冷编译命令没有 `--`，其挂载、环境、目录和 Cargo build 行为相同。最终入口已重新完成缺盘与路径检查，且增量、并发和 Herdr 版本读回都用最终入口；不把初版的参数检查通过结论移给最终候选。

Enchanted 保持冻结。以后并入 Muster 后，其 Rust 部分使用同一构建入口；独立 npm 构建入口须先做同样的真实挂载检查，再设置外置盘的 `npm_config_cache` 和临时目录。没有修改 Enchanted 仓库或用户级持久配置。

夹具、反例产物与冻结候选全文已保存为 [fixture-and-review-artifacts.tar.gz](fixture-and-review-artifacts.tar.gz)，打包命令与目录清单见 [artifact-packaging.json](artifact-packaging.json)。原目录保留；归档中的测试目录没有 Git 元数据，不作为顶层 gitlink。

独立只读审查为 [PASS](acceptance-review.md)，通过新 sentinel 验证缺盘诊断随外部输入变化，并独立核算磁盘采样。原审查记录中项目 status 因 T-024 缺地图索引退出 1；主控同期补入索引，本 worker 移除自己新增的重复行，保留主控版本。T-024 的“研究实测 PASS、交接与独立审查 INCOMPLETE”原结论没有改变。最终项目检查另存 [project-map-status-final.txt](project-map-status-final.txt) 与对应命令记录，Problems (0)、Stale living docs (0)，未改写原审查或原失败状态。

M1 的 GPUI 探针、Muster 引擎、a2a 三套验收和真实 run 均不属于本 ticket，本次未运行。
