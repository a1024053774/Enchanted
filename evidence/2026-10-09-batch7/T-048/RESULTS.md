# T-048：项目标题与启动器身份格式

**PASS（worker 实现与隔离验收）；待主控关闭。** 正式工作台尚未迁移，不以隔离通过代替正式重启证据。

| 交付身份 | 值 |
| --- | --- |
| 任务书 / 规格 | [brief-T-048](../brief-T-048.md)、[T-048 ticket](../../../.project-map/tickets/T-048-project-title-and-legacy-identity.md)，含 2026-10-09 主控补充 |
| Worker / 主控 | `s7-t048`，`wF:p1D` / Claude Code，`wF:pM` |
| a2a 起点 | `1e7c3ffb33f3c0f5d95034c27ee566b282ef9b34` |
| fork 起点 → 候选 | `09fc57f8a67ea2a1ed70397c04e49e9bb4849a5b` → `42376b018616d56a2f0774913bf85c7a9cf82940`，分支 `a2a` |
| 请求配置 / CLI | `gpt-6.1-sol`、`xhigh`、`service_tier=fast`；Codex CLI `0.162.0`；供应商实际 tier 未核实 |
| 运行环境 | macOS arm64；Bun 入口 `a2a/scripts/bun`，Node `24.13.1`，Vitest `4.1.10`；缓存、测试 Git 夹具在外置盘；完整元数据见 [session.json](session.json) |
| attempt / session / fence | 任务书未提供；未自行创建或接管门禁 attempt。此报告是 worker 交付，不是门禁验收/集成收据 |

## 修改与证据

- `service.ts` 直接使用 create 请求已有的 `project` id 命名新项目；不增字段或平行接口。已有项目直接读回并保留原名，仓库不匹配仍拒绝。**Ubiquitous language** 沿用项目、任务、agent 会话；任务 `title` 不当作项目名。
- `launch-workbench.mjs` 与 `workbench_runtime.py` 都在 `LC_ALL=C`、`LANG=C` 下采集完整的启动时间与命令；删除全部 locale 遍历。**Deep modules**：沿用原身份读取入口，不引入新包装或兼容路径。
- 新项目验收走真实门禁 `call(create)` → 原生 orchestration engine → SQLite projection → `getShellSnapshot()`。这是保留在生产路径上的 **Tracer bullet**；未启动 provider。两个不同项目输入、已有项目和错误仓库场景的读回见 [title-green-proof.json](title-green-proof.json)。前端既有 `storeNormalization.ts` 将项目 `title` 映射为 `name`，`Sidebar.tsx` 使用 `project.name`；本轮没有 UI 截图。
- 身份 oracle 执行实际 launcher，只有 `require("electron")` 返回值替换为临时 shell 可执行文件；spawn、真实 `ps`、JSON 写入和 `workbench status` 全部走生产代码。覆盖 4 种 locale、2 种独立 `LC_TIME`/`LC_CTYPE` 组合、中文可执行文件路径、0600 记录、36 个写读组合、其他进程身份拒绝和已退出 PID。
- T-046 的旧中文记录正例改为拒绝正例：主控已要求合并前以旧代码停止，合并后重启写出规范记录，因此继续识别非规范旧记录不再是当前合同。字节上已等同 C 输出的旧记录仍可通过完整身份比较。

| 检查 | 结果与原始证据 | 退出码 |
| --- | --- | --- |
| 项目标题红态（父版本） | 固定 `a2a pagination` 被期望 `release-catalogue` 拒绝，[日志](title-red-setup.log) | 1 |
| 身份首轮验收脚本异常 | GB2312 stderr 的严格 UTF-8 解码失败；[错误摘录](identity-red01-harness-error.txt)。不计作产品红态；原空输出 `identity-red.json` 保留 | 1 |
| 身份有效红态（父版本） | 50/61 通过，5 个实际写入结果不规范、6 个旧记录误接受，[完整输出](identity-red02.json) | 1 |
| 项目标题与已有门禁服务测试 | 11/11 通过，[日志](title-service-green.log)、[快照](title-green-proof.json) | 0 |
| 同一身份 oracle 绿态 | 61/61 通过，[完整输出](identity-green.json) | 0 |
| 格式检查 | 首轮仅新测试格式失败并保留；格式修正后 [复验](fmt-check02.log) 通过 | 1 → 0 |
| lint / 同步文件系统检查 | [日志](lint.log)：0 errors、868 warnings；脚本参数只转发到最后的检查，oxlint 实际扫描了 4040 个文件。未将这些未逐一核对的 warnings 宣称为已解决或已证明基线问题 | 0 |
| 服务端 typecheck | [日志](typecheck.log)，`--noEmit` | 0 |
| Windows runtime 边界静态检查 | [日志](windows-runtime.log)；不代表 Windows 实机运行通过 | 0 |
| 项目地图 | [status](project-map-status.log)：Problems=0，stale living docs=0 | 0 |
| 独立验收审查 | [结论](acceptance-review.txt)：worker 声明范围 PASS；只读审查独立复跑身份 oracle 61/61。标题依赖已保存的真实投影证据，没有 HTTP/CLI 到 UI 的完整验证 | 0（身份 oracle） |

完整命令、工作目录与退出码见 [commands.json](commands.json)。标题验收根目录保留，连同相关服务测试的 12 个 Git/门禁夹具完整归档为 [fixtures.tar.gz](fixtures.tar.gz)，路径见 [fixtures.json](fixtures.json)；没有把夹具登记成 gitlink。skill 原文与文件版本信息见 [skills.json](skills.json)。

在 fork 根目录复跑项目标题与相关服务测试：

```sh
A2A_SYNARA_SLOT=t048 ./a2a/scripts/bun run --cwd apps/server test src/a2a/project-title.test.ts src/a2a/service.test.ts
```

在 a2a 根目录复跑已交付的身份 oracle：

```sh
python3 -B evidence/2026-10-09-batch7/T-048/workbench_identity_oracle.py /Users/luckye/Documents/Code/synara
```

## 主控收尾与边界

- 正式工作台、正式数据、endpoint/token、用户 Codex/Claude home 均未操作；未执行 `build:desktop`，未改 dist，未调用产品模型，未 push。只结束本 oracle 创建的子进程；临时身份目录清理后原始记录留在 JSON 中。
- 当前 checkout 的新读取代码会拒绝正式工作台已有的非规范记录。主控须按任务书用父版本停止，再完成合并/更新，再启动核对新记录。实际正式重启、桌面 UI、正式门禁传输及集成未验证，ticket 保持 open。
- 按任务书“a2a 只提交你的证据与 ticket Resolution”，`acceptance/workbench_identity_oracle.py` 已更新并验证，但不纳入本 worker 的 a2a 提交；完整 [oracle 快照](workbench_identity_oracle.py) 与 [patch](workbench_identity_oracle.patch) 在证据提交中，实际源文件改动留给主控收尾。主控可单独收录，不必重写测试。
- 未跑全仓测试或全仓 typecheck；未改迁移。候选没有增加异常处理、fallback、retry、兼容分支或平行 API；本轮删除原兼容路径。
- 完成检查点的只读 behavioral-acceptance-review 在新上下文中审查冻结候选，结论见 [acceptance-review.txt](acceptance-review.txt)；它只审上述 worker 声明，不替主控关闭 ticket 或授权正式操作。
