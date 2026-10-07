# T-027 自带测试运行边界

首轮 `scripts/build test` 的完整日志保留为 `engine-tests-01.log`。它没有完整结束：CLI help 测试将进程 SIGPIPE 改为默认处理，后续同进程的关闭 socket 写入测试收到 SIGPIPE，整个 harness 中断。这个进程全局状态路径已由 `platform/unix_common.rs::begin_cli_output` 和首轮停止位置核对；不能将中断后的未运行测试计为通过。

另一个环境失败由 `test-socket-failure-detail.log` 独立复现：统一构建入口为编译器设置的外置盘 TMPDIR 加上上游测试的长 socket 文件名，超过 macOS SUN_LEN。真实引擎探针已使用短 `/tmp/t027-*` 的运行目录。

后续测试仍通过 `MUSTER_BUILD_SLOT=worker-t027 ./scripts/build test --locked --manifest-path muster/Cargo.toml --bin muster --no-run` 构建。已构建的真实 test binary 用 `run_unit_tests.py` 执行：每个顶层模块在新的进程运行，运行时夹具放在短 `/tmp/t027-unit-*`。这是测试进程及运行时路径隔离，没有改 Cargo/Zig 的构建输出、registry、cache 或编译临时目录，也没有删除或跳过测试。每组保存命令、返回码和原始输出。

已发布的 generation 1 `PaneRightClickTarget` 只有一个 wire 值 `herdr`；Muster 的 Rust variant、CLI 参数和显示名称为 Muster。改名不应改变这个已发布协议标识，不添加旧/新双值或 alias，不更新冻结方法的 oracle。只在未来另行协商协议 generation 时才可更换该 wire 值。

checksum 和中文截断测试的固定示例恢复为上游原始字节：这些是独立输入，不是产品界面。全局替换它们会破坏既有 oracle；没有重算 checksum，也没有修改固定答案。

在线更新已禁用，现存的本地 release-note 展示需要说明“Online updates are disabled”，其相关测试按这个合同核对。修改后的测试还将以恢复旧更新指令的已知坏 mutant 验证。

Letta 的一次 hook 捕获测试由真实异常诊断定位为新写的假 CLI 首次执行超过该 hook 的 1 秒预算（`letta-in-place-test-diagnostic.log`），随后共享 mutex 被 poison，污染了其他 integration 测试的结果。没有放宽产品 hook 的 timeout，也没有增加 retry。仅在该测试中预先验证假 CLI 可执行，并删除预备执行的捕获文件，再要求实际 hook 重新生成参数证据；预备输出不能满足原有断言。

第一版分组 runner 忽略了 Cargo 使用 package 目录作为 cwd 的行为，导致相对路径插件夹具缺失；该轮原始失败保留。顶层 `tests::` 在 libtest 中是子串匹配，会意外匹配其他模块的 `::tests::`；修正为逐个精确运行真正的顶层测试。所有测试仍列入列表，不通过 skip 掩盖失败。
