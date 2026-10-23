---
id: T-143
title: 终端滚动与切换窗格卡顿
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

来源：用户 2026-10-23 在本 session 逐字（第 6 条）：“6.还有现在这个终端窗口的滚动和切换窗格特别卡,怎么 herdr 人家就这么流畅,是因为他也是在终端里而我们是套在 app 里吗”

不是“套在 app 里”的必然代价（VS Code 的终端同样在 Electron 里，很流畅）。本仓库的具体原因：
- `app/renderer.tsx:186` 开着 `screenReaderMode: true`，xterm 为每行生成可访问性 DOM，滚动和输出都慢。
- 没有 WebGL/canvas 渲染插件，用默认 DOM 渲染。
- 输出靠 100ms 轮询 IPC + base64（`read()`），不是推送。
- 切视图 `changeView` 销毁全部窗格，重新按偏移回放整个积压输出（隐藏回放）才显示。

做法：先量后改。第一步在真实 Electron 里量滚动帧率与切换耗时（基线入证据）；再逐项试：screenReaderMode 改为默认关（需要时手动开）、加 WebGL 渲染、输出改推送或缩短轮询、切换时不销毁已连接窗格或只回放最近一屏。每项给前后数字，没改善的不留。
不做：换终端实现。

## Acceptance

- [ ] 基线与改后的滚动帧率、切换窗格耗时入证据，同一夹具同一命令。
- [ ] 切换后输出不丢、不重复（偏移核对仍通过）；焦点与输入仍正确。
- [ ] 与 T-139 的视图改动同批验证，不互相回退。

## 同批验证

T-139 与 T-143 同一批验证（用户 2026-10-23：“T-139 和 T-143同一批验证”）：同一夹具、同一次真实 Electron 运行，先后合入但不分开验收，互不回退。

## 不做

范围外的问题经问题上报，不顺手改。

## Resolution

