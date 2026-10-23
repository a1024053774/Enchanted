# T-143 独立只读审查 01

状态：**INCOMPLETE**。

审查来源：干净只读会话 `/root/t143_acceptance_review`，冻结版本 `8faf2a64638ca21dacdef8a493be5476b3e6672f`。
审查期间 HEAD 与候选文件未变化。此报告保存该次结果，不替修正后的版本宣称通过。

审查者独立运行 selection、真实 SQLite/layout、terminal catalog，均为 PASS；
无保留实验与候选仅 retainedPaneLimit 的 0/4 差异，zsh 语法通过，三份保护 oracle 未改，地图 0 个问题/0 个 stale。
旧候选 feea09ebc 的 selection 在 switch_back_retains_binding 失败，新候选通过，提供已知坏实现的对照。

发现 P1：联合 e2e 第 206、209 行使用 `#settings-terminal-accessibility input`，但该 id 位于 h3，input 是兄弟 label 下的元素，匹配数为 0。
因此会在设置处超时，无法到达后续布局、历史 agent 与普通终端验证。建议使用 `[aria-labelledby="settings-terminal-accessibility"] input`。
修正已写入测试；未改生产实现。真实 e2e 必须到达开关及其后检查，超时不能视为通过。

审查限制：未运行 Electron/GPU、性能对照、真实 T-133/T-107 或 T-091 起点比较；
未在该次审查执行保留集 N−1/N/N+1、并发切换或撤销失败场景。后续本地补测上限边界见 retention-boundaries-01.json，25 项 PASS。
不将这些本地结果上调为真实联合验收。

审查原始小文件保留在 /private/tmp：
- t143-review-selection-8faf2a.json
- t143-review-layout-8faf2a.json
- t143-review-catalog-8faf2a.json
- t143-review-experiment-8faf2a.json
- t143-review-accessibility-selector-8faf2a.json
- t143-review-selection-control-feea09.json
