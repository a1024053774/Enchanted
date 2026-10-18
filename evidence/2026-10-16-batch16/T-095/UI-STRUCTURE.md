# T-095：锚点识别合同（主控 #115 / 主控 #8）

Ubiquitous language 保持内部值 `waiting_controller_answer`、显示名“等待主控回答”。本轮按主控明确的新规则替换整屏结构校验；旧规则原文保存在 `STRUCTURE-96464ecf.md`，旧真实 NO_GO 不改写。

| 来源 | 当前识别规则 |
| --- | --- |
| 折叠锚点 | 在最后 **12 个非空可见行**中查找计数前缀 `? N question` 或 `? N questions`，忽略行首空白；N 为正整数。匹配前缀后的任何字符均不影响识别，不校验年龄、单复数搭配、队列标题、回答快捷键、输入框或底栏。 |
| 展开锚点 | 任一可见行同时含有字面标记 `⌃] skip` 与 `⇧→ main prompt`。两标记不能分处两行；不校验 enter、选项编号、标题、上下文或上方残留输出。 |
| Herdr | 读取前后身份与状态代次核对通过，且 `agent_status` 精确为 `blocked`。 |

两份读屏（visible / detection）均有任一锚点，且 Herdr blocked，才输出等待，附 worker / launch / pane / native session。两份读屏的形态、数量或周边内容可以不同，锚点是否存在才参与正判；不比较标题、选中项或原生问题数量。

只有屏幕锚点或只有 blocked，或者两份屏幕对锚点是否存在不一致，都输出 unknown，并在 `conflicts` 记录每个屏幕来源是否有锚点、Herdr 原值和保守决定。空屏加 blocked 也属于缺少屏幕印证。读不到、身份不符、原生记录不完整和读取中变化仍遵循原有 unknown 保护。

本轮等待正判以锚点与 blocked 为准，原生日志不作为额外的正判条件。它仍须通过自己的会话身份与完整性检查，并继续用于普通 working / 回落：日志 `clear` 不是“当前屏幕没有面板”的事实；日志 pending 而屏幕无锚点、Herdr 已 working，也不能假称已解决。

两边均无等待信号时，普通 working / idle 继续使用原有活动行、输入框、底栏与原生无 pending 的机械依据。不是用“没看到问题”直接推出 working。对相同标记不猜测其文本意图；例如屏幕有标记但 Herdr working 时，按单边成立保守 unknown。

## 原件回归与已知限制

red 折叠原件只有 Working、没有上述锚点，按新规则为 unknown，记录 blocked 单边成立。删除了旧的“原生 pending + blocked + 普通活动画面就判等待”的路径。red 展开、green 和 green-independent 的两种面板均有相应锚点；三份原件离线回放只算回归，下一次新会话才是新的独立验证。

三个历史 run 的实际投影和 NO_GO 结果保持不变。skip 后原生没有可关联的解决事件，即便出现同 turn sleep 返回或继续执行，也只能证明屏幕不再显示面板，不能证明已解决；继续 unknown 并留冲突。`accepted:true` 始终只是回执。
