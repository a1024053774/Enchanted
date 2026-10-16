# 主控 #339：rev2 测试工具交接

这是未绑定运行现场的工具提交。业务源码没有改变；没有启动真实 Claude/Codex、Electron、daemon、模型或真实业务目标，没有合并 main，也没有生成源码冻结包。A16／09C 的实际 owner、claim、launch、原屏签字和版本绑定仍等 T-090 合并后生成。

## 原件采集与回收

实现位于 `workbench/tests/t078_raw_retention.py`。

- 假 API 的 `HttpExchange` 在校验前以实际序号存 request.bin；meta 保留 method/path/content type、原长度、时间，完全不接收认证头值。逐块保存实际尝试写出的 response.bin、确认写出的字节数；409、拒绝、未完成和重试不被过滤。没有完成的响应明确 complete=false。
- collector 只遍历两角色 http-exchanges/hooks、两份 NDJSON、目标 baseline/final 和 owner 明列的证据树；不遍历 HOME、认证文件或整个 root。原始 hook 的 started/stdin/stdout/stderr/finished/tmp 都按实际文件留存，不从预期事件列表挑选。停机前以一个只读事务导出八类实际表行，关闭连接；不归档 SQLite/WAL/SHM。
- 先按敏感 JSON 值（也含 data/body_raw 里的嵌套 JSON）和显式 secret inventory 定点脱敏。保留其余字节及原/新区间映射。必须有 root/retention-secrets.json；秘密清单本身不入包。二进制/SSE 中的非结构秘密靠这份清单匹配；签 owner 前必须把本场所有 capability/API 凭据值纳入，不能把空清单当一般场景的证明。
- 外置 tar 逐成员集、类型、链接目标与普通文件字节读回。成功之后才生成每个逻辑原件的 `.archive.json` 与 bundle；CLI 同时把可入库的指针复制到 output/archive-pointers。不得只有 summary。没有调用 hash。
- finish 在副作用前要求独立方从 tar 重数的签字收据、原件集/字节稳定、原 Stage A/claim、实际 B1 manifests、原进程身份收据、九 PID 完整 argv/lstart 双读和进程图一致。然后独占、fsync shutdown-intent，再认证 daemon_stop、确认七受管进程退出、两原 API 各一次 SIGTERM。任何身份未知或退出超时都 BLOCKED，不重发、不 SIGKILL。
- 停机后只比较 tar/暂存文件/HTTP/hook 文件清单与字节，不再打开 SQLite。daemon 的 socket/PID 文件必须消失。新/变原件（包括晚出的 finished）阻止删 root；另经主控批准处理尾部，本工具没有自动补漏或 summary fallback。

运行接口（下面是字段契约，**不是已填值的 A16/09C 启动命令**）：

```text
python3 -B workbench/tests/t078_raw_retention.py --mode finish --dry-run --owner OWNER.json --approval CLEANUP-APPROVAL.json --archive EXTERNAL/scene.tar.gz --output NEW-DRY-RUN
python3 -B workbench/tests/t078_raw_retention.py --mode capture --owner OWNER.json --archive EXTERNAL/scene.tar.gz --output NEW-CAPTURE
python3 -B workbench/tests/t078_raw_retention.py --mode readback --archive EXTERNAL/scene.tar.gz --output NEW-READBACK
# 执行主控从实际包独立读回并签 readback.json、cleanup 批准后：
python3 -B workbench/tests/t078_raw_retention.py --mode finish --owner OWNER.json --approval CLEANUP-APPROVAL.json --archive EXTERNAL/scene.tar.gz --capture-result NEW-CAPTURE/capture-result.json --independent-readback NEW-READBACK/readback.json --output NEW-CLEANUP
```

owner 明确 scene=A16/09C、source/40位 source_revision、原 stage_a、完整原 claim_binding；target_binding 是该 claim 的 task/attempt/session/fence/spec_rev/thread/workspace，加 runtime_identity.launch，不编造字段；processes 是九个 `{pid,started,command}`，由 identity_receipt 原件固定，另有按 label 的 process_graph（每项只含 ppid/pgid/tpgid）。roles 包含两份实际 manifest 路径及 launch/session/native session。还需 target_bytes、target_baseline（root 内真实文件）与 evidence_trees（明列且无符号链接的目录）。CLI 不接受 REHEARSAL owner；它只在函数级确定性测试中使用。

外置 capture 必须在 `/Volumes/WD-Elements/a2a-evidence` 的新目录；未挂载报错，不回退。finish 的 dry-run 不读 archive/capture-result、不捕获、不停机、不删。正式回收前独立读回不是 collector 自签；测试中的 executor 签名都明确只针对确定性夹具。

## 09C 驱动与协议

实现位于 `workbench/tests/t078_09c_driver.py`，复用现有 phase_registry、协议 core、`p1_output` 和 ElectronClient。真实 API 仍只有 `t078_09b_fake_api.py` 一个服务入口，C 是显式 phase-plan profile；没有第二套 HTTP 服务或兼容 fallback。当前新服务/prepare/I1 入口只认 `rev2-raw-c-profile-v1` / `rev2-registered-raw-v1`，防止把旧进程当成新代码。旧材料原件不改、新冻结尚未生成。标准 prepare 已加入两个新运行模块的闭包。

1. 两角色独立首启、各自 readiness 后，用 C-I1 的 initialize 检查两者 unknown/空队列/0 POST，再初始 release；不向首启屏输入业务内容。每阶段各有角色/launch/session/target/source 的独立签字批准；arm 仅登记。
2. start 仅允许 C-I1，经真实 pane_dispatch 返回的 `dispatch` 对象、实际全局 seq 与仅去末尾 CR/LF 的正文核对，记录 test-simulated-user window-stop-request，再 pane_release。独占 body/action 文件禁止不确定派发后的重复 start。其他四根只能由真实 inbox/gate feedback 到达。
3. phase resolver 只从实际 launch、dispatch_queued/turn_submitted、inbox stop 与原 request 对应的 feedback 判阶段。C-I1 下发 Bash.command 的 send；C-I2/C-I3 是同一实际 stop/target 的 gate stop；工具结果先结算原生 queued 回执，业务成败只来自 Stop/relay，不在假 API 编造错误。
4. C-E1 只有一个 held POST，SSE 注释 heartbeat 不算额外 POST，不发 tool/ack。真实 C-I3 oracle 验证 ideation 中断与目标字节后写绑定的 hold-release，才中性结束该流。角色每个真实 POST（包括错误）均计数；C 上限 I7/E1，阶段为 2/1/2/2/1。
5. I1、I2 的权限仍用现有 `t078_09b_i1_permission.py` 的完整读屏、一次 awaited Enter 和真实 control action 回执，结算分派到 C oracle。C-I3 的 permission 模式使用已构建的隔离 Electron，保持同一窗口，写实际原屏/模板供执行主控签字；不在两分钟附近临时 build。模板字段、完整原屏、窗口/代次、命令框解析、PermissionRequest、prompt、dispatch/seq、stop/created_at/request、目标全部身份、无 ack 与持续要求必须逐项相等。
6. 时间原点由实际 I1 Stop/relay 后的 created_at 收据建立（10秒内观察），每次记录系统 UTC/monotonic。只有真实墙钟 age>120000 且观察 elapsed≥120100，Enter 开始≤130000，才 fsync 独占每-dispatch intent 后沿原 `terminal-key(permission=true)` 发一个 CR。每≤10秒复核，时钟漂移>1秒、模板/原屏变化、未知写入都 INCOMPLETE 且不重试。
7. settle 要实际工具 POST/queued request、Stop/idle、relay 结果、无 ack；早期必须 stop_too_early 且目标零增量；晚期必须 ideation 的实际 emergency 事件、事件时间>120秒、目标恰一个1b且仍存活、原 claim/attempt/fence/workspace 未变。150秒期限适用于结论；不能以 queued 或按键成功替代实际中断。

CLI 提供 initialize/arm/start/observe/permission/collect；C 原生 input 的 turn_limit 必须 I4/E1，不接收09B的E6配置。C-I3 的 review/template.json 除签字栏外不可改，签为同目录 approved.json。其余阶段批准、plan、owner、readiness、input、实际 build 路径和完整命令将在合并后绑定材料中给出，本轮不捏造运行值。

## 已运行与未运行

- 新契约红态 `rev2-tools-local-01/contract-red`：缺实现，exit1，明确不是旧产品缺陷。第一次 green-01 是相对归档路径夹具错误，原件保留；改用绝对输出后通过。API-handler-04 是离线 lifecycle 少两个模拟 API label 的夹具错误，原件保留；-05 及最终版通过。两处临时 root 都仅含确定性文件，已清理；未涉及实际场景。
- `rev2-tools-final-check-02/result.json`（42项，含后续gate反馈竞态）：文件归档/回收、严格读屏、全部绑定字段、clock/ack/demand、未知写入幂等、实际 Python 窗口 adapter 回执形状与 gate dispatch 包装形状检查 PASS。归档坏字节在 stop 前 BLOCKED；关停晚出 hook 在删除前 BLOCKED；数据库在 normal_stop 替身里被移除后绿态仍通过。
- 三个坏实现（跳过字节验证、跳过模板验证、伪造时间判定）在新 oracle 处 RED；额外真实 API Handler 的 Bash argv 坏 schema 在源自 Claude 2.1.296 tools 定义的断言处 RED（api-bash-mutant-red，exit1）。候选 Handler 全 C 阶段及正文/seq/身份/角色/预算五反例 PASS（C-handler-final-02）。它是实际 Handler 的字节流入口，不是 socket 或 native CLI/relay 证明。
- B 原协议 core 与九阶段矩阵 PASS；旧 protocol.json 逐字未改。没有依赖新增第三方库。
- **INCOMPLETE**：真实 loopback HTTP、实际进程 SIGTERM 在本轮尚未执行；系统时钟单独已本地实跑PASS（见下）；给主控的单脚本如下。它有210秒硬超时（外层230秒），只起两只假 API，确定性窗口/库行/normal_stop，保存实际请求/响应、完整 SSE、时钟采样、SQLite backup（不是漏 WAL 的拷贝），用同一回收函数先验归档、停两 API、再删 scratch。
- **INCOMPLETE**：实际九进程 owner/原生 Electron/真实门禁 C 全链、独立审查、合并 T090 后整组/F4，仍需后续材料绑定与审批。当前没有把 spy 当真实 Claude、把注入时钟当真实时钟，或宣布 09B/09C 业务 PASS。Behavioral acceptance 的独立证据要求留给主控 fresh reviewer；本会话没有另起子代理。

主控沙箱外执行（全新输出，约两分钟；首败即停、不重试）：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/run-rev2-tools-outside.py --output /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/rev2-tools-outside-01
```

预期六段 exit0：本地契约、元数据原子发布、C Handler、B 已记录 Claude 请求的真实 HTTP 正反例、C 真实 HTTP/真实时钟、API SIGTERM≤2秒。C 正例实际 POST=7/1；之后五反例也留原件，归档独立重数为 ideation11/executor2。后五条是故意拒绝的工具测试，不能混入正式09C的7/1预算场景。真实时钟证据必须读 real-clock-enter 的原始采样，不能只读 summary 的 PASS。

元数据发布的实际交错红态另保留在 `rev2-meta-atomic-red-01`：reader 在文件truncate与write之间看见无效JSON。改成 `.meta.tmp` 写完后 replace；`test_t078_rev2_meta_atomic.py` 的同一交错候选PASS，legacy-writer变异仍RED（另两个新目录），避免真实HTTP观察时把夹具读写竞态当协议失败。

本地反复夹具原件已无损压缩到 `rev2-tools-local-01.originals.tar.gz`，7,489成员／5,630文件、原字节23,737,158，压缩943,062字节；逐成员/字节验证后才用原样结果JSON读回替换展开树。完整清单在 `rev2-tools-local-01/originals.archive.json`。这只封装本地确定性测试输出，不是源码/launch冻结包，也不代替未来两场的外置盘原件归档。所有失败和坏实现输出仍在tar，未丢弃/改写。

许可写入后可能立刻出现正常的C-I4 gate反馈根；单CR是否新增用户turn intent按实际request_id关联，不误计这个正常根。`rev2-permission-feedback-red-01`保存旧判定红态，最终42项在同一事件交错下通过。

`test_t078_rev2_clock.py` 已在本会话实际等待：rev2-real-clock-01 PASS，wall 120.109656秒、monotonic 120.108549秒；Enter时实际wall age 120109.138ms、观察elapsed 120107.939ms，只有一个替身CR。使用系统time.time/time.monotonic，没有注入或快进；这是确定性原屏/窗口上的时钟证明，仍不是实际CLI/gate紧急停止证明。
