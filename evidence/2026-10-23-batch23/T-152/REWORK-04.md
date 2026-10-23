# T-152 第 4 轮：统一 Stop 信封与单一正例

状态：INCOMPLETE，04 尚待主控沙箱外运行。授权：执行主控 #12 确认 PLAN `a6a8e9c84`，执行 FLOW-AUDIT 剩余修改集合 1～4；本轮只准备单个新夹具的 tracer_review_copy，不写 05、不跑全套变异。

03 的缺陷特定红态已由主控实跑取得：`outside-03-NM4823lV/green.json` → `/private/tmp/t152-753dx2lx/run/tracer_review_copy/command-0025.stdout.bin` 返回 question_origin_unverified；原 Stop 缺 cwd/transcript_path。它是夹具输入缺陷证据，不是保留业务断言的有效 mutant 红态。现有 01～03 的原始现场不重用、不覆盖。

本次改动均在已授权测试/专用 runner 与本票证据内：

- `stop_envelope` 统一 session、turn、Stop、cwd、transcript_path、最后消息；cwd 来自 worker attempt.workspace 或 reviewer candidate_workspace，日志路径来自该 launch 的受控 record.log。没有导入产品 locator 来替测试生成输入，没有关闭 hook 校验。
- 本地覆盖 stop_turn，供首轮 worker 和 ACK 共用；signal 错误立即保存输入/回执并带完整错误对象抛 HarnessFailure，不再等 ACK 超时。
- 本地覆盖 send_review，保留原 review_packet、JSON/原始消息、真实 signal/relay、状态读回；同样保存输入/回执并立即报告 signal 错误。
- held-socket 路径只接入同一 Stop 构造，保留 socket 生命周期、completedReview、结束前拒收、脏/干净对照及后续集成断言。
- 本票 run_suite 增加 --case，互斥 mutant / worker-regression；默认全套行为不变。04 明确只选 tracer_review_copy，每次仍创建全新源码副本、fixture 和输出路径。

`RUN-OUTSIDE-04.sh` 的 SUMMARY.json 从真实命令与运行前关闭阶段保存的数据库/请求副本逐项读回：排队回执及文件绑定；首轮匹配 Stop（session/cwd/精确日志路径）；同一 launch/request 的 relay_result 和 submitted candidate；恰好一条 source=gate dispatch；其 turn_submitted 对应 ACK 的唯一 pane_idle；独立 reviewer 的 review_result；副本删除事件先于 review_reclaimed；副本物理不存在。所有步骤均须成功且正常 tracer 自身 PASS，摘要才为 PASS。缺步骤、重复步骤、harness_error 或清理失败均为 INCOMPLETE。

04 的 PASS 仅能证明单个受控正例已走通，不能关闭 T-152，也不能代替有效业务 mutant 红态、完整正常场景、T-090/T-141 或 held-socket 的运行证据。正例通过后才按主控后续指示准备 05。

本地已用真实 `validateHookEnvelope` 对照 03 的旧 Stop：旧输入被 question_origin_unverified 拒绝，新 Stop 与 ACK 元数据通过；移除 cwd 或换成外来日志仍被拒绝。另用已知失败的 03 运行检查 04 读回器，它返回 INCOMPLETE；语法和差异检查通过。具体命令与保留输入在 `local-checks-04*.json`；这些只是孤立信封/报告器证据，不证明 signal/relay 已走通。
