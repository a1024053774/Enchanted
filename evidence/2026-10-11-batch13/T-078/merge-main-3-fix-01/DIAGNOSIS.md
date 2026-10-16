# 主控 #320：T-082 受控宿主的鉴权引导缺失

2026-10-16。**根因定位与不启服务的局部红绿 PASS；真实 T-082 启动/结束回归 INCOMPLETE，待主控在新目录续跑。** 产品代码未改，A-14 现场未访问。

合并提交 `859fd649765e64926c87c7eb69499854b18ae042` 上，主控运行 `merge-main-3-outside-01`：pending/controller、startup 领域与 M5、startup 真实入口与 M5、worker inbox 四段均 PASS。第五段的 tracer 与四个边界变异均在宿主启动阶段失败，不能算 reviewer 业务拒绝。

## 原始证据与根因

宿主 stderr 并没有丢失；原本就写在输出目录，未放在被删除的 q76 scratch 中。例如正例为：

```text
merge-main-3-outside-01/t082-launch/tracer_review_copy/tracer_review_copy/host-01.stderr.bin
```

其他四份在各自的 `launch-boundary-refused-*/launch_boundary_refused/` 下。五份原文全是 `daemon.ts:24` 的 `Error: operator_credential_required`。本目录 original-host-01～05.stderr.bin/start.json 是字节副本，来源及数量见 failure-readback.json；没有改写旧目录或打开归档恢复一个运行现场。

实际入口是 `quality_chain_host.ts`，并不是已自动合并的 `daemon_acceptance_host.ts`。前者由 T-082 的质量 tracer 使用；后者是之前 T-078 已迁移过凭据引导的旧受控宿主。T-082 单独在 main 上运行时 daemon 尚无 T-078 的 operator 启动鉴权，所以旧质量宿主可以裸调 serve。合并后 daemon 正确要求启动方先创建 state 绑定的私有凭据，而 QualityCase 的环境仍没有 A2A_OPERATOR_CREDENTIAL，quality_chain_host 也没有调用真实 createOperatorCredential。拒绝发生在 helper/PTY/门禁创建之前，尚未到 review 副本、启动 argv 或结束核对，没有发现需要裁定的产品语义交叉。

## 最小修复

- QualityCase.start_host 为每次宿主启动分配本夹具内全新的 `operator-<generation>.credential.json`，已有路径直接拒绝；基类仍清除继承的 A2A 身份。客户端与宿主共享这一个明确路径，不沿用外来凭据。
- quality_chain_host 在自己的 state 创建后，调用选定产品源码的 createOperatorCredential，再调原 serve；没有匿名放行、假凭据或旧接口 fallback。reviewer 仍由真实 launch 凭据发 Stop，未改角色业务调用方式。
- 宿主确认退出后才校验并删除该夹具创建的 operator 凭据，删除结果入 cleanup.json。仍存活、路径/模式/state 不符时记录 cleanup failure，保留现场，外层不会归档删除它。凭据正文不会复制到证据。
- 启动失败异常直接给 stderr 路径。run_t082_boundary 在失败用例返回后，把宿主 stderr/stdout/start argv 另复制到该用例顶层的 `host-startup-diagnostics/`，在 run.json 的 host_diagnostics 中列路径，早于外层 scratch 归档/删除。原嵌套日志也保留。

没有改 daemon.ts、core.ts、panes.ts、relay.ts、reviewer 权限、报告格式、完成条件或预期错误码。未修改 T-082 的边界断言与结束核对用例。

## 局部红绿及边界

新增 `test_t078_quality_host_bootstrap.py` 先写失败方式清单，再在未修复的宿主/夹具上运行。它拦截真实 QualityCase 的宿主 Popen，只截断 socket 前的 serve；随后真正执行 TypeScript 宿主入口、产品凭据 API 和受控 PTY 安装器，没有启动 socket、PTY、供应商 CLI 或模型。两代启动均使用外部给定的 foreign 继承身份作为哨兵，期望本夹具自己的新路径；另检查退出后凭据移除及失败日志复制。

`bootstrap-red-01`：exit 1，两代启动均为 path/kind/state/mode=null；失败日志复制清单为空。`bootstrap-green-01`：exit 0，四项 PASS；两代不同路径，mode=0600、state 正确、继承 launch 不存在，凭据在归档前移除，日志字节复制一致。红绿使用同一个测试，scratch 均已删除。真实启动失败已有主控原 stderr，本地探针不替代这个边界，也不证明 reviewer 已可运行。

可重跑的局部命令（输出另选新目录）：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/workbench/tests/test_t078_quality_host_bootstrap.py --output /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/merge-main-3-fix-01/bootstrap-green-02
```

完整续跑命令在 REGRESSION-02-COMMAND.txt；只读路径/语法/先前收据与源码范围预检的实际输出保存在 preflight-01.stdout.txt/stderr.txt。续跑只执行 T-082 tracer＋四个启动边界变异、六项报告与结束核对，不重跑已经通过的四段。

续跑要求产品源码、app、bin 和 package.json 相对上述已测试的合并提交完全不变，只允许四份明确的质量夹具文件变化；保留原四段 PASS 的来源。允许这次夹具修复尚未提交时运行，但会复制四份实际夹具源码到新输出的 fixture-source，记录 HEAD 与先前结果，并在结束时逐字确认这些文件未变。不会把工作树夹具变更冒称为 HEAD 中已有的内容；若先提交，命令也无需变化。

本轮没有运行真实服务回归，不宣称 T-082 或整票验收 PASS。新增的 bootstrap 探针也不是独立审查；真正门禁拒绝、报告与结束行为仍由原有外部用例核对。此类“新宿主漏迁启动鉴权”的重复问题由实际宿主入口的两代 bootstrap 探针机械检出，不能仅靠 node --check 或只检查被选择的产品文件。
