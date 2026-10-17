# A-16 I1 第一步（主控 #346，仅备材料）

先由主控执行 P1 根目录的 `READINESS-CONFIRM-COMMAND.txt`：核对已保存 s13 原屏与 launch/session/repo、完整capture及EOF、空提示符/manual，再查当前0 HTTP原件/请求/响应日志及0提交事件，全部成立才以排他创建写 `readiness.json`。依据为主控 #346 的首启读回；worker本轮不执行、不写入 readiness，也不把生成命令算作确认完成。

随后核对并签本目录 **`approval.json`**（两项签字仍空），只运行 `STEP1-COMMAND.txt` 的唯一命令。它沿冻结入口 `t078_09b_i1_driver.py --protocol --stage I1 --protocol-phase dispatch`：

- 输入为 `i1-prompt.txt` 的完整批准自动化停止请求，经真实 `pane_dispatch` / `pane_release`，记 test-simulated-user，不冒称真人手输；业务 stop 由角色随后执行工具，不由 operator 代写。
- dispatch id、全局seq、UPS prompt_id、request/tool_use id由实际门禁/HTTP/钩子产生后绑定，不填固定 #1/#2。原文仅去尾部CR/LF的登记规则不变。
- 假API下发 Bash.command 的 `I_SEND_STOP`，命令取冻结 protocol 的argv与实际target/input引用；故意参数 `--from executor` 不覆盖真实ideation凭据。
- **到 READY_FOR_PERMISSION 即停。** 此步预期1根、1个实际 `/v1/messages` POST、1次PermissionRequest；不按Enter、不执行工具、不启动executor。完整I1在另批一次性Yes后才有第二个POST/tool_result与Stop→pending结算，整阶段预算仍1根/2POST。

45秒内未得到预期许可、HTTP409/重试、额外POST/根、身份/正文不符、完整读屏被拒或输出目录已存在，都停下保留原件，不能再dispatch/默认Enter。若首步已派发后失败，先读回实际dispatch和状态，不能把命令当成可安全重跑。

逐POST原件由已运行的rev2 API立即写 `roles/ideation/http-exchanges/NNNN.request.bin`、`.response.bin`、`.meta.json`，连同requests/responses日志；UPS与PermissionRequest的stdin/started/finished/stdout/stderr在该角色hooks目录。第一步尚无Stop，不伪造Stop原件。认证头不进入捕获接口，后续归档按 `t078_raw_retention.py` 结构脱敏、逐成员字节读回、从tar独立重数并留每条archive指针；先归档通过再停机，停机后不读SQLite。不得清掉原件或以汇总代替。

`STEP1-REVIEW.json` 是审阅说明，不是已观察的dispatch/请求/许可记录。现有 `COMMANDS.txt` 中后续permission生成/Enter只作施工材料，**本次只交第一步，不批准后两步**。
