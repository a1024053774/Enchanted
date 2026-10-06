STATUS: PASS

TARGET: `evidence/2026-10-06-m1-batch1/T-026/review-snapshot-artifacts/`，T-026 external-build-entry v2；基线 `5de427ee924943fbcc034feb96e8b23dd2272429`。

EVIDENCE:
- 合同取自冻结的 `evidence/input-brief.md:24`，未读取实现聊天或 ticket Resolution。
- 对冻结入口使用未见输入 `/Volumes/t026-review-unseen-271a5cd271c24ac2a687c42072ed5faa`：退出 2，stderr 精确包含该路径；缺盘目录、随机内置缓存路径及 snapshot 下 target 均未生成。普通目录冒充挂载点也被拒绝。
- `entry-final-path.json` 经过真实 Cargo/build.rs，覆盖被污染的缓存环境、随机子程序参数、目录逃逸和 target 覆盖。生产入口没有导入测试 oracle。
- `zig-install.log` 记录官方发布包安装和实际 `zig version=0.16.0`；冻结入口精确核对版本。官方确有该发布版本。[Zig 官方下载](https://ziglang.org/download/)
- 原始日志确认冷编译 162.06 秒、改单文件后增量编译 49.69 秒。两个并发进程相隔约 1.3 毫秒启动、均退出 0；其中一个明确等待同 target 的构建锁。
- 独立重算三阶段采样峰值，均与 result/measurements 一致；Cargo 输出与中间产物路径的环境变量语义符合官方文档。[Cargo 配置文档](https://doc.rust-lang.org/cargo/reference/config.html#buildtarget-dir)

FINDINGS:
- 未发现限定验收主张内的行为违规。

COUNTEREXAMPLE:
- `known_bad_build.sh` 直接调用 Cargo：缺盘时退出 0 并生成内置 target；缺盘和路径测试均拒绝该反例。
- 修复前入口错误拦截 `--` 后的 `--config`，被 `red-child-path.json` 拒绝；最终入口通过相同场景及新的随机参数测试。
- 新 sentinel 的拒绝信息随外部输入变化，排除了固定缺盘路径输出。

LIMITATIONS:
- 冷编译使用修复前入口。逐字 diff 仅新增遇到 `--` 时停止过滤；冷编译 argv 没有 `--`，因此支持相同构建路径，但 162.06 秒不能表述为最终入口重新测得的冷编译耗时。
- 磁盘峰值是约五秒采样的下界；内置盘空间变化包含系统噪声，不能证明整个系统零写入。
- `check_missing_volume.py:39` 单独只断言非零退出与无 target；本次精确诊断检查、真实挂盘正例和已知坏入口共同补足其证据。
- 未重新执行完整编译；未验证独立 slot 的吞吐收益、Muster/M1 或受管 run。
- 项目地图 status 两次均退出 1：T-024 缺少决策索引，stale living docs 为 0。该问题不属于本冻结候选的行为验收范围。

RULE:
- 不适用。
