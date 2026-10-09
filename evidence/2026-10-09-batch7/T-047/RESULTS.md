# T-047：门禁 CLI 长时 HTTP 回执

状态：**PASS**；工程验收与一次只读独立审查通过。ticket 保持 open，待主控关闭。

候选：Synara fork `5aaf90ac1406250a037593448725730973849102`，分支 `a2a-t047`，基线 `09fc57f8a67ea2a1ed70397c04e49e9bb4849a5b`。工作区为 `synara-t045`。本次仅修改 CLI 的 run 请求选项及工作台说明，共 2 个文件、5 行。

## 结论与修复

超时来自 **Bun fetch 客户端的空闲计时**。默认配置下旧 CLI 在 360.335 秒报 `TimeoutError`，但同一服务端 run 继续完成。只把客户端 `BUN_CONFIG_HTTP_IDLE_TIMEOUT` 改为 1 秒，失败就提前至 8.195 秒；服务端配置保持相同，仍完成交付。这组对照将客户端空闲计时与服务端处理期限区分开。[Bun 官方说明](https://bun.com/reference/globals/BunFetchRequestInit)给出的默认空闲期限为 5 分钟；本机实际报错耗时以上述记录为准。

修复在 `packages/a2a-gates/src/cli.ts` 对 `run` 设置 `timeout: false`。`wait_seconds` 依照冻结规格只约束成功投递后等待 submit，不能直接作为整个 HTTP 请求的期限。提交等待、验收、集成、回收与原 attempt 绑定继续由原门禁负责，没有新增运行入口或异步结果协议。

指定的 T-046 `events-final.json` 已经能通过 Python 严格 JSON 解析，未发现其中有未转义的字符串控制字符。隔离夹具让真实 oracle 输出 NUL、SOH、ESC、tab、CR、LF，旧实现与候选的原始 events 回执都能严格解析，并保留解码后的控制字符。因此本次没有修改 events 序列化。依据见 [原材料检查](original-evidence-check.json)、[严格 JSON 检查](strict-json-check.json)及各运行目录的原始 `events-*-stdout.json`。

## 入口与独立预期

Tracer bullet 使用实际 `a2a/scripts/gate → cli.ts → /api/a2a → A2AGates → Git/SQLite`。服务端使用实际 `a2aGateRouteLayer` 和 `makeBoundedNodeHttpServer`；只替换原生线程边界，服务注册中不构造 provider。隔离目录都位于外置盘 `instances/t047/`，监听随机本机端口。夹具发布自己的 endpoint 和进程身份供真实 gate 脚本核对。

预期来自 ticket 与 [受管 run 规格](../../../.project-map/specs/supervised-run-2026-10-06.md)，而非实现输出。夹具注册外部 oracle，验收指定的交付文本；随后从真实 `refs/a2a/integration` 读回文本。客户端回执中的 run/attempt 与服务端最终事件及 task 对照。线程完成消息本身不推进验收，夹具经原门禁显式 submit。

## 结果

| 场景 | CLI 耗时 | 结果与证据 |
| --- | ---: | --- |
| 原始 T-046 工作台运行 | 约 360 秒 | 任务书提供的真实失败；本次只读核对既存材料 |
| 旧 CLI，默认空闲期限 | 360.335 秒 | 预期红态：exit 1、无最终回执；服务端 completed，[原记录](red-default/result.json) |
| 旧 CLI，客户端空闲期限 1 秒 | 8.195 秒 | 同类红态；服务端 completed，[原记录](red-idle-one/result.json) |
| 候选，同一缩短期限场景 | 76.285 秒 | PASS：exit 0、completed、验收/集成/回收读回通过，[记录](green-idle-one/result.json) |
| 候选，延迟 610 秒显式交付 | **611.583 秒** | PASS：最终回执、严格 JSON、Git 集成及原 attempt 回收通过，[记录](green-long/result.json) |
| 无 submit，等待期限 2 秒 | 2.332 秒 | PASS：exit 1、run_deadline、非 accepted，[记录](green-deadline/result.json) |
| 原生线程报告权限阻塞 | 0.391 秒 | PASS：exit 1、run_blocked、paused、非 accepted，[记录](green-paused/result.json) |
| 长时 run 期间再次请求 run | 立即返回 | PASS：run_busy；前后 task/attempt 相同，[记录](green-long-concurrent/result.json) |

两次红态的原 `result.json` 仍保存为 INCOMPLETE，并保留完整 stderr、空 stdout、服务端事件和 Git 读回，未改成绿态结论。长时绿态开始时的源码与上述候选提交相同，之后 fork 保持干净。[汇总](run-summary.json)、[候选差异](candidate.diff)。

格式检查、lint、gates 及其依赖的类型检查、相关 Vitest 均 exit 0；Vitest 1/1 通过。lint 报 868 项 warning、0 error，未把 warning 写成零。[命令与结果](checks-summary.json)。未运行全仓测试、桌面构建、模型或正式工作台复验；任务书明确要求隔离验证。

独立验收审查：**PASS**，冻结候选读回、父版本反例、真实入口、Git 引用及控制字符解析均核对通过，无发现。审查耗时中的 614.65 秒为完整夹具过程；表中 611.583 秒为 CLI run 请求。审查范围限本地 HTTP 门禁与受控线程边界，不含 provider、模型或正式桌面部署。[原始审查证据](acceptance-review.json)。

## 重放与保留

实际命令记录在各目录的 `command.json` 和 `result.json`。在 a2a 根目录重放长时场景，使用一个未存在的新 label，避免覆盖先前证据：

```sh
python3 evidence/2026-10-09-batch7/T-047/run-http-proof.py green-long-replay-01 --delay 610 --wait 660
```

同一缩短期限场景：

```sh
python3 evidence/2026-10-09-batch7/T-047/run-http-proof.py green-idle-replay-01 --delay 75 --wait 100 --idle 1
```

红态使用基线版本；[基线 CLI 快照](baseline-cli.ts)保留。夹具与检查脚本为 [http-fixture.ts](http-fixture.ts)、[run-http-proof.py](run-http-proof.py)。完整 Git/SQLite 现场保存在 `completed-fixtures-01.tar.gz`、`red-default-fixture.tar.gz`、`green-long-fixture.tar.gz`，不登记 gitlink。外置盘原夹具亦保留。

仅停止本任务启动的 7 个服务，均退出 0；测试 endpoint 已删除，归档不含 endpoint 或用户 auth.json。[清理核对](cleanup-check.json)。正式工作台和 T-048 checkout 未操作，不 push。模型、CLI、工具及技能版本、启动配置来源见 [运行上下文](runtime-context.json)；启动参数中的 Fast 配置不作为供应商实际 tier 的证明。
