# 单角色绿态：原样请求修复、清理与新实例审批

主控 #184 实跑的 source 为 `7e77f8b81611dc03e7df95a95801bda3f617393d`，材料提交 `41672c9363ce5c70689f2e3a9f71d16256e9a9a7`。本场 **INCOMPLETE**，预算 **NO_GO（主 Messages4/3）**；原 permission 结果、api-error、API4 与缺少最终 ACK/Stop/idle 均保留，不将本场改成 PASS。

## 实际达到的入口与校验器缺陷

[只读副本](slice1-green-3-readback/database-readback.json) 保存数据库／WAL／SHM 两次相同字节读取与原始 tar；所有 SQL 查询在另建副本上进行。原 API、hooks 和登记反馈原文均独立保存。

真实一次 Enter 为 control action，permission_control_written seq88 引用第一根原 submission；没有 source=user 提交。API2 同 ID 实际 tool_result 为 queued=true/delivered=false，真实 Stop exit0、prompt1 对应，seq93～94 收到并执行一次 schema2 inbox 请求，只返回 IDEATION sentinel；seq96 原根 idle。请求不含 worker attempt/fence，journal 的 attempt 空表示 controller 无 worker 尝试。

seq100～101 反馈第二根登记并写 CR，第二 UPS exit0，prompt2 与第一根不同。登记 dispatch2、UPS2 与 API3 的正文完全相同，见 [独立对照](slice1-green-3-readback/registered-feedback.json)。API3 的 user.content 是字符串；原校验器只遍历 block 数组，漏掉它，最后取到了第一根 nonce，误报不是 gate feedback。API1 的 user.content 为多 text blocks，因此先前合成数组测试没有覆盖此实际表示差异。这是夹具缺陷，不是后台反馈正文错配。

API3 被拒后 CLI 自身重发 API4；驱动没有重送新根，实际 UPS/intent 仍各2。但最后 ACK、第二 Stop/idle 不存在，不能声称完整绿态或原 scene 成功。此处仅已实测穿过真实客户端、角色 caller、Stop 转交与第二根到达的部分链路。

## 原样红绿与保持的边界

[原样 red](slice1-green-3-recorded-red/results.json) 为 12 条检查、只有 original-API3 失败；API1/2 及 API4 拒绝等原断言稳定。修复后 [原样 green](slice1-green-3-recorded-green-02/results.json) 14/14 PASS：同一原 API 字节、独立登记反馈，兼容文本字符串／text blocks 表示；改正文、model、stream、command、tool ID、request ID、实际登记但越角色结果以及 API4 均拒绝；真实数据库参考读取只匹配该 launch，foreign launch 没有参考。

校验器第三请求现在要求实际登记反馈原文，精确比较完整正文，不裁剪、不容忍拼接或额外字符。假服务只读自己的 state.sqlite3，以该 launch、第二次 gate dispatch 和对应 dispatch_queued 事件取得实际完整文本；不从 API 请求生成 expected，不写业务行／请求文件，不通过 operator 代替角色操作。既有 model/stream/预算/唯一固定 tool/queued/request关联/角色 sentinel 校验不放宽。readback 同样要求第二 UPS 等于实际登记反馈。

合成 green11、原 red协议12 回归 PASS；[有效预算坏变异](slice1-green-3-budget-mutant/results.json) 仍只在第四 Messages 条件失败。所有重放／反例／SQL 参考测试没有启动服务、CLI、Electron 或模型，也没有重发旧请求；它们不是完整真实绿态。产品源码、本轮已有入口回归文件与 app/hook/bin 未改。

## 固定本实例 cleanup

先在沙箱外运行 [cleanup-slice1-green-184.py](cleanup-slice1-green-184.py)：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/cleanup-slice1-green-184.py --approval-ref "主控 #184"
```

仅绑定 root `/private/tmp/t078-2-p1-slice1-green-1yhrmwad`、launch `284a5916-fd75-4c4d-bec0-9a8d49e063d9`、session `10b07cc8-bdc6-47e4-a801-c4d63dd37bb4`。API44036、daemon44048、CLI44069、shell44068；实际 owner／ready／manifest／PIDfile／命令及两次 lifetime 核对后，先认证 daemon_stop 并确认原 CLI/shell/daemon 退出，再最多向 API44036 发一次 SIGTERM并确认退出。PID 变化／未知退出即 BLOCKED，不发强制或进程组信号。

逐成员归档读回到外置 `p1-materials-slice1-green/cleanup-184/fixture.tar.gz`；原 api-error 根保持，脚本无 root 删除选项，旧／新 slot 不动。当前仅 [静态核对](slice1-green-3-cleanup-static.json) PASS，cleanup 本身 **INCOMPLETE**；worker 没有执行任何信号或生命周期命令。

## 新冻结与逐次 launch 审批

cleanup PASS 后，以原启动身份运行 [commit-and-prepare-slice1-green-3.sh](commit-and-prepare-slice1-green-3.sh)。第一提交冻结修复、旧场景原件、读回与测试；新材料为 `p1-materials-slice1-green-3`，新 root/HOME/launch/session/thread/nonce，绑定该 source，逐文件 Git/tar 字节核对，再第二次材料提交。生成与静态核对不 launch。

明确复用 outside-02 的 controller-entry6／空框17／runtime12／input-failures11／worker-inbox14 PASS，来源 `7e77f8b…`；准备脚本逐项读回 status/setup/cleanup，并以 Git 核对产品、app、hook、bin、acceptance、scripts 及相关入口／驱动源码未变。仅测试协议与材料脚本变化，新的原样重放单列，不将旧回归称为新运行。不会重跑未受影响组或启动额外 agent。

生成成功后主控先读新 approval/control-plane/static-check，再单独批准 launch：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/workbench/tests/run_t078_p1.py --materials /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/p1-materials-slice1-green-3 --phase launch
```

仍为固定 Claude2.1.296、Haiku5.5/low、manual、Bash/Read、隔离 HOME/CLAUDE_CONFIG_DIR、loopback假服务、空 MCP、三个原 hook、供应商模型0；launch 输入0。根2／主 Messages3／Bash1 不增加。主题／notice／目录信任逐屏、readiness、nonce与精确工具命令、真实一次 Yes/Enter分别批准；不得复用旧批准或按第二次 Enter。实际键来源如实记为 executor 批准的 test-simulated-user。

实际完整绿态仍须 queued实际返回 → 原 Stop一次角色执行 → 精确登记反馈第二根 → API3最终ACK → 同 prompt2 Stop exit0／idle；两条原 intent 均结算、许可无新 user intent、实际scope只返回IDEATION、没有API4或新工具／业务send/ack。任何错误／预算越界／身份或原屏变化立即停，不自动重试，保留场景。新实例生成、完整真实绿态、独立 reviewer、09B/09C和整票当前均 **INCOMPLETE**。
