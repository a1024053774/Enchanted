# A-15 readiness 确认与 I1 第一步待批

主控 #326 的六键/各屏输出、签字件已提交为 `a3c36f1ac1c7269176ff5103fcb5c4ed7ed8f07a`，九项尾注齐。六个 key_result 都是 written；P1 的 key/screen 结果保留 INCOMPLETE 原文，不改成完整 09B 验收。s13 原件为 `a15-ideation-s13-screen/screen.bin`；主控已读回空提示符、manual mode on，且报告零业务输入。

本轮只写以下材料，没有确认 readiness、派发、release、读新屏或按键：

1. `09b-a15-b1-ideation-p1-01/READINESS-CONFIRM-COMMAND.txt`：由主控执行，核对保存的 s13 原屏与 launch/session、尾部空提示符和 manual 标记，并核对实际 HTTP POST 原件数、请求/响应日志行数均为 0，以及该 launch 尚无提交/UPS/Stop 事件；通过后用排他创建写 readiness.json。屏幕标记检查辅助主控 #326 的实际读屏，不另冒充终端渲染 oracle。命令不发业务输入、不 release；已有 readiness.json 时不覆盖。
2. `09b-a15-b1-ideation-p1-01/phases/I1/approval.json`：空签字 I1 草稿，已带本次真实 target binding、ideation launch/session、原提示文件和 synthetic_input_id；approved_by/approval_ref 均为空。它批准的是执行主控签字的 test-simulated-user 窗口停止请求，不记为真实用户亲手输入；permission_enter_authorized=false。
3. `09b-a15-b1-ideation-p1-01/phases/I1/STEP1-COMMAND.txt`：主控先核对上述 readiness，审签 I1 草稿后执行。使用现有 protocol 驱动，经真实门禁 pane_dispatch 原提示、登记实际全局 seq/dispatch ID，再 pane_release 一次；API 根据实际 gate 历史绑定 I_SEND_STOP，仅下发 Bash command。到真实 PermissionRequest 后保存事件/原屏，返回 READY_FOR_PERMISSION 即停，不发 Enter，也不自动进入第二条 Messages。

完整注入文本（保留原提示文件末尾换行；产品登记仅去末尾 CR/LF）：

> 09B A-15：这是执行主控批准的 test-simulated-user 窗口停止请求。请按本回合登记的唯一 I_SEND_STOP 工具请求停止目标；工具返回仅排队时结束本回合，等待真实 Stop 转交，不重试、不新增请求。

`I_SEND_STOP-preview.json` 从当前 protocol 和本场景真实 plan 生成，只预览 argv/command；tool_use ID、dispatch seq、request_id、prompt/Stop ID 仍由真实执行登记，不预造。故意 --from executor 的命令继续由角色凭据核对实际 sender=ideation，不由 operator 代发 send。工具回执异步排队；真正 Stop/relay 之后才生成 stop 条目，本次第一步不会走到那里。

I1 全回合预算为 1 root / 2 Messages、1 次工具许可；本次 dispatch 第一步只预期第 1 次实际 POST，在许可屏停止。许可 Enter、tool_result 的第 2 次 POST、Stop/relay 和 pending/零反馈读回留待下一次独立批准；未启动 executor。角色全场预算仍为 ideation 4/6、executor 6/11、供应商模型 0。任何 409、身份/正文/seq 不符、超预算、意外工具或 45 秒未到许可屏，均停下保留，不重试。

第一步输出为已存在父目录 `phases/I1/` 下的新 `dispatch-01/`，不会复用旧 output；本次材料没有创建该输出、stage-approvals/I1.json、stop-body 或用户动作记录。原有 `phases/I1/COMMANDS.txt` 仍列完整后续流程供追溯；此次待批只覆盖 STEP1，后续 permission 草稿必须从实际事件与原屏生成、另外签字。
