# T-074 执行主控决定 02：按 ticket rev 2 续做（2026-10-11）

回应 `needs-decision-02.md`。用户的决定由构思主控以 revise 条目 `20261011T004535Z-ideation-revise-001`（a2a `2ccdad9`）转来，已写进 ticket T-074 的“修订 rev 2”一节和 spec 第 6 节“批准与派发分开”。验收以 ticket `ready_rev: 2` 为准，与 rev 2 冲突的卡片条文以 rev 2 为准。下面是执行主控定的实验协议。

## 1. 受管 worker 不弹批准（两家各至少 3 次）
- 启动：Codex 用 `-a never`（approval_policy=never）加 workspace-write 沙箱；Claude 用 `--permission-mode dontAsk`，允许的工具经 `--allowedTools` 或 `--settings <本卡证据目录或 /tmp 下的文件>` 传入。只经每会话启动参数，不写任何全局配置。
- 每次：让模型在夹具里做一件允许范围外的事（例如写夹具根以外的 /tmp 文件，或执行规则外的命令），记录它被拒、窗格里没有批准窗口、原生记录里拒绝的样子；随后用 M3 注入一条带标记的文字，按 60 秒窗口核对它作为新用户消息送达，不被当作批准。
- 结果记进 `r7-injections.jsonl`，`state` 用新值 `never_after_denial`（Claude 同名），并加字段 `launch_mode`。

## 2. 主控窗格：权限请求 hook 与竞态
- 启动：Codex 用需要批准的模式（如 `-a on-request`），Claude 用默认权限模式；都只经每会话启动参数。
- hook 安装：**本决定逐次批准**在本卡的隔离 CODEX_HOME 里装 Codex 0.162.1 提供的、与批准请求对应的 hook，只做一件事：把事件原文追加到本卡证据目录下的一个文件。Claude 的 PermissionRequest hook 只经 `--settings` 传入，同样只追加事件。先读 `--help` 与文档确认存在；Codex 没有对应 hook 就写“未找到”并列出查过的途径，不改用读屏或 OSC 9 文字匹配。
- 要核实：批准窗口出现时有事件、结束（批准或拒绝）时有事件、能拿到请求标识，以及两者的时刻。若只有开始没有结束，如实记录，不推断。
- 竞态：分段写入一条 M3 注入（例如先写 bracketed paste 的前半段），在写完之前让 CLI 进入等批准，再写完剩下部分；记录实际发生了什么（`outcome` 照旧，含 `taken_as_approval`）。批准回答不得由 Enter 默认给出；需要结束批准窗口时，由探针以明确的“拒绝”按键结束并记录。
- 被批准的动作只能是夹具里无害的写文件。hook 不可靠或竞态无法避免时，停下写进报告，不加兜底重试。

## 3. Claude
- 用用户平常的 Claude 登录：直接运行本机 `claude`，**不设** `CLAUDE_CONFIG_DIR`，不读取、不复制、不打印任何凭据或 Keychain 内容。CLI 自己写 `~/.claude` 会话历史和 `~/.claude.json`（首次信任目录）可以接受；你与探针不写 Claude 的设置或权限文件。
- 模型 `claude-haiku-5-5`，**最多 15 个原生回合**（含试跑），达到就停下报告，不追加。工作目录用 /tmp 下的新夹具。
- Claude 的 R7 基本项（idle/running 下 M3 送达）、上面第 1、2 项都在这 15 回合内做；先排好计划，按“1 → 2 的 hook 事件 → 竞态 → R7 基本项”的优先级用，不够就照实报缺哪项。
- 观察送达以 Claude 自己写的会话记录为准（只读本次会话对应的那一个 jsonl，不读别的会话）。

## 4. Codex 额度
Codex 主 turn 上限仍为 **30 个**（含已用的 14 个）。超出就停下报告。

## 5. 交付
同卡片：a2a 提交、`T-074/RESULTS.md`（本轮新增一节）、更新 `findings/` 报告（写明对 T-075 的影响、spec 第 6 节的派发规则是否需要再改）、ticket Resolution（保持 open，写“待主控关闭”）、终端一行 `T-074 DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit>`。完成条件 1 的统计命令照旧要能跑。隔离 CODEX_HOME 用完删除；Claude 夹具保留在 /tmp。
