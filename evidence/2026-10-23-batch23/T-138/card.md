# 任务卡 T-138-1

先读 `evidence/2026-10-23-batch23/COMMON.md`（公共约定）和 `.project-map/tickets/T-138-ime-composition-position.md`（ticket 全文，用户原话在里面）。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-138-1 |
| 来源 | `.project-map/tickets/T-138-ime-composition-position.md`，ready_rev 1（提交 ebbae7bd0） |
| 目标 | 在行中间用输入法提交的文字是刚打的字，不是隐藏输入框末尾的字；连续多次中间插入、回车后再插入都正确。 |
| 非目标 | 改 xterm 源码；候选框之外的输入法体验；终端性能（T-143 已合入，不回退）。 |
| 修改边界 | 允许：`workbench/app/renderer.tsx` 的终端输入与 composition 部分、`workbench/tests/**` 新文件、`evidence/2026-10-23-batch23/T-138/**`。禁止：`workbench/src/**`、`.project-map/**`、`AGENTS.md`、`CONTEXT.md`、验收文件。 |
| 验收文件（oracle_paths） | `workbench/tests/test_t091_pane_ipc.mjs` 以及 T-139/T-143 合入的 e2e（派发消息里给出路径） |
| 红态命令 | 新 e2e 加 `--revision <你的起点>`：中间插入“打出”，PTY 收到的是末尾两字。 |
| 任务类型 | 缺陷修复 |
| 修复对象 | 终端输入框的 composition 处理 |
| 复杂度 | S |
| 执行器 | Codex `gpt-6.1-sol`，`model_reasoning_effort="high"`，`service_tier="default"` |
| 起点 | 见派发消息 |
| 唯一写入者 | Herdr agent `b23-t138`，worktree `/Users/luckye/Documents/Code/a2a-wt-t138`，分支 `exec/t138` |

## 完成条件与交付

1. 先复现（ticket 第 1 步）：真实 Electron + CDP `Input.imeSetComposition` / `Input.insertText`，在一行中间（光标左移后）提交两字词“打出”，记录 PTY 实际收到的字节。修前若不是末尾两字、复现不成立：报告真正原因并停下，不凭猜测修（ticket 第 3 步）。
2. 修：每次提交后清空隐藏输入框，使下一次 compositionstart 的起点为 0、光标在末尾。不改 xterm 源码。
3. 新 e2e（如 `workbench/tests/test_t138_ime_e2e.py`）：中间插入“打出”收到“打出”；连续三次中间插入；回车后再中间插入；全部正确。
4. 红态 `--revision <起点>` 失败；已知坏实现（还原修复）被抓住。
5. 回归：`test_t091_pane_ipc.mjs` 与 T-139/T-143 的 e2e 绿态。
6. RESULTS.md 与 RUN-OUTSIDE 脚本按公共约定。
