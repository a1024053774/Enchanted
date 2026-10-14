# 09A-3 失败方式与实施前边界

2026-10-14，主控 #128；授权原文见 [用户决定](20261014T120839Z-ideation-answer-001.md)。状态 **BLOCKED：尚未修改产品，尚未取得本候选的真实入口红态**。

目标：用户自行处理输入框后，以引用对应中断的空框声明放行；只有结构化登记的当前注入正文错配时，在 UserPromptSubmit 处理前阻断。非目标：后台删字、裁剪或容忍拼接、自动重送、改变 Stop、改门禁核心、启动真实模型。

**Tracer bullet**：Esc → 用户实际处理草稿 → 声明空框 → 窗口放行 → 第二回合独立 prompt/hook/API；另一个独立夹具保留拼接提交的阻断反例。**Deep modules**：状态和串行写入由 Panes 持有，窗口凭据由 daemon 核对，不另建写入入口。**Ubiquitous language**：声明只是用户声明；后台草稿占用不是 CLI 输入框检测。

## 空框声明与放行

| 失败方式 | 独立预期与证据 |
| --- | --- |
| 没有声明就调用放行 | 拒绝；队列、PTY 输入、active 不变；留拒绝诊断。 |
| 声明引用别的中断、旧 launch 或旧窗口 | 拒绝；不能解除当前占用。中断引用来自实际 Esc 写入收据，不能只传 interrupted=true。 |
| 声明后新键入、粘贴、二进制输入 | 输入代次改变；陈旧放行拒绝；新输入仍按原顺序记录，不删除或丢弃。 |
| 声明后发生中文组合输入，尚无提交文字 | compositionstart 已占用新代次；即使未产生 onData，也拒绝陈旧放行。 |
| 声明与按键并发，身份检查或记录器 await 时有新输入 | 写入前再次核对中断和代次；不能用 await 前的检查放行。 |
| 第二窗口输入使第一个窗口声明过期 | 代次属于窗格；不能只核对调用窗口的 sequence。 |
| 声明重复送达或窗口关闭／身份失效 | 请求去重和当前身份检查仍拒绝；不重复 paste/CR。 |
| 用户实际没有清空却声称为空，或 CLI 后续自行恢复草稿 | 不声称后台观察到空框；登记注入正文错配由提交前拦截挡住；保留诊断，不自动重送。 |
| 空框声明被记成机器观测，或恢复的旧文字被记成新用户 message | 记录明确为用户声明及中断引用；旧文字不新记为亲手输入。 |
| 用户按 Ctrl+C/U/S 等控制字节 | 记 terminal-key/control action，保留原字节；不记 message，不据这些键推断空框。 |

## 当前注入提交前拦截

| 失败方式 | 独立预期与证据 |
| --- | --- |
| 当前登记注入与 hook prompt 拼接或其他错配 | UserPromptSubmit 阻断输出实际到达 hook stdout/exit；保留原始 prompt、dispatch/submission 关联和诊断；假 API 请求数不增加。 |
| 只拒收 a2a 信号，hook 却 exit 1 | 不合格；exit 1 不阻断 Claude。不能把 daemon 拒收当供应商提交已阻断。 |
| daemon 返回阻断 JSON，但 CLI 丢弃它 | 不合格；必须从实际 hook CLI 输出核对阻断决定。 |
| 当前提交来自用户手打，正文恰含旧派发标记或 nonce | 不拦截；来源必须由当前结构化注入登记判断，不能按文本关键词猜测。 |
| 无当前注入、历史 dispatch、退休 submission、旧 hook | 不能用历史记录拦截手打提交；诊断与生命周期规则分别验证。 |
| 当前注入正文精确匹配 | 允许，实际 prompt_id 关联仍成立，独立 CR 与回合预算不变。 |
| 缺 prompt_id、重复 ID、错误 native session | 原有关联／身份诊断不削弱；阻断来源不能扩成“所有 signal 失败都 block”。 |
| Stop 出错、错 ID、晚到或重复 | 原行为不改；不得统一改 exit 2 或把 UPS 策略应用到 Stop。 |
| 错配后自动裁剪、容忍、重送或再次请求模型 | 不合格；保持待处置诊断，模型／假 API 请求数证明没有消费。 |

## 必须先协调的文件边界

当前 `workbench/src/gates/cli.ts` 的实际 signal 结果输出是 `result.ok ? {} : result`，返回码是 `result.ok ? 0 : 1`。成功的阻断 JSON 会被清掉，失败结果只 exit 1；仅改 daemon 不足以让真实 Claude 在处理 prompt 前阻断。该文件属于 T-080 独占，本轮按主控 #128 的“必须改时先停下告诉我”停止产品实现。

`workbench/app/preload.ts` 的 releaseQueue 和 `workbench/app/main.ts` 的 release IPC 都没有参数，不能将 renderer 持有的中断引用及输入代次传给 daemon。最小接线需要同时修改这两处；不能靠后台猜测当前快照来替代用户确认所引用的那次中断。

待主控协调：允许 main/preload 转发声明；让 T-080 或获得明确授权的 T-078 修改 CLI 的 UserPromptSubmit 阻断结果输出，保持 Stop 不变。core.ts 无须修改。授权前不改产品，不生成可启动的 09A-3 launch，不复用旧 09A-2 实例。

## 当前证据限制

旧 09A-2 实跑的拼接及 hook exit 1 证据见 [DRAFT-OPTIONS](DRAFT-OPTIONS-09A2.md)，这是旧候选证据。本轮的新条件红态仍待真实入口探针，不能用读源码替代。

电脑重启后原根 `/private/tmp/t078-2-p1-09a2-sm_du7jo` 已丢失；外置 fixture 归档及仓库小份仍保留。原根中未被归档的原件存在证据缺口，不补造，也不能再运行依赖原根的处置脚本。只删旧 slot 的独立脚本另交主控执行，清理结果不替代产品验收。
