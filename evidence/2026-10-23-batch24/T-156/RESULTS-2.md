# T-156-2 迁移与删除记录

状态：本地检查 **PASS**；整体验收 **INCOMPLETE**。本地正常路径、7 个隔离反例和删除后的导入检查通过；绑定提交复验、外置盘归档与独立验收尚未执行。执行主控 #42 已裁定 T-090 是日期证据脚本，不算现行入口、不改它，复跑须检出其当时 revision；HISTORICAL.md 已注明。原问题与检索输出保留在 [ISSUE-2.md](ISSUE-2.md) 和 LOCAL-2.json，不把历史引用当作现行导入失败。

任务 `T-156-2`、attempt `a1`、worker `b24-t156b`，起点 `3feb9e5ae4eec88285741b93158b08ae6922a6be`，分支 `exec/t156b`。本地验证针对未提交候选；完整候选版本由主控运行 RUN-OUTSIDE-02 时核对。没有修改产品代码、其他测试断言、地图或任务卡。

## 迁移范围与独立期望

新增 `workbench/tests/test_t156_quality_host_credentials.py`，删除旧 `run_t082_boundary.py` 与 `test_t078_quality_host_bootstrap.py`，在 HISTORICAL.md 记录覆盖去向。期望来自原 bootstrap 第 71～100 行及 COVERAGE.md，没有用产品常量或产品输出生成答案。

| 原检查 | 新测试的检查与边界 |
| --- | --- |
| 真实 QualityCase 两次 spawn；路径不继承外来凭据、不复用两代路径 | `generation-1/2-spawn-path`、`generation-1/2-host-path`：独立预期 fixture 下 `operator-01/02.credential.json`。每代捕获实际 `start_host` 的 argv/env 后，启动实际 TypeScript host。 |
| 实际 host 在 serve 前创建可读凭据 | `generation-1/2-created`、`generation-1/2-readable`；只替换 daemon.serve，真实 host、创建和读取 API 保留。先记录不含 epoch/token 的元数据，再让真实 reader 读取，避免 reader 拒绝掩盖具体属性失败。 |
| kind/state/0600 | `generation-1/2-kind/state/mode`：硬编码契约值 operator、独立 fixture state 的绝对路径、精确 0600。 |
| 不继承外来 A2A_LAUNCH | `generation-1/2-launch-filtered`；输入 sentinel 为 foreign-worker-launch。 |
| close_fixture 清理两代凭据 | `cleanup-failures`、`capabilities-removed-before-archive`；调用真实 close_fixture 后检查返回失败列表与目录残留，再销毁测试独占临时目录。错误元数据与清理诊断保存，凭据 token 不进入证据。 |
| 旧 runner 的失败 stderr 复制 | 随旧 runner 退役；它只守护旧 runner 自有诊断协议，不迁移成平行包装。 |

本次只验证共享测试 host 的凭据基础设施；daemon socket、PTY、真实 CLI 和 reviewer 启动均不在该探针的证明范围。实际模型回合为 0。旧 T-082 正常 tracer 与启动边界的现行守护者仍为 T-152 测试与 runner，未借本次 import 成功称其整组业务通过。

## 反事实与运行证据

完整本地摘要见 [LOCAL-2.json](LOCAL-2.json)。先完成新增测试的正常路径和隔离反例，确认信号有效后删除旧文件；删除后重新运行正常路径和受影响导入。所有变异只修改 `/private/tmp/t156-2-suite-01/*-source/` 的副本，工作树的产品和共享测试未变。

| 变异 | 独立预期失败检查 | 实际结果 |
| --- | --- | --- |
| 删除实际 quality_chain_host.ts 的 createOperatorCredential 调用 | `generation-1-created`（两代均无凭据） | 测试 exit 1，命中预期检查；不是导入或启动失败。 |
| kind 改为 worker | `generation-1-kind` | 测试 exit 1，kind、reader、清理诊断均拒绝。 |
| state 改为固定外来路径 | `generation-1-state` | 测试 exit 1，state、reader、清理诊断均拒绝。 |
| mode 从 0600 改为 0400 | `generation-1-mode` | 测试 exit 1，仅两代精确 mode 检查失败；真实 reader 仍可读，证明检查不只要求无 group/other 权限。 |
| 去掉真实 close_fixture 中 credential.unlink | `capabilities-removed-before-archive` | 测试 exit 1，仅残留检查失败。 |
| 第二代生成 operator-03 | `generation-2-spawn-path` | 测试 exit 1，第二代 spawn/host 两处路径检查失败。 |
| 基类环境过滤保留外来 A2A_LAUNCH | `generation-1-launch-filtered` | 测试 exit 1，仅两代外来身份过滤失败。 |

可复现命令（output 必须不存在，换新路径重跑，不覆盖旧证据）：

```sh
python3 -B workbench/tests/test_t156_quality_host_credentials.py --output /private/tmp/t156-2-green-01
python3 -B evidence/2026-10-23-batch24/T-156/run_credentials_suite.py --output /private/tmp/t156-2-suite-01
python3 -B workbench/tests/test_t156_quality_host_credentials.py --output /private/tmp/t156-2-post-delete-01
```

前后两次正常路径均 exit 0、18 项 PASS。suite exit 0 表示正常路径通过且 7 个变异均以 exit 1 命中指定失败检查；不把变异的 INCOMPLETE 当产品失败。每案两代 host 都到达 socket 前的观察点，并且探针临时 fixture 已清理。

删除后导入 `test_quality_chain_e2e`、`test_t082_review_boundary_e2e`、新测试，并以非 main 名称加载 `evidence/2026-10-23-batch23/T-152/run_suite.py`，exit 0。精确命令在 LOCAL-2.json 的 affected_imports。现行 `workbench/scripts/acceptance` 无残留 Python 导入；全仓仍保留 T-090 的历史引用，按主控 #42 裁定符合现行入口的验收范围。

## 主控接续

[RUN-OUTSIDE-02.py](RUN-OUTSIDE-02.py) 已准备，worker 不运行、不提权。主控在本 worktree 运行：

```sh
python3 evidence/2026-10-23-batch24/T-156/RUN-OUTSIDE-02.py --revision <完整候选提交号>
```

它要求 HEAD 与显式提交相同，相关代码和脚本已提交；重跑正常路径、7 变异、受影响导入与两级检索，保存 OUTSIDE-02.json；外置盘必须挂载，原始 run/源码副本和现有三份本地原始现场复制到 `/Volumes/WD-Elements/a2a-evidence/2026-10-23-batch24/T-156/`，核对文件数与字节数，写 OUTSIDE-02.archive.json，不计算校验值、不覆盖旧证据。脚本保留原始 /private/tmp 目录供主控检查。仅允许主控 #42 已裁定的 T-090 历史引用；新增其他残留导入仍使总状态 INCOMPLETE。

首次 `git add --sparse` 被沙箱拒绝，exit 128，原因是共享 Git 元数据的 `index.lock` 不可写。执行主控 #42 随后明确授权仅为 `git add --sparse` 与 `git commit` 发起一次提权请求；没有把此授权扩大到测试、归档或其他沙箱外运行。

依 behavioral-acceptance-review 技能，独立验收必须针对冻结候选在新只读上下文中进行；worker 的本地红绿不能代替主控新开的 reviewer。本交付没有自行派出绕过受管任务门禁的 reviewer。
