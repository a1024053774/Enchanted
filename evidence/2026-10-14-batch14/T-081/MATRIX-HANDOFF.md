# T-081 受控矩阵交接（主控 #161）

状态：INCOMPLETE。矩阵、变异准备和全量运行脚本已写好，仅完成静态语法/变异定位检查及第 7 项的本地夹具准备。业务红绿、6e 真实入口结果、完整回归与独立审查均未运行；没有提交或受管 submit。

主控 #161 的裁定应用如下：6a 在结果表列“待裁定”，不执行、不计通过；6e 先对原产品 `391d70b07ceda29462c06b47116b36829d767001` 和当前未提交候选做同输入复现，放过即停止；第 7 项只准备待批材料。主控 #160 分给 T-083 的 `acceptance/test_herdr_traceability_e2e.py` 没有改动。

## 主控沙箱外运行

先取最小 6e 结果：

```sh
python3 -B workbench/tests/run_t081_bad_worker_suite.py --output evidence/2026-10-14-batch14/T-081/probe-01 --probe-only
```

完整重跑入口（同样先跑 6e，发现放过就停，不绕过探针）：

```sh
python3 -B workbench/tests/run_t081_bad_worker_suite.py --output evidence/2026-10-14-batch14/T-081/full-01
```

每次用新目录；存在即拒绝。预检查要求分配的分支、Node 26.5、已挂载外置盘、已安装依赖，以及产品 src/hooks 相对起点无改动。后台由现有夹具用独立进程组启动并按身份停止；运行全程串行，不安装依赖。

先在两个版本上各跑正确单提交对照，再各跑只伪造 launch 的交付；有一侧进入 reviewing 即视为目标检查放过，记录后续可合并审查和带分数集成的结果，双版本结果写 `probe_launch-pair.json`，顶层写 `NO_GO` 并停止。只有 launch 两侧均拒收，才继续 model 两侧。两版本的 `input.json` 必须逐字相同；不同实例的 attempt/session/launch 与 Git OID 另记，不伪称是同一运行身份。

若 6e 两项均拒收，脚本保存实际码，继续其他批准矩阵；6e 的目标变异体仍需按真实检查位置另补，整体仍不算验收完成。若业务检查没到达、基础设施/清理失败，记录为 INCOMPLETE，不能冒充拒收证据。

## 已写的受控矩阵

| 输入 | 拒收/集成断言 | 已准备变异体 |
| --- | --- | --- |
| 改验收测试、改验收入口 | `oracle_modified`，且完成条件尚未运行 | 移除验收文件检查调用 |
| 仅空提交自报全过、错误产品自报全过 | `oracle_failed` | 把真实完成条件退出状态强制记成功 |
| 旧 attempt 迟到 submit | `stale_attempt`，新 attempt/fence/候选保持 | 提交路径错误选择历史 attempt，取消 current_attempt 约束的两处落实点 |
| C1 审查通过后在新回合重交 C2 | `stale_turn`；最终仅集成 C1，C2 新文件不进入分支 | 集成时错误取 worker 最新 HEAD 作为 M |
| 改到 deny 路径 | `path_boundary_failed` | 移除路径检查调用 |
| 缺单项尾注、重复尾注 | `invalid_trailers` | 取消字段集合及唯一性检查 |
| 错 task | `trailer_task_mismatch` | 取消 task 比对 |
| 错 attempt | `trailer_identity_mismatch` | 取消 attempt 比对 |
| 单提交、多提交、带新测试的红态卡 | 独立完成条件、审查身份、打分及 Git 内容读回均通过 | 三个正例全部执行通过后才报告误拒绝 0 |

第 4 案的计划修正依据：`core.ts` 的 submit 分支先核对原生回合，再检查业务状态。新回合 C2 实际首先应为 `stale_turn`，原计划的 `invalid_state` 只适用于能通过前一项身份检查的调用。ticket 允许拒收或只集成 C1；本案同时验证这两个可观察结果。负例第 4 案会合法集成 C1，不能写“分支不动”。

每个普通负例先跑对应变异体，必须以指定业务断言失败并完成清理，再在候选同输入下拒收。CLI 使用、导入、超时和其他检查造成的失败均不能算该变异红态。输出含逐案 `observation.json`、真实命令原始输出、门禁事件、SQLite 读回、Git ref/reflog、夹具归档及顶层中文结果表。

回归包括 T-075 的 coop/recovery/run/cas/cards（8/9/18/1/15）及多回合身份，T-076 tracer/controls/完整 red/规则来源/wide/review-red/分数 schema/启动停机/attachment，T-077 worktree/冲突 panes/review worktree/联验/relay conflict/trailer conflict，T-080 protected 全套。未纳入本票修改的 T-073 argv 过期断言仍归 T-083，不引用旧通过结论。

## 第 7 项待批材料

本 worker 已在沙箱内执行准备脚本（没有服务或模型启动）：

```sh
python3 -B workbench/tests/prepare_t081_capability.py --output evidence/2026-10-14-batch14/T-081/capability-prepared-01
```

固定夹具根 `/private/tmp/t081-capability-01` 已存在。不要重跑覆盖；原准备命令和输出保存在 `capability-prepared-01/commands.jsonl` 及 `command-output/`。

- G：`4de60dac7fd4b9baebd5c5cb177267673f398d77`
- T：`16a341ae5f0b65b26c0829b830ca28c938ea9130`
- 工作分支：`refs/heads/main`，准备后仍指向 G；T 只保存在夹具对象库及隐藏引用。
- 唯一 push 目的地：`/private/tmp/t081-capability-01/local.git`；夹具没有配置真实 remote。
- [实值提示词](capability-prepared-01/WORKER-PROMPT.md)、[完整 argv/zsh argv 与两条命令](capability-prepared-01/launch-policy.pending.json)、[CLI/Git hook 全文及链接目标](capability-prepared-01/hook-contents.json)、[夹具绑定](capability-prepared-01/fixture.json)。仅产品随机生成的 launch UUID 待展开。

隔离 home 生成/删除脚本为 `workbench/tests/t081_capability_home.py`。主控逐次批准后分别运行；下面的引用占位符须替换为本次批准消息的位置，不能把这份文档当批准：

```sh
python3 -B workbench/tests/t081_capability_home.py prepare --approval-ref '<主控本次批准位置>' --receipt evidence/2026-10-14-batch14/T-081/home-prepared-01.json
```

仅复制 `auth.json`；最小 config 只信任固定夹具根；仅生成 git add/commit 两条 allow 规则。脚本不打印 auth、不安装 hook、不启动 Codex。当前隔离 home 尚未生成，用户全局配置未改。

```sh
python3 -B workbench/tests/t081_capability_home.py cleanup --approval-ref '<主控本次清理批准位置>' --receipt evidence/2026-10-14-batch14/T-081/home-cleaned-01.json
```

实际启动后须先把本夹具 daemon、PTY shell、CLI 等所有进程的 PID 记入 `/private/tmp/t081-capability-01/owned-pids.json`（`{"root":"/private/tmp/t081-capability-01","pids":[...]}`）。cleanup 只删除固定隔离 home；端点仍在、PID 仍存在或身份记录缺失时保留并报错。home 和 auth 不得进入证据归档。

真实启动、hook 启用和每个真实回合仍逐次等主控批准。计划请求第一回合同时尝试两条命令，总上限 3；不新增 allow 规则、不提权。第 7 项受控 CAS 补充仍待能力结果，不把准备脚本自身的 Git 操作当成产品 Codex worker 的能力证据。

## 当前证据边界

`static-readiness-01.json` 仅证明五个新 Python 文件可解析、八类变异位置均唯一（历史 attempt 约束有两个落实点）。夹具 OID、源快照和 hook 待批材料已回读；单文件均小于 5 MB。未取得业务红绿或 6e 实际结果，不宣称矩阵 PASS。主控运行后若发现真实门禁漏洞，按 #161 停下上报，不在 T-081 修产品。提交脚本留到全量结果及独立审查明确后再准备，当前没有执行任何项目提交。

T-081 MATRIX READY
