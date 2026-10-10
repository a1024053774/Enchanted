# T-065 一次独立审查请求

审查者：fresh-context acceptance-auditor `/root/t065_acceptance`，只读，不再委托审查。按 behavioral-acceptance-review 输出 STATUS / TARGET / EVIDENCE / FINDINGS / COUNTEREXAMPLE / LIMITATIONS。

冻结候选：

- fork `/Users/luckye/Documents/Code/synara`：`9654e1c63d87f41d033a3d6093c24d2a401b347a`；开工基线 `1bcf20720`。
- a2a 证据：`e18feadee4535c40aab22159c61801eb8cc70ed4`。
- 范围：上游 ChatView.tsx 空态块，a2a IssuePanel.tsx / TaskWindow.tsx。

验收依据为 ticket-contract-review.md 的 What / Acceptance / 说明，以及 controller-decision-01.md 的条件。主张仅为 GUI 布局验收，外观由用户判断；125% 可为 device-metrics 模拟，不能冒称真实菜单缩放。

不得读取任何 RESULTS*.md、ticket 的 Resolution、inbox 条目正文、实现者聊天/隐藏计划/理由。只读指定版本的契约、diff、截图、原始机械 JSON/log、测试与重放脚本、exact *-command.json。主控持续追加的 controller-poll.log、dispatch.jsonl、panes.txt 不属于候选；.grok/ 不属于候选。不改文件、branch、commit、服务、profile 或外部状态。

输入证据：red01-ui/red02-ui 的已知坏源码；green01-ui 的局部候选故障；green03-ui（3 条问题）、no-panel02-ui（真实空问题列表）、many01-ui（15 条问题）的原始数据、截图与命令；many01 的最短缩放按钮截图；相关 suite 和 typecheck/lint/fmt 的 *02-command.json / *02.log。candidate-binding.json 绑定执行源码 revision + dirty diff 与最终提交。

从外部契约重建 oracle，不只信绿色汇总。核对真实页面、首屏输入区、坐标点击输入、6 对相交面积、可见文字完整和按空间的整块收起；核对长中文、resize 往返、窄列、问题列表滚动、125% 模拟和控件完整可滚动到。已知坏版本须因业务断言被拒绝。只审查一次；FAIL 后由实现者修复并交 INCOMPLETE，不自行追审。
