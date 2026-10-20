# T-109 合并接线位置

相对起点 main 6411bdff8482ba47da207efa6a295a12666222aa。行号是本次候选的工作树行号；主控合并时以函数与上下文为准。

| 文件 | 候选行号 | 最小接线内容 |
| --- | --- | --- |
| workbench/src/sidebar.ts | 5 | 引入 questions.ts 的 questionState、projectQuestions |
| workbench/src/sidebar.ts | 22–24 | 在 agentState 的生命周期拒绝之后投影原生问题状态，取得已回答／取消的 tool_use_id |
| workbench/src/sidebar.ts | 46–48 | Codex 原生日志中的待答 call_id 若已经由原生 hook 确认解决，则不继续计入 pending |
| workbench/src/sidebar.ts | 101–102 | 只读 SELECT 纳入四种已保存 native_question 事件；未新增写入／扫描 |
| workbench/app/renderer.tsx | 12–13 | 引入新 QuestionsPanel 组件与 NativeQuestion 类型 |
| workbench/app/renderer.tsx | 16 | Snapshot 增加 questions 字段 |
| workbench/app/renderer.tsx | 56 | 声明绑定 pane key 的 answer preload 方法 |
| workbench/app/renderer.tsx | 300 | 在当前 SessionPane 中挂接 QuestionsPanel，沿用 inputEnabled 与 paneKey |

树结构、父子关系和侧栏树渲染未修改。问题状态实现位于新模块 workbench/src/questions.ts；问题 UI 位于新组件 workbench/app/QuestionsPanel.tsx 与 questions.css。T-107 的只读快照及写入变异检查已继续运行，结果见 RESULTS.md。

精确复现接线差异的只读命令：

```sh
LC_ALL=C git diff --unified=0 6411bdff8482ba47da207efa6a295a12666222aa -- workbench/src/sidebar.ts workbench/app/renderer.tsx
```
