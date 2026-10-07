# 原生 UI 观测摘录

以下保存 `mcp__cua_repl.js` 实际返回的 UI 文本。`getApp` 首次观测会自动显示完整树，随后保存到 `desktop-ax.txt`、`desktop3-ax.txt` 的 `getAXState` 返回了差异或“未变化”信息；这里补存首次完整观测中的关键字段。截图原始字节另存为 `desktop.png`，未编辑。

## 首次实例

调用：`await cua.getApp("/Users/luckye/Documents/Code/synara/apps/desktop/.electron-runtime/Synara Cua.app")`。工具返回耗时 2143.5398 秒；此耗时不作为冷启动时延。

```text
Window: "Synara Cua", App: Synara Cua.
0 标准窗口 Synara Cua, Secondary Actions: Raise
  1 container Synara Cua
    2 container
      3 HTML 内容 Synara, URL: synara-cua://app/index.html#/2ba0e6c5-9c8b-4ac9-8ffd-ae057bbe7896
        4 container
          5 container
            6 container
              7 container Open threads
            8 container Open panels
          9 container Notifications
          10 container Notifications
          11 container Welcome to Synara
            12 container
              13 标题 Welcome to Synara
                14 文本 Welcome to Synara
              15 文本 A local-first workspace for coding agents. Setup takes about a minute.
              16 内容列表
                17 container
                  18 text Local-first No account. Workspace data stays on this machine.
                19 container
                  20 text Your own agents Drives the CLIs, accounts and keys already set up here.
                21 container
                  22 text Verify before done Diff, terminal, browser and PR stay in one loop.
              23 进度指示器 Setup progress
              24 按钮 Skip setup
              25 按钮 Get started
            26 按钮 Close
              27 图像
  28 关闭按钮
  29 全屏幕按钮 Help: 此按钮也可以执行缩放窗口的操作, Secondary Actions: 缩放窗口
  30 最小化按钮
31 menu bar
  32 Synara Cua
  33 File
  34 Edit
  35 View
  36 Window
  37 Help
```

## 旧实例退出后的暖启动

新 main PID 24997 先经 `ps` 确认，随后重新选择同一 source bundle。工具返回耗时 0.3363 秒。入口启动 epoch 为 1791397083.6782598；原生 AX 观测结束 epoch 为 1791397090.046；6.367740154266357 秒包含观察调用与两者之间的调度，因此是观测上界。

```text
Window: "Synara Cua", App: Synara Cua.
0 标准窗口 Synara Cua, Secondary Actions: Raise
  1 container Synara Cua
    2 container
      3 HTML 内容 Synara, URL: synara-cua://app/index.html
        4 container
          5 container
            6 按钮 Toggle thread sidebar
            7 按钮 (disabled) Back
              8 图像
            9 按钮 (disabled) Forward
              10 图像
          11 container Primary
            12 按钮 Home
            13 按钮 Inbox
            14 按钮 Spaces
            15 按钮 Tasks
            16 按钮 Code review
            17 按钮 Automations
            18 弹出式按钮 More
            19 弹出式按钮 Help
            20 按钮 Settings
          21 container
            22 container
              23 弹出式按钮 Switch sidebar surface
              24 按钮 Search
              25 切换按钮 Switch to activity view
              26 内容列表
                27 按钮 New thread
              28 container
                29 文本 Projects
                30 container
                  31 弹出式按钮 Sort projects
                  32 按钮 Add project
                33 文本 No projects yet
              34 container
                35 按钮 Chats
                36 container
                  37 弹出式按钮 Sort chats
                  38 按钮 Open new chat home
                39 内容列表
                  40 文本 No chats yet
          41 container
            42 按钮 Description: Resize Sidebar, Help: Drag to resize sidebar
            43 图像 Synara
          44 container Notifications
          45 container Notifications
  46 关闭按钮
  47 全屏幕按钮 Help: 此按钮也可以执行缩放窗口的操作, Secondary Actions: 缩放窗口
  48 最小化按钮
49 menu bar
  50 Synara Cua
  51 File
  52 Edit
  53 View
  54 Window
  55 Help
```
