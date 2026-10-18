# T-093 产品平级 profile 候选交接 06

**INCOMPLETE：产品已改造、局部检查通过；完整新链及变异仍待主控沙箱外运行。不得据此验收、集成或关闭。**
task T-093 / attempt a1 / ready_rev 1，worker s16-t093；受管 session 67f986cc-92e4-4089-9c22-802a1143b645，native session 01a14ae2-a3df-7731-a7b0-1b679b3bce95，launch launch-45148b6732394eccab3b21224b238513。
最后 FROZEN SHA 绑定当前源码与命令，不代替受管 submit、独立审查或集成回执。九项尾注由提交钩子生成。

## 已核实的外部事实

主控 #84 的 [parallel-profile-01.json](parallel-profile-01.json) 绑定 1243d810a72cde3bf76c0595901c6443dcf665e9。
C/F/U/S/M/CLI 子进程的真实 HOME 新文件拒写、F 的单监听／单上游／只写记录目录、C 绕过 F 拒连、F/U 禁 fork 与 Security 1100、合成本地配置正例和删规则变异均成立。
原结果仍是 rc 2／INCOMPLETE：primary_failure=null，U_closed 已存在，后清单丢失；cleanup_failures 两项为 endpoint_shutdown_unconfirmed 与 after_inventory_unavailable。主控另述事后 ps 无残留；worker 未执行该外部 ps。

U 的原始收尾 stderr 随旧临时根删除，无法断言具体异常。本次移除服务结束后的 Node→Python exec：U 在同一个受保护 Python 进程内服务、收后清单，完成后才确认 closed。profile() 的 AST 与 1243d810a 逐项相同，没有放宽旧探针规则。
局部合成测试验证后清单失败时不能产生 closed；重建“先 closed 后采集”的变异，由 U_closed_must_include_post_inventory 断言拒绝。新的 JSON 握手完整写入后才原子发布，不能用半写文件作为 ready／closed。

另一个已复现的收尾风险是目录在 stat 后、枚举前消失：旧清单函数抛 FileNotFoundError。现在保留此前元数据并明确标 missing／vanished_before_enumeration；PermissionError 仍传播、不能伪称完整。inventory-race-red-01／green-01 保存了这个独立合成反例；不据此断言旧 U 一定因此失败。

## 产品实际改造

- R 只精确读取一次原始 auth，复制 claudeAiOauth 至私有 HOME；生成最小 onboarding／项目信任状态，不复制其他内容。以 OS 账号 HOME 为准，不信任 HOME 环境变量。输入目录、launch UUID、CLI 路径和 audit 规范路径在写入前核对。
- F 独立施加 profile，复用 ClaudeForwarder；只监听配置 P、只连显式固定 IPv4 与 URL 端口，不查 DNS、不换地址、不跟随重定向或重试。TLS 仍验证原 URL 主机。日志逐条先写并 fsync，再发往上游。
- C 根直接 exec 原 daemon；为本次 root 创建操作凭据，随后仍走相同 controller_start／hook／Stop。版本、auth status、PTY、CLI 与 hook 都继承 C；删除内层 sandbox-exec、daemon 内原始 auth 读取与内置转发服务。
- 一次准备只可消费一次；并发第二个 start 在取得资源前失败，不能清理第一个 start 的 HOME/F/D。
- D 是独立、无网络／Security／fork 的 Python 清单与清理 helper，先于持有凭据副本的 F 启动。端点先等待自身 bootstrap 登记，再执行角色工作。只读四范围目录/stat，HOME 文件正文禁止读取（程序源码除外）；快照仅存私有根。C 输出脱敏差异后，D 核对本次登记的 PID/组并删除整个私有根。失败、取消和未确认清理分开记录。
- 事实 schema 2 重数 forwarder/journal/requests.jsonl；真实 HOME 清单只报告、不作通过条件。新事实命令不重读原始 auth，不自动批准／拒绝模型回合。
- 基线由一次短 D 进程在原始 auth 读取前采集；输入前事实单列 preflight.json，F 提供历史入口计数，C 记录准备参数/环境引用、扫描及“结束对比 pending”。`--stage facts --preflight --audit DIR` 是外部 V 入口；C 内部事实子进程直接继承 C，不嵌套 profile。
- 元数据序列化的额外缺口已取得 journal-red-01／journal-green-01：方法字段和数值字段含凭据时，写盘前也脱敏，保留可解析 JSON。该局部测试没有监听或发请求。

## 进程及 profile

新链尚未运行，以下是启动路径，不是伪造的 PID 证据；实际 PID／PPID／进程组及相同源码下的系统调用结果由各输出填写。

| 进程 | profile／生命周期 |
| --- | --- |
| R 初始准备 | 仅参数／FD／临时目录、原始凭据读取在业务 profile 之前；无长期未保护监督进程。关闭额外 FD，拒绝 HOME 内 stdout/stderr |
| Git 版本／索引检查 | G，禁写真实 HOME、禁网络、禁 Security；只读检查，关闭 optional locks，凭据变体只走 stdin |
| U/F/D/S/M 短脱离 helper | 先 setsid/fork，随后独立施加各自 profile 执行 true 并退出；helper PID、profile、退出码单列 |
| F Python→Node，同 PID | 单次 F；禁写真实 HOME，只写自身 forwarder 目录，单 P 监听、单配置上游出站，禁 Security／fork |
| D Python，同 PID | 单次 D；只写私有根与自己的收据目录，禁写真实 HOME、禁出站／Security／fork；完成后清理私有根 |
| 读取原始 auth 前的基线进程 | 短 D，独立施加一次并等待退出；PID 与进程组在 initial_inventory_process/baseline 中单列 |
| C daemon 根 | R 的同一 PID exec 单次 C；禁写真实 HOME，保留读屏障，TCP 仅 F，Unix 仅本次 control.sock；允许原生 fork/exec |
| PTY helper→zsh→编译假 CLI | 继承 C；该组全部结束才收集最终事实 |
| fixture Python、原生 Node hook/inbox、ps、clang、事实 Node | 继承 C；Node 启动及其他实际 child PID 分别记录，不记 argv/env/凭据 |
| 测试 U Python | 独立 U，只监听两个明确本地测试端口、只写 U 目录，无出站／Security／fork；不再回 exec Node |
| 测试 S/M Python | 各自单次应用产品 C 规则；S 额外禁写合成 HOME，M 只删这条合成规则，保留真实 HOME 保护 |
| 结果核对器 | 独立 V，禁写真实 HOME、禁网络／Security；只读六个结果，不导入产品事实函数 |
| 操作者的外部事实命令 | 单次 V，另保留 HOME 读取屏障，只读当前原件与选定阶段的事实；不读取 auth |

F/D/U 与 CLI 均非父子链。新链没有真实供应商 CLI、真实登录读取、真实上游或模型回合；只有合成 auth 的一次原始文件读取。

## 主控沙箱外命令

在本 worktree 中设置两个任务变量；SHA 使用最后的完整 FROZEN 值。每条命令分别执行，所有路径必须是新的，日志只放真实 HOME 外。

```sh
t093_repo=/Users/luckye/Documents/Code/a2a-wt-t093
t093_candidate=FULL_FROZEN_SHA
```

先核对原探针收尾（没有修改旧输出）：

```sh
bash evidence/2026-10-16-batch16/T-093/PROBE-PARALLEL-01.sh "$t093_repo" "$t093_candidate" /private/tmp/t093-parallel-profile-02.json
```

再跑新产品链。none 期望 rc 0；另外五条期望 rc 2，并且主失败必须为表中业务断言，清理错误必须为空。

```sh
bash evidence/2026-10-16-batch16/T-093/EVIDENCE-RECHECK-03.sh "$t093_repo" "$t093_candidate" /private/tmp/t093-chain-04-green.json none
bash evidence/2026-10-16-batch16/T-093/EVIDENCE-RECHECK-03.sh "$t093_repo" "$t093_candidate" /private/tmp/t093-chain-04-home-mutant.json home-references-empty
bash evidence/2026-10-16-batch16/T-093/EVIDENCE-RECHECK-03.sh "$t093_repo" "$t093_candidate" /private/tmp/t093-chain-04-scan-mutant.json scanner-zero
bash evidence/2026-10-16-batch16/T-093/EVIDENCE-RECHECK-03.sh "$t093_repo" "$t093_candidate" /private/tmp/t093-chain-04-count-mutant.json counts-always-match
bash evidence/2026-10-16-batch16/T-093/EVIDENCE-RECHECK-03.sh "$t093_repo" "$t093_candidate" /private/tmp/t093-chain-04-first-mutant.json drop-first-record
bash evidence/2026-10-16-batch16/T-093/EVIDENCE-RECHECK-03.sh "$t093_repo" "$t093_candidate" /private/tmp/t093-chain-04-empty-mutant.json empty-credential-cases
```

| 场景 | 必须出现的主失败 |
| --- | --- |
| none | null；原件与独立上游均两次，状态 400/200，原生 Stop 动态哨兵只交付一次 |
| home-references-empty | home_path_injection_must_be_reported |
| scanner-zero | credential_injection_must_be_detected |
| counts-always-match | missing_raw_request_must_be_detected |
| drop-first-record | forwarder_record_count_must_match_upstream |
| empty-credential-cases | credential_injection_cases_must_not_be_empty |

变异仅在 /private/tmp 的源码副本生效；导入／依赖指向完整快照，不修改工作树或门禁。首条漏记保留对账主失败，清理另列；空注入必须由业务断言拒绝，不能靠 ENOENT。每次运行后删除整个私有 HOME 及合成夹具，只在结果中保留小型原件记录／反例。

最后用不导入产品函数的核对器独立重数、核对八个 HOME 反例路径、三个原反例、删规则创建／删除、两个拒连反例及六个场景分类：

```sh
python3 -I -S -B workbench/tests/check_t093_chain_results.py --candidate "$t093_candidate" \
  --output /private/tmp/t093-chain-04-verdict.json \
  /private/tmp/t093-chain-04-green.json /private/tmp/t093-chain-04-home-mutant.json \
  /private/tmp/t093-chain-04-scan-mutant.json /private/tmp/t093-chain-04-count-mutant.json \
  /private/tmp/t093-chain-04-first-mutant.json /private/tmp/t093-chain-04-empty-mutant.json
```

核对器只有全部场景满足外部预期且无清理问题才返回 PASS；它不是模型调用放行器。

## 边界与未完成项

probe-10 三条边界继续有效：hasCompletedOnboarding／项目信任都是 2.1.302 内部状态，换版本必须重新核对；两个 onboarding hello 不经过 BASE_URL，状态必须避免触发，事实分类终端／私有 debug 预检信号；400 后的 CLI 重试也须计数。本次完整假 CLI 明确模拟一次失败后重试，不声称又跑过真实 CLI。

产品严格禁写整个真实 HOME；需要写入的工作区与 Git 元数据也须在 HOME 外。专用 C 只允许 F，不证明多供应商子 CLI、实际 Git 集成或 GUI 场景。本票不修改门禁、全局配置、其他任务或旧审查报告。
真实上游 DNS／TLS、实际新生命周期的供应商 CLI、真实模型回合均未运行。沉默的被拒连接尝试未测量；OS 拒绝直连，不能据转发记录推断所有网络尝试。前后清单差异不推断因果，按裁定 A 不作通过条件。

当前已有局部逻辑通过和旧边界外部证据，尚无本候选完整 OS 绿态；原 independent-review-01、PARALLEL-PROBE-REVIEW-01 与全部失败保持原文。
