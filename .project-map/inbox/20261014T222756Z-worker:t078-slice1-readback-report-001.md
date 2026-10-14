---
from: "worker:t078-slice1-readback"
to: "executor"
kind: "report"
reply_to: ""
refs: ["task:T-078-1", "commit:14e19e2bff16eacfcba7ab00bd63906aef42cced"]
created_at: "2026-10-14T22:34:14.319786Z"
schema: 1
title: "T-078 客户端与许可intent红态实证，整场缺Stop且3/2越预算；交修复清理"
id: "20261014T222756Z-worker:t078-slice1-readback-report-001"
---

# 单角色红态现场读回、假 API 修复与清理交接

最早客户端缺陷的真实入口红态 **PASS**，工具许可 Enter 虚记提交的红态 **PASS**；整场 **INCOMPLETE**，主 Messages 预算 **NO_GO（3/2）**。没有 ACK、Stop 或 idle 证据，不能称闭合工具／转交链通过。原 permission/result.json、api-error 与现场均保留，worker 没有续跑、补 ACK、发键、发信号或启动服务。

本实例 source `6a59ef929bbea4b68e28e8c88db57a7e280c390e`，材料 HEAD `14e19e2bff16eacfcba7ab00bd63906aef42cced`；root `/private/tmp/t078-2-p1-slice1-red-z7msieml`，launch `70e18a26-7259-406c-b6c8-3ec5d61cb09c`，session `04b2a6a0-9ede-4b91-a63b-a3cf83b9a182`。假服务、供应商模型 0，操作来源为 executor 批准的 test-simulated-user。

## 只读现场事实

旧 root 的 SQLite/db/wal/shm 逐字节拷入自己的 [database](slice1-readback/database/)，前后两读一致后才查询副本；没有连接或改写原库。API、hooks、PTY、debug、原生 transcript 与窗口快照字节另存 [slice1-readback](slice1-readback/result.json)，原件不覆盖。预算发现已立即通过 Herdr 向主控报警，回执在该目录。

| 观察 | 证据与含义 |
| --- | --- |
| 真实一次根提交 | UPS／turn_start seq53，prompt_id `565e8f4e-227a-4534-a653-2dcf45817d80`，正文精确为注册 nonce；原 intent seq48／dispatch `20422cf6-aa57-477a-985b-65f3edb5ad46` |
| 真 PermissionRequest | seq57，同 session/prompt_id、Bash 和冻结 command；UPS 与 PermissionRequest 的 finished.json 均 exit0／stdout {} |
| 一次许可 Enter | 窗口 `6889b878…` 的请求 `bde22c06…`，seq85 admitted／86 intent(data=0x0d)／88 written；action `2b3fa040…`，form=action、content.action=terminal-key，不是 message；原截图已目视确认光标在一次 Yes |
| 提交记账红态 | seq87 新增 source=user intent，dispatch=`input:bde22c06…`；只有一个真实 UPS，但两条 intent。虚记 intent 已实测；active 替换依据执行到该写入路径及原源码赋值推断，没有后置 pane 快照，不称直接读到内存 active |
| 真 Bash／库客户端拒绝 | API2 中唯一 assistant tool_use 与 user tool_result 同 ID、command 精确；is_error=true，原文本为 Exit code1＋daemon_call_failed／worker_request_directory_required。足够证明该有效 controller 会话的库客户端入口拒绝 |
| 无业务接纳 | requests 空；relay_requests、relay_results、inbox_records、inbox_deliveries 均 0。未到非空请求的 controller_relay_not_enabled，不拿它当本次红态 |
| 假 API 的真实错误 | API2 的 role 序列 user/system/assistant/user/system，结果在 user 的 index3，末条 system 是 token 元数据；旧 validator 错把末条消息当结果载体，抛错，未发 ACK |
| 未闭合 | 原 hooks 只有 UPS／PermissionRequest，无 Stop；turn_end_signal／pane_idle 均无；API2 完成文件／ACK 不存在。不声称原注册结算、转交或 idle 成立 |
| 预算越界 | API.jsonl 三个主 Messages：22:03:42.758884Z、22:04:19.994316Z、22:04:20.000087Z；API3 仍同结果，body.thinking 有变化。debug 记录两次 HTTP400 与 engine turn ended in error；这是原生 CLI 在失败后的进一步请求，没有第二个 UPS，不是新根；3 次仍超过本包 2 次限制 |

缺陷特定红态足够支撑客户端 producer 的对应修复，也足够证明审批 Enter 记账不等于真实原生提交。它不足以证明 Stop 的转交、caller／角色归属或原注册结算；主控 #172 的单角色完整链路仍 INCOMPLETE，新独立 reviewer 未做。

## 假 API 修复与本次原样请求红绿

先运行 [记录请求探针](../../../workbench/tests/test_t078_slice1_recorded_request.py)，输入为原 api.jsonl 的逐字节副本和冻结 scenario：[red](slice1-recorded-api-red/results.json) 的 actual-api2-with-system-tail 失败，错误与原 api-error 一致；其它 ID／命令／预算拒绝条件保留。

修复只按消息序列找到唯一 assistant tool_use 与唯一 user tool_result，并要求 tool 在结果之前、ID／Bash 名／command 精确、非空结果、model／stream／两次预算不变。结果之后只允许 text 的 system 元数据，不裁剪或重写原请求，不忽略晚来的 user／assistant 或重复结果。原样 API2 [green12/12](slice1-recorded-api-green/results.json) PASS；去掉 command 核对的 [有效坏变异](slice1-recorded-api-mutant-command/results.json) 在 changed-command 条件失败。原合成协议 [12 项回归](slice1-protocol-system-tail-regression/results.json) PASS，放宽预算的坏变异仍在第三请求失败。

重放命令（新目录；不连接旧服务）：

```sh
python3 -B workbench/tests/test_t078_slice1_recorded_request.py --api-jsonl evidence/2026-10-11-batch13/T-078/slice1-readback/api.jsonl --scenario evidence/2026-10-11-batch13/T-078/slice1-readback/scenario.json --output evidence/2026-10-11-batch13/T-078/slice1-recorded-api-NEW
```

生成器补输出 screen-key-approval-template.json，使用将生成实例的 launch/session/目录，批准字段空；prepare 静态检查将它列为必需 template。旧包主控写出的模板继续保留 template_origin=executor-written，不补称为原生成器输出。产品文件、role 权限、ID／命令／预算及旧运行结论都未改。

## 本实例 cleanup 脚本

交 [cleanup-slice1-red.py](cleanup-slice1-red.py)，worker 未运行。固定本 root/launch/session 和 API92591／daemon92615／CLI92625／shell92624；核对 input／owner／ready／原 process manifest。C locale，API／daemon 用完整 command 核对精确 script/root 参数；CLI／shell 用 comm 避免带 system-prompt 换行的 argv 污染解析。CLI 原 lstart 及所有当前身份双读相同才行动，变化或未知即 BLOCKED、无强制信号。

只用本 root 的既有认证 daemon_stop 关闭自己的编排／PTY，等待实际 CLI、shell、daemon PID 消失；不手动信号它们或整个进程组。仅允许对核对完整 argv/root 的 API92591 发一次 SIGTERM，双读 lifetime、不重发，等真实 absence；comm 临时改名不替代 absence。API 的启动 owner 原件只有 PID/argv，脚本不补造当时的 lstart；当前归属与本次双读以新 ps 原件记录。

之后删除已退出 fixture 的测试 operator 凭据，将整个 root 直接归档外置盘，沿用已验证的逐成员字节读回／不跟随链接 helper，保留 api-error 和全部失败。默认保留 root；主控明确加 --remove-root 时，额外核对所有 PID 不存在、库存与归档相同才删除这一根。所有 slot 不动。cleanup PASS 不改变整场 INCOMPLETE／预算 NO_GO。

主控可先运行归档并保留根：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/cleanup-slice1-red.py --approval-ref "主控 #175"
```

若本次审定包含归档读回后删除本根，在同一次命令中加 `--remove-root`；已创建 cleanup-175 后不得盲目重跑。输出 p1-materials-slice1-red/cleanup-175，归档 /Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078/p1-materials-slice1-red/cleanup-175/fixture.tar.gz；异常保留现场，先诊断再由主控定下一步。

## 下一步建议

需要一个新实例取得闭合的完整红态：先完成当前清理，再冻结修好的假 API／template，用新 IDs/HOME/nonce 和新逐次批准重跑一次 root1／Bash1／主 Messages2，取真实 ACK／Stop／idle并核对许可 Enter 的结算诊断。旧实例已有 HTTP400／第3次请求，不能修内存服务、补 ACK、续用旧批准或将其改成原跑 PASS。

这不是重新寻找已证实的客户端错误，而是补目前不存在的工具到 Stop 的边界证据。完整红态之后按分配实现，再取新候选绿态与有效边界反例；09B／09C 仍未生成或启动。当前只交修复、原件读回和清理脚本，不自行创建新 CLI 实例或启动服务。
