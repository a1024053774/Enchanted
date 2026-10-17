# T-093 独立审查请求 02：验收证据修正

task T-093，attempt a1，ready_rev 1，worker s16-t093。
受管 session 67f986cc-92e4-4089-9c22-802a1143b645；原生 session 01a14ae2-a3df-7731-a7b0-1b679b3bce95；launch launch-45148b6732394eccab3b21224b238513。
工具 codex-cli 0.163.0，模型配置 gpt-6.1-sol / xhigh；不声称供应商实际 tier，也不补造 fence。

**当前 INCOMPLETE：两处验收文件修正已做本地检查，完整沙箱外复验与新候选独立审查尚未完成。**
请执行主控按下述脚本取得新运行证据，再安排新的干净、只读 reviewer；本请求不代替 submit、验收、集成或关闭 ticket。

## 冻结对象与变更边界

第一次冻结为 1d4c58b4a83b754b4dda4b2ee4887627e2941358。[独立审查 01](independent-review-01.md) 对它给出 NO_GO；报告原文未改，不上调原结论。
修正候选为 **c34d71a975b59a0db8c1e97bb40c0f7a94e629d1**。
最终对象是包含本请求、RESULTS 更新、独立审查 01 原文、本地驱动检查摘要及 freeze-checks-03.json 的冻结提交，完整 SHA 由本次 `T-093 FROZEN <sha>` 交接。
相对 c34d71a97，复验脚本另把首条漏记的判定收紧为同时要求主失败标记与原记账断言 `ledger must exist before receipt`；生成驱动不变。
请先核对差异仅是上述文档／证据和这条判定，再绑定最终 SHA 审查。

本次没有修改产品源码、gates、acceptance、地图、原生完整链脚本或假 CLI。
修改只有 test_t093_forwarder.ts、test_t093_counterfactuals.py 和新建 EVIDENCE-RECHECK-02.sh；旧 reviewer 的 REVIEW-OUTSIDE-01.sh、02.sh 均保持原文。
修正来源为主控 #77；完整历史及版本边界见 [RESULTS.md](RESULTS.md)。规范仍是 T-092 决定与 T-093 ticket，真实模型在合入后仍须用户另说开工。

## 两处修正与已知证据

| 审查发现 | 修正 | 本地证据／边界 |
| --- | --- | --- |
| 凭据变体为空跳过注入，只由 rmSync 报 ENOENT | 验收输入改由测试独立构造原值、JSON、URL、base64、无填充 base64、base64url；输入非空、文件确实写入、命中 >0、至少执行一项且全部执行都有明确断言。终端公开字节的禁止值与 Git index 模式同样独立，不再依赖生产 credentialVariants／credentialHits 作答案 | counterfactuals-05-red.json 复现旧 ENOENT／未命中业务断言；forwarder-green-04.json 对照通过；counterfactuals-07.json 12 项通过，其中空生产枚举器必须命中 `credential injection must be detected`；空场景、跳过循环、取消写入各有指定断言，fixture_missing_error 均 false |
| 首条请求漏记的业务失败被后面的清理断言覆盖 | 新建驱动保留首个 failure，清理等待不再因 boundaryFailure 短路；清理异常分别写 cleanup_failures，不改主 failure，也不在结果写盘前抛出清理断言 | evidence-recheck-local-02.json：对实际生成驱动在 setup 前强制双失败；旧式未捕获清理错误会丢失主失败，被对照拒绝；修正版同时保存主业务标记和清理标记。该项不启动 PTY/auth/ps，是 L1 驱动回归；真实首条请求漏记仍需下面的沙箱外执行 |

不能仅因退出非零、出现任意 AssertionError、ENOENT、超时或清理出错，就把某个变异记作业务拒绝。
新反事实检查对空枚举器及三个空／未执行注入场景要求精确的断言类别。旧红态、旧审查和旧失败原件保留。

## 需要主控在沙箱外执行

第二个参数必须是本次最终冻结的完整 SHA；脚本要求当时 HEAD 与它一致，自动新建输出，不覆盖旧运行：

```sh
bash evidence/2026-10-16-batch16/T-093/EVIDENCE-RECHECK-02.sh /Users/luckye/Documents/Code/a2a-wt-t093 FULL_FROZEN_SHA
```

此脚本由 worker 派生，不是新的独立审查结论。它只导出指定提交的 workbench 到一次性 /private/tmp/t093-evidence-02-*，编译假 CLI、使用合成凭据和本地假上游，不启动供应商 CLI，不读真实 auth、不连接真实上游。
实际 HOME 只读既定四范围元数据；并发差异仍保留，不归因或自动忽略。后台进程脱离调用者进程组；按本轮登记的 PTY／私有根／夹具收尾，不按全局名字或宽 glob 清理。

执行顺序：

1. 双失败优先级对照：未捕获清理错误的坏驱动必须被拒，修正版保留主失败与 cleanup_failures。
2. 未修改候选的完整链对照与独立三反例对照；无有效对照就停止变异。
3. 首条请求漏记、HOME 引用漏报、凭据枚举器为空、计数恒一致四种单处生产变异；空枚举器另跑候选自己的完成检查。

回读 SUMMARY.json、各结果 JSON、host-home、cleanup 和 stdout/stderr：

- 空生产枚举器的 candidate-oracle 必须是指定扫描 AssertionError，不是 ENOENT。
- omit-first-request 的主 failure 必须包含 independent_upstream_assertion 及原先的记账断言；cleanup_failures 独立保留。原始错误若仍无结果 JSON 或被清理替代，保持 INCOMPLETE。
- 清理状态与业务拒绝分别判定；外层补救删除不能证明内部清理通过。
- 所有实际 HOME 差异照实报告；失败段 host-home 的 INCOMPLETE 可能来自 child 非零，须查看差异列表，不能猜测归属。

本地仅执行过带 `--check-only` 的模式：它在 setup 前验证双失败优先级，并对三种生成驱动做 node --check；不会运行真实 PTY、auth helper、ps 或模型。
该模式 PASS 不代替上述完整复验。完整模式本轮尚未执行，不能宣称四个真实变异都已有效拒绝。

## 新审查的范围

请 reviewer 从票据重建合同，重点核对：独立凭据输入是否实际执行、禁止值是否独立；指定坏实现是否因预定业务断言被拒；首个业务失败与清理信息是否都能留存；驱动是否改变了生产语义或掩盖缺口。
产品源码相对第一次冻结逐字相同，但不把旧报告中的 PASS 部分无条件当作新候选验收。原始完整链及三个独立反例的历史来源、probe-10 三条边界仍见 RESULTS；不能把转发计数说成全部网络尝试。
旧审查认为产品行为未确认有缺陷；本次也不通过扩大权限、读真实凭据或跑模型来补证。

若需要其他沙箱外动作，写成脚本交执行主控，不申请升级，不自行运行 ps 或操作用户其他会话。
worker 冻结后停止修改；最终结论绑定最后冻结 SHA，由执行主控安排后续独立审查及唯一门禁。
