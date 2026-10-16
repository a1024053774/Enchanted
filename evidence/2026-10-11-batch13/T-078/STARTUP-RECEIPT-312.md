# 主控 #312：首启投递完成条件补强

独立审查为 NO_GO，原因是完成条件漏检，不是已确认的候选产品缺陷。本轮只改测试、夹具和证据；不改 workbench/src，不操作 A-14。

最小完成条件：同一原条目在每个首启键之后、release 之前，必须经会调用 readWakeDelivery 的真实收据刷新路径重新查询；返回 queued，整个投递历史无 delivered，原 I2 尚不存在。只查未刷新的 SQLite 最新行不够。release 之后仍应由真实 turn_submitted 使同条目 delivered，并关联原 request/entry 的唯一 I2。

隔离检查需区分以下失败方式：没有调用刷新方法；查询了错误条目；只检查第一键；最新行 queued 但历史已错误追加 delivered；首启期间产生 I2；真实 release 后收据仍不更新；M5 因缺文件/身份故障失败而被误算为被业务断言拒绝。

保留审查员的精确 M5 diff 与独立时点探针在 `startup-receipt-oracle-312/`。先确认旧完成条件让同一 M5 存活，再补断言，要求 M5 在“首启后刷新结果仍 queued”这一条失败，候选仍通过。所有变异仅在一次性副本，不修改产品文件。真实 CLI/daemon/Stop/relay 的入口复验由主控沙箱外执行，供应商 CLI/API/model 均为 0；独立审查仍待新候选，不能把本轮作者自检称为新独立 PASS。

已执行：`09b-startup-receipt-legacy-M5-01` 中冻结的 06fc9feca 领域测试在精确 M5 下仍 15/15 PASS，确认原漏检。补强后 `09b-startup-receipt-domain-03` 中 M5 的两项正例都在第一键后的新刷新断言失败（实际 delivered，预期 queued）；其保存的历史为 queued→delivered、物理写入仅 ArrowUp、状态仍 unknown、队列一条。候选 15/15 PASS，单键和六键合计七次真实 gates.inboxDeliveryStatus 刷新均 queued、无 delivered 历史和 I2；release 后实际提交仍可刷新为 delivered。01/02 阶段证据保留，03 是增加逐时点证据核对后的最终运行器结果。

领域夹具补入同一个已记录的 A14 stop 条目，并用真实 A2AGates、Panes 与同库 queued 收据执行刷新。它仍以 PTY/前台身份 spy 代替进程，未声称领域测试具有 daemon 的延后 I2 调度。入口测试则在每个真实 pane_screen_key CLI 调用后，由认证 executor 操作员用真实 `workbench/bin/inbox list` 查询原条目；这是收据查询，不是代写 send/stop/ack，不新增业务根或 Messages。返回值、完整投递历史、I2 intent/registered/dispatch 与原 thread/message 每次另存 `startup-receipt-0..5.json`。

`STARTUP-RECEIPT-ENTRY-COMMAND-01.txt` 是沙箱外复验命令，输出全新 `09b-startup-receipt-entry-01`。脚本先跑精确 M5、要求它在 startup refreshed delivery 0 处实际 delivered/预期 queued 失败，再跑候选、要求六次真实刷新和后续 release/delivered/原 I2/ack 链通过。M5 原始用例必须保留 INCOMPLETE/exit 1，运行器 PASS 仅表示反例确被检出。预检 `09b-startup-receipt-entry-preflight-01` 已实际组装两份副本并加载真实 inbox 入口，未启动服务；完整入口阶段仍 INCOMPLETE，待主控执行。

新增六条收据查询仍各有 5 秒期限，启动场景总期限改为 160 秒、外层 190 秒，原无首启材料场景的期限不变；没有重试或时钟快进。全部产品源码与工作树一致，M5 仅存在于一次性副本和保留的 diff/JSON 中。A-14 未读写或回收，仍 NO_GO；新独立审查前不批准新 launch。
