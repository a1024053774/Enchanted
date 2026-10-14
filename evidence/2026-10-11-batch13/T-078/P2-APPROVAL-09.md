# 材料 09：09A 启动审批，停止链路按场景继续

依据主控 #116～117，场景顺序与每步读回／失败停点见 [PLAN-09](PLAN-09.md)。**本次只冻结 09A 的启动、Esc 与第二条 nonce；09B/09C 的完整停止链路范围保留，待 09A 取消行为读回后再冻结各自实际角色／工具／启动材料。** 尚未收到分阶段偏好的补充回复，按已说明的 09A/B/C 顺序准备，不把它当作任何启动批准。

08e 全部运行证据、外置归档 manifest、原始 hook 小份和中文结论已提交 `675fac49`；仅证明变基前代码的单回合可行性。用户关闭 blocking issue 的条目由构思主控抄录，单独提交 `f3b33316`，未混入证据提交。

## 09A 候选与证据边界

产品候选 `5510ee72134fc7a8c08d37d03773adc96605debf`，[最终 diff](implementation-final-09.diff) 供主控审。依据 08e 实际 prompt_id 及 [官方 common input／Stop](https://code.claude.com/docs/en/hooks#common-input-fields)，按真实 prompt ID 绑定／结束关联，拒绝旧 ID；Esc 写出后登记并释放 active，保持 busy／interrupted／队列，不等不存在的中断 Stop。用户放行清理旧关联后才送第二条。

nullable 主控窗口按 task/spec_rev、当前 launch/native session 与实际 CLI leader 校验，worker attempt/session/fence 校验保留。显式 turn_limit=2 才扩大预算，未声明仍为 1，其他值拒绝。fake API 改为并发处理两条声明请求，第一条只观察真实 peer 关闭，第二条独立回应；不伪造 CLI hook、历史或后台事件。单回合仍用同一 API 实现，旧文件别名不保留。

红态：[回合关联／Esc](claude-epochs-red-09/results.json)、[nullable 窗口误拒](controller-window-red-09/results.json)、[第二请求返回 400](fake-two-requests-red-09/results.json)、[起点忽略显式预算](two-turn-profile-red-09/results.json)。新域／参数／内存 HTTP 检查 7＋5＋3＋1，通过；原单回合 signal/profile 3＋3，通过；原菜单／notice／信任检查 30 项通过。均未启动 CLI／API／socket／UI／模型，不替代实际 09A。

有效反例：[旧 Stop 错配](late-stop-mutant-02-09/counterexample.json)、[Esc 不清 active](esc-retirement-mutant-09/counterexample.json)、[窗口不核对 leader](window-liveness-mutant-09/counterexample.json)、[异步 Stop 清掉替换提交](stop-transfer-mutant-09/counterexample.json)。第一次只删入口 prompt 匹配仍被后续匹配挡住，已保存 [无效变异](late-stop-mutant-09/probe-error.json)，不能算反例。两次 apply_patch 因上下文／重复文件操作未应用，随后按实际内容修正，是编辑工具错误，不算产品红态。

## 新实例、准确参数和预算

实例 `/private/tmp/t078-2-p1-09-c_gw0g87`，task `t078-p1-09`；launch `12a5d58e-29fd-4c81-addc-a2b9a168abd8`，session `bfca5080-e272-4537-8986-1b05ee19b6d2`，thread `de9dddc8-24fb-4959-bad9-031e30dae6d6`。一个实际 ideation CLI，executor 调用者仍是已认证 operator；本场景不冒称双主控协作或真实用户亲手操作。

完整 CLI argv/shell argv/env/角色/hooks/预检见 [approval.json](p1-materials-09/approval.json)；API 和控制端 argv/env 见 [control-plane](p1-materials-09/control-plane.json)，准确构建／Electron／后续驱动 argv 见 [scenario-driver](p1-materials-09/scenario-driver.json)。CLI 参数仍固定 2.1.296、Haiku 5.5／low、manual、hooks timeout 3 秒、debug、公开 Bearer、theme=dark、无 IS_DEMO、禁标题请求、空 MCP、不用 --bare。HOME／CLAUDE_CONFIG_DIR／临时目录全在本隔离根内，不碰用户认证、设置或历史。

两份独立 nonce 和 [声明场景](p1-materials-09/scenario.json) 冻结：第 1 请求 cancel，第 2 请求 echo P2_ACK。真实模型预算 0，CLI 根提交和主 Messages 请求各 2。launch 输入 0。API 只在启动时分配 loopback 端口并写 runtime manifest，只有 api_url／ANTHROPIC_BASE_URL 可改变，私有 capability 不留证。

当前源码快照 67 文件，包含前端构建源与 Electron harness；CLI／API／Electron 都未启动，构建也未执行。T-077 合入后再变基，材料须重新生成、重新审批并完整重跑，当前候选与旧 PASS 不替新 main 背书。现在不 rebase，不 push。

## 本次请求：只启动 CLI，不发输入

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-launch-09
```

只预检、初始化本夹具、启动自己的 API／后台／CLI、记录实际 PID／身份后停下；launch 返回 INCOMPLETE，仅记录进程启动，无首屏／回合就绪主张。

继续沿用逐屏机制，先另批只读：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-screen-09 SCREEN_ID
```

读回本次原字节后，用 [模板](p1-materials-09/screen-key-approval-template.json) 单独保存 approvals/SCREEN_ID.json，写 executor 批准引用、basis、用途、明确按键、目标项与原文路径，再逐次另批：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-key-09 SCREEN_ID KEY PURPOSE
```

主题 Up→Auto／Down→Dark／Enter→Dark；固定 notice Enter→Continue，文字与 [固定基准](p1-materials-09/security-notice-text.txt) 逐字相等；信任 Down→Yes→读回→Enter，默认 No 的 Enter／Digit1／重复确认拒绝。不自动补键；新权限、认证、遥测、共享或其他引导停下保存。真登录用户 HOME 出现任何引导屏一律停下、不按键。

实际到主提示符后另填本实例 readiness.json；再从 [动作模板](p1-materials-09/actions-approval-template.json) 另存 actions-approval.json，明确批准自动化测试的 Escape 与 queue-release 两个动作及 PLAN-09 A1～A5 的停点条件。两份模板都不是批准。后续单独审批：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-continue-09
```

该阶段才构建独立外置盘 slot、打开自己的 Electron 窗口、发送第一 nonce、busy 时登记第二 nonce、经实际窗口 Esc、核对 active 释放／队列 held／API peer 取消，截图后经实际放行按钮发送第二条。记录 UPS1／UPS2 不同 ID、唯一 Stop2／idle、三份 hook receipt exit 0、ACK2、用户动作与原始字节。动作提前批准按确定的停点条件执行，不冒称真实用户当时亲手按键。原始窗口 capability 不写入日志。

第一取消最长 90 秒，第二响应屏障 60 秒，普通观测等待 30 秒，构建 90 秒；失败即停，原件保留，不重试、不发送替代输入／模型，不伪造 Stop。未中断、active 未释放、提前送达、同 ID／错误 ID、hook 非 0／丢失、第三请求、来源／窗口失效或记录器错误均 INCOMPLETE。

最后另批 `p1-cleanup-09`；只停止本 manifest 的 CLI/API/后台，确认退出后归档／删自己的根，Electron 正常关闭或报告自己的清理失败。单文件超过 5 MiB 停下报告，外置归档由主控运行、字节读回后仓库只留摘要与路径。

## 09B/09C 待后续冻结

完整 stop→执行→ack、120 秒无 ack 后只中断的每步原件、真实角色、worker 目标、反例与停止条件已列 [PLAN-09](PLAN-09.md)。Claude 库 inbox 转交仍未启用；这两阶段需要分别准备两个实际角色的每次新启动、隔离 home、工具权限和模型请求预算，不能用 operator 冒充。当前不宣称 B/C 静态实现完成或可执行，也不发它们的启动命令；范围与验收保留。

## 静态重放

[准备报告](p1-preparation-check-09.json) 核对实例、文件／ID、2 次预算、明确场景、无内部状态／readiness／动作批准、固定参数、源码逐字节、Node/Python/shell 语法、原 notice、尺寸和 project-map status。真实 09A 仍 INCOMPLETE。

```sh
python3 -B workbench/tests/regenerate_t078_p1.py --label p1-materials-09 --extra-source evidence/2026-10-11-batch13/T-078/p1-check-materials-09.py
python3 -B evidence/2026-10-11-batch13/T-078/p1-check-materials-09.py --output /绝对路径/新静态报告.json
```

生成命令只记录本次原始调用，不能对已存在的 09 目录重跑；变基后用新的材料编号／检查器／实例，并重跑完成条件及原回归。T-078 仍 INCOMPLETE、open、待主控关闭。
