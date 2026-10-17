# 单角色 controller 原生转交候选与绿态启动审批

局部实现检查 **PASS**；沙箱外入口回归、新实例静态核对、真实 Claude 绿态及独立审查仍 **INCOMPLETE**。本轮未启动 Claude、假 API 或 Electron。主控 #178 授权的修改限于八个产品文件和测试；README 所有权缺口已上报，不擅改地图或文档标记。

**Tracer bullet**：真实 inbox 客户端写请求文件 → 当前 prompt 的实际 Stop → 原生 caller → 唯一门禁 → 实际反馈进入第二次登记提交。**Deep modules**：扩展原请求 writer、relay 和 caller，不另建 operator 代理路径。**Ubiquitous language**：queued 只表示请求文件落盘；执行结果、根提交、主 Messages 和许可 control action 分别记录。

## 红态、实现与反例

主控 #175 的真实工具结果 `worker_request_directory_required` 和许可 Enter 多记 `turn_submit_intent` 是本次修复的两条真实红态；原场景无 ACK/Stop/idle、主 Messages3/2，仍为 INCOMPLETE／NO_GO。#178 cleanup PASS：API92591 一次 SIGTERM、外置逐成员归档读回，api-error 根按规则保留，slot 未动；[原清理结果](p1-materials-slice1-red/cleanup-175/result.json) 不改写。

controller 使用 schema2：launch、preset、project、task、spec_rev、session、native_session、prompt_id。daemon 在匹配的 UPS 后发布该 launch 的当前 context；实际客户端从 context 写文件，实际 Stop 才转交。caller 核对持久启动记录、当前任务版本／项目、绑定 preset、当前 active／prompt、原生会话及同一 shell／leader，并在原生观察 await 后再核对。controller 不携带 worker attempt/fence；journal 的 attempt 列可空仅表示此记录无 worker attempt，不是伪造执行尝试。原 schema1 worker 与 reviewer 仍沿原通路。

controller_start 在实际 pane 创建后注册其角色及 preset；门禁用真实 caller 的 address，`list --role executor` 不能覆盖 ideation 身份。只开放 controller 的 inbox/stop 请求，worker submit 请求仍拒绝。请求字段／身份不符、旧 Stop、未知处理结果与重复转交保留诊断；不自动重送。

PermissionRequest 必须引用当前 Claude prompt 与 active；同窗口的一次 CR 记录 control action/write，保留原 active，不新增根提交 intent。普通 Enter 仍按用户提交记录。此行为不把工具许可当成用户授权新业务命令。

| 信号 | 结果与边界 |
| --- | --- |
| 实际 inbox producer | [parent 红态](controller-producer-red/results.json) → [当前绿态](controller-producer-green/results.json)；真实库客户端，无 daemon／原生身份结论 |
| #175 原 UPS／PermissionRequest 载荷 | [旧版红态](permission-accounting-red/results.json) → [3/3 PASS](permission-accounting-green/results.json)；执行生产 signal/input 状态路径，PTY 为 spy |
| relay／caller／角色范围 | [22/22 PASS](controller-caller-scope-green-02/results.json)；八个请求身份反例、旧 Stop、假 attempt、撤销／进程更换／await 后变化、worker submit 拒绝和历史迁移；taskspec／project 先取 [局部红态](controller-caller-scope-red/results.json) |
| 不扩大角色权限 | 复核发现 controller 扩展漏保留原 relay 白名单，先取 monitor／unknown [误接纳红态](controller-green-relay-role-red/results.json)，补回原检查后 [2/2 PASS](controller-green-relay-role-green/results.json)；controller22 重跑仍 PASS |
| worker writer 回归 | 新检查误拒 `/tmp` 的 [原失败](controller-green-worker-producer/results.json) 保留；规范路径拼写检查只用于新 controller context，[原 worker 三请求 PASS](controller-green-worker-producer-02/results.json) |
| 局部已有回归 | worker relay（5 次受控 effect、failure=null）、scope5、controller-window5、pane-runtime11、Claude epochs7、inbox-domain11 PASS，分别保存在 controller-* 回归目录 |
| 绿态 API 契约 | [11/11 PASS](controller-green-protocol-contract-02/results.json)：独立双角色 sentinel、请求关联、空结果／越角色／多工具／重放拒绝；[有效预算坏变异](controller-green-protocol-contract-mutant-02/results.json) 仅第四请求条件失败 |

`controller-green-protocol-contract-mutant` 首次第四请求用反馈历史作输入，被另一个条件挡住，错误地 PASS，不能作为预算变异证据；原件保留。第二版改用本来有效的 tool-result 请求，取消预算时该条件确实失败。先前 relay scope 命令参数错误保存在 controller-green-command-errors.json，也不算产品红态。

启动 profile 的两回合预算3项与角色文本参数检查 PASS；后者使用 #175 保存的官方 CLI help，没有重新启动 CLI。首次角色参数探针漏传 help 路径的调用错误原样另存，不作为产品红态；正确结果在 controller-green-role-prompt-02。

## 主控先冻结并运行入口回归

按原启动身份运行 [commit-and-prepare-slice1-green.sh](commit-and-prepare-slice1-green.sh)。第一提交冻结实现、测试、证据和阶段脚本；同一个脚本随后执行 [controller-green-stage.py](controller-green-stage.py)：实际 daemon／window／库 inbox／hook 六项、空框声明入口17、实际 Electron／PTY 的 runtime12、input-failures11、worker-inbox14。原生 process／PTY spy 的部分明确单列，不冒称真实 Claude。新构建必须在外置盘；服务脱离调用进程组，异常即停，超时不发信号／重试，slot 保留。

回归全 PASS 后，脚本才以该代码提交生成 `p1-materials-slice1-green`，逐文件与 Git／源码 tar 读回，检查新 root／HOME／launch／session／thread、空请求目录、空批准字段和未启动状态，再作第二次材料提交。任一步失败保留原输出，后续步骤不执行；没有 launch。脚本执行前，实际新实例及这些入口结果均 INCOMPLETE。

## clean launch 审批范围

生成成功后，主控读 `approval.json`、`control-plane.json`、`static-check.json`，再逐次批准。材料源码绑定第一提交；第二提交只含证据／材料，不改其冻结字节。预算为 **根提交2、主 Messages3、Bash1、供应商模型0**：nonce 根产生 tool_use 与实际 tool_result 两次 Messages；首个真实 Stop 执行原请求，daemon 将真实收据登记为第二根；第三次 Messages 只确认该反馈并结束。禁止重试、新工具、新角色或额外根。

launch 仍使用 Claude2.1.296、Haiku5.5/low、manual、Bash/Read、隔离 HOME／CLAUDE_CONFIG_DIR、loopback 假服务、三种既有 hook 和空 MCP。不写用户全局配置或 auth。launch 输入预算0；下面命令只在主控批准该新实例后运行：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/workbench/tests/run_t078_p1.py --materials /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/p1-materials-slice1-green --phase launch
```

主题／Security notes／目录信任沿原 screen → 主控读原屏 → 单键审批流程。生成器提供 screen-key-approval-template；不因旧实例已信任而放行新实例。看到主提示后主控签 readiness 和 submit-approval，精确 nonce／Bash／预算均绑定本实例。`control-plane.json` 的 continue_driver_argv 只发 nonce，之后等待真实 tool_result 或 PermissionRequest，不默认按 Enter。

出现工具许可时，主控读本实例原始屏、PermissionRequest session/prompt/tool command、dispatch／eventseq，确认光标在 `❯ 1. Yes`，才签 permission-approval 并运行 driver `--phase permission`。驱动通过同窗口一次 Enter，记为 executor 批准的 test-simulated-user control action；无永久 allow／bypass。屏或身份变化、命令不符、键回执不齐即停。

为拒绝“总返回空”或 role 参数覆盖，launch 夹具只播种两条预先声明的 incoming test inputs：ideation sentinel 与 executor sentinel。此为夹具输入，origin 与原内容在 scenario／launch 记录中；不是另一真实角色发送，不调用 operator 代写本次 inbox 请求。API、驱动均不伪造本次 queued request／Stop／执行收据。唯一有效绿态是实际 relay result 返回 ideation 那条，FOREIGN 那条缺席。

实际读回必须：一份 schema2 请求文件、同 prompt 首 Stop、实际 queued tool_result 与反馈 request_id 一致、一次角色范围执行、两组 distinct UPS/Stop exit0、两条原登记 intent 均被 idle 结算、许可键无 user intent、三次 Messages，无 api-error、新业务 send/ack 或第二工具。假 ACK 文本不作为业务成功证据。旧文件在第二 Stop 只回放已知收据，不再执行／反馈。

cleanup 到现场后单独准备、另批，当前脚本不删除新旧 root／slot。完整 8/9/18/CAS 本轮未重跑；09B／09C、真实模型、真登录、独立行为审查和整票交付均 INCOMPLETE。内存约束下未开审查子代理；局部绿态不替独立 reviewer 或实际 Claude 绿态。
