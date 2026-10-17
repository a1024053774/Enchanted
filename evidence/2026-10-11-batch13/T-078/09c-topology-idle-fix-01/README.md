# 主控 #366：idle 原屏规范化修复

状态：**原屏入口红→绿与拒绝反例PASS；现场idle-02/turn未运行**。没有发键、派发、API请求、ps或停机。本轮只改测试工具和准备材料，不动产品源码/现有现场。

主控已完成探针setup、真实ideation B1/六键和s13；原 `../09c-topology-probe-run-01/idle-01/result.json` 因在原始VT字节中搜索连续 `manual mode on` 而失败。本轮完整保存上述新输出和签字件，idle-01不改写。固定原屏是 `ideation-p1/a365-ideation-s13-screen/screen.bin`，**8799字节、完整EOF**；其中manual单词间有CSI定位序列，去控制符后为 `⏸manualmodeon…`。这不是没有manual，也没有发生业务输入。

将原 `prepare-c2-runtime.readiness` 的OSC/CSI清理提到共享 `p1_simulated_actions.terminal_text`，并复用既有 `prompt_frame`：先严格核对完整capture/EOF，再读取最后一个完整编辑框，要求整个编辑框为空（包括折行），且它之后的首个状态行精确为暂停图标加manual mode on。没有退回到仅搜索❯，也不从历史主题/信任屏或旧manual状态推断当前就绪。Probe.idle与原readiness调用同一函数；原业务源码/协议/预算不变。完整原屏先落盘，再判定，后续拒绝不会再丢失已读取的完整屏。

[red-01](red-01/result.json) 在实际 `observe` 入口重放本次原屏，复现原同名断言；[Git旧源重放](known-bad-red-01/result.json)再次命中。这里仅把pane_output页和进程sampler设为明确transport夹具，没有连接活daemon或冒称真实ps。新 [green-03](green-03/result.json) **10项PASS**：真实原屏、完整空框manual正例；原native字节中直接插入草稿/将manual替换为plan，以及单行非空、多行非空、历史manual+当前plan、manual off、截断transport、缺编辑框结束线均拒绝。拒绝在owner日志/采样前，调用只读pane_output，键/ps均0。去掉判定、只看❯的[坏变异](marker-only-red-01/result.json)在非空草稿反例失败。

相关回归 [regression-runs](regression-runs.json) PASS：原probe入口、原模拟草稿流程、严格分页reader；分别为5项、14项、6项。它们仍是记录/模拟I/O，不作为本次物理采样或子进程归属的证据。没有增加允许进程规则，caffeinate仍待证，第3场NO_GO。

## 主控续行

1. 执行 [IDLE-02-COMMAND](IDLE-02-COMMAND.txt)，全新idle-02；核对原屏、prompt-readback、0 POST与10秒样本。失败即停，不重跑已有目录，不重启服务或角色。
2. idle-02 PASS后，审签本目录 [turn-approval-01.json](turn-approval-01.json)，字段从本现场原模板逐项复制，签名为空。执行 [TURN-COMMAND](TURN-COMMAND.txt)：新turn-01，只派发一个批准的模拟用户stop请求、保持同一POST采15秒、再放出该响应到I_SEND_STOP许可屏采15秒；**许可Enter为0，工具不执行，1根/1POST、模型0**。

两条命令的脚本/输入路径已静态检查，未来输出尚不存在。原B1/daemon/API/角色的运行绑定仍是 **ce0dba18c563da875077128d636583b81fc40f2b**；本次是主控#366批准的观察工具修复，不把已运行服务改称加载了新代码。无需重建probe，也不要重跑setup/首启；旧包和签字不改写。新的观察入口使用本修复提交；原件/预算/拓扑检查及一次性turn日志不变。只有实际探针取证后才能判断允许项，局部红绿不代替该证据。
