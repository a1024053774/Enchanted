# T-074 ready_rev 2 本轮探针（2026-10-11）

起点 `004c9646c19a5aa22b8231aa1b9d7df1cff601e5`。依据当前对话主控 #8、ticket 的修订 rev 2、spec 第 6 节和 controller-decision-02。只做事实探针，不做 T-075，不新增产品队列或重试。

REALITY GATE: INCOMPLETE。目标：两家各三次不问模式实际拒绝越界，随后 M3 新用户消息送达；验证权限请求 hook 的开始、结束、请求标识；在完整协议支持时测分段注入竞态。材料预示 PermissionRequest 可能只有开始且缺 request id，这还是 inferred，须实测原始事件与明确拒绝后的结果。

权限例外逐字来自 rev 2：“直接用你平常的登录”、“Haiku 5.5，最多 15 回合”、“worker 不弹批准”、“等批准时暂停，先验证”。Claude 不设 CLAUDE_CONFIG_DIR，不读取/复制/打印凭据；CLI 自己的历史与首次信任写入已授权。worker 不写全局设置或权限文件。

失败清单与独立预期：

- never/dontAsk 可能只是模型拒绝而未实际尝试：必须有原生工具调用及拒绝输出，不能用模型自报。
- /tmp 通常是 Codex 额外可写根，不把“夹具外 /tmp”冒称越界。Codex 实测目标为本卡证据目录内、沙箱工作根外的无害标记文件，验证文件不存在与真实权限拒绝。
- Claude 的 dontAsk 会保留已有 allow 规则。只经启动参数忽略 user/project/local 设置并明确 allowedTools=Read，Bash/Write 仍存在但不预先批准，不读取全局设置。
- 启动更新、登录或信任弹窗不能用任务文字/空白 Enter 默认批准；固定版本、关闭更新。只有已核对的自建夹具首次 trust，才按明确选择操作并记录。
- native 文本解析不能来自屏幕。Claude 只读明确 --session-id 所对应的一个 jsonl；结构化 OSC 7501 可以提供基础状态，但不替代权限 hook 的结束事件或 request id。
- hook 只原样追加 stdin JSON，不返回批准/拒绝，不改变权限。Codex 仅隔离 home 与每会话 -c；已逐次获批的精确 logger 可用文档的本次 hook-trust 参数，不改用户 home。Claude 仅 --settings。
- hook 若只有开始、没有结束或请求标识，保存明确拒绝后的全部原始事件，不补造关联；按决定停下写 needs-decision。竞态尚未执行时报告未测，不用 OSC 文字补接口。
- 竞态若可执行，partial paste 的每段先登记，批准只以明确拒绝按键结束，不发送默认批准 Enter。只允许夹具内无害副作用。

额度：Codex 已 14，本轮预计 worker 初始化 1 + 三次越界 3 + 三次后续消息 3 + hook 初始化/请求 2，共 23，竞态预留 2，均不超过总 30。Claude 预计同样 9 个原生输入回合，最多 15；剩余留给竞态与 R7 基本项。原生记录核对实际次数，辅助调用单列。达到上限、hook 不可靠或新门禁未知即停止，不自动追加。

Tracer bullet 未开始；Deep modules 只扩展一个证据终端宿主以支持第二家实际 CLI；Ubiquitous language 沿用窗格、原生会话与派发记录。用 evidence-first-testing 保留真实拒绝和竞态证据；不宣称修复或独立验收 PASS。

启动探针的设置修正（保留各自现场）：Claude 首次 prompt 跟在多值 allowedTools 后，未取得原生输入；新标签加 `--` 分隔。第二次启动因为省略普通环境/用户设置而得到 authentication_failed。恢复用户平常 CLI 的环境与设置来源后，第三次原生记录确认实际模型 claude-haiku-5-5。worker 的限制改为本会话 settings 中 `Bash(python3 *)` deny，dontAsk 不变，global hooks 仅在本 worker 会话禁用；不读取普通来源中的凭据。主控探针按参数 ask 同一无害 Python 写入，并只追加 PermissionRequest。
