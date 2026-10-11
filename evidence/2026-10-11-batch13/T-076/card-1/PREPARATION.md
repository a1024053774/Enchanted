# T-076-1 红态交接（2026-10-11）

状态：**INCOMPLETE**。主控决定 01 已批准 PLAN、四个 hook 和两回合计划；本轮只准备测试与沙箱外脚本，没有修改产品逻辑、运行后台/模型或提交代码。

实际实施起点：`18235b2c53610c412b5f4ea53e0e6e5c56d35849`。相对计划起点 `ffe7ecb85e9e224d5917183b48754f15ac0c5ba6`，workbench/src、hooks、tests、README 与 acceptance 无差异。红态脚本从实际起点的 Git 对象导出冻结源码，不依赖运行时的 main。

执行主控分别运行下列命令，每个标签必须是尚不存在的目录：

```sh
zsh evidence/2026-10-11-batch13/T-076/card-1/outside-sandbox.sh red-focused outside-red-focused-01
zsh evidence/2026-10-11-batch13/T-076/card-1/outside-sandbox.sh red-mutants outside-red-mutants-01
```

- `red-focused`：真实 Git hook 链的四个实际回合正例应在起点读回 unknown 并失败；缺当前上下文正例仍应输出 unknown。run 与首次 reclaim 两个回执回合场景各应在业务断言处失败，错误为 identity_conflict；新一致性检查器不存在的合同红态另记。脚本核对 failure/error 数量与门禁返回，不把夹具错误计成红态。
- `red-mutants`：先在冻结起点跑离线字节/窗口与构建 guard 对照，再跑五个单点产品变异体，逐项保存原始结果和覆盖清单。前四类使用起点已有的业务断言；缺盘类新补明确的构建入口断言。已能检出的标“已有覆盖”，不能宣称起点全无测试。

两阶段都不调用 Codex，不复制 auth，不修改全局配置。只启动自建后台/Electron，或在 `/tmp` 的自建 Git 夹具中执行钩子。缺盘变异体的写入也限制在已挂载外置盘的专属目录；不真的卸载磁盘、不回退到内置盘。

原始命令的 stdout/stderr、退出码、夹具与源码归档留在各阶段目录；运行错误不覆盖重跑。当前脚本只启用这两个红态阶段；真实回合的实际完整 argv、环境和预算记录会在后续真实阶段保存，脚本头部目前只有已批准的 argv 模板，不能当作运行事实。

本轮静态检查通过：五个 Python 文件可解析、TypeScript host 的 `node --check`、shell 的 `zsh -n` 与 diff 空白检查。尚未取得任何红态或绿态，这些语法检查不证明测试可运行。

静态检查发现一个探针兼容问题：当前 Python 的 `TarFile.extractall` 没有 `filter` 参数。已在第一次执行前修正为只提取固定本地 Git 对象、逐一校验成员/链接不越过夹具根后解包；没有重试或产品兼容分支。该修正不改变业务断言。

获得主控的红态运行输出后，再确认失败位置，按已批准计划开始对应产品修复。若出现新协议/产品失败或无法判定的情况，保留并交主控。
