# T-176 结果：各处会话状态一致

## 状态：PASS（agy 第二轮 PASS，`review-agy-02.md`）

## 根因与改动

L03 的四处现象来自两种原因：几处界面各取各的来源；另有一处钩子事件没送到后台。

| 现象 | 原因 | 改动 |
| --- | --- | --- |
| 主控回合结束仍“运行中” | 窗格头对项目终端显示的是 zsh 进程的生命周期（活着即“运行中”），侧栏用主控钩子报的回合状态 | 窗格头一律显示侧栏同一行的状态（`sidebar_snapshot` 的 `agentState`），不再另算 |
| worker 窗格头“空闲”、底栏“执行：运行中” | 底栏另显示 CLI 进程的生命周期 | 删掉底栏的“执行：…”，只留窗格头一个状态 |
| 主控在等用户时项目行是“等待主控回答” | 项目行只按“有 worker 等主控答复”聚合，不看主控是否在回合中 | worker 等主控答复、而本项目没有主控在回合中时，项目按“等你回答”聚合（要你去提示主控） |
| 刚结束的会话显示“已结束 1 天” | 时间列一直是启动至今 | 已结束的行显示“结束 N 分”（结束事件时间），悬停写“启动于/结束于” |

另一处：实测那一轮（真实 0.1.3、用户真实 Claude 2.1.310）主控终端里 **一条钩子事件都没有送到后台**（`terminal_turn` 为 0；该会话的 Stop 钩子清单里也没有 Enchanted 插件的钩子，技能列表里也没有 `a2a`），所以侧栏一直停在批准时的默认“运行中”。我用隔离夹具和用户真实登录各试了能想到的组合：开发树与已安装应用包的包装脚本和插件目录、预先信任与当场过信任框、从 Herdr 继承的 `CLAUDECODE`/`CLAUDE_CODE_*`/`HERDR_*` 变量、用户 `settings.json`（含 `CLAUDE_CODE_PLUGIN_DIRS`），插件 **都能加载**（真实登录下 `/enchanted-a2a:a2a` 出现在补全里，没发消息）。那一轮为何没加载，目前 **未知**，没有改它；已作为上报写进完成报告。

## 验收

测试：在 `workbench/tests/test_t133_t107_terminal_controller_e2e.py` 加 T-176 的四项检查（失败方式 8～11）；真实 Electron、后台、门禁、项目终端里的真实 Claude Code 2.1.310（模型是本地脚本化接口，零额度）。

| 运行 | 结果 |
| --- | --- |
| `--revision 8f36d6495`（修前 main） | 红：`controller_pane_header_matches_row`，侧栏 `idle`、窗格头“运行中”（`shots/red-controller-header.jpg`） |
| 修后 `green-01-test-syntax-error.json` | 前 16 项过，最后一项卡在测试脚本自己的 JS 花括号错误，保留原样 |
| 修后 `green-02.json` | PASS 17 项：主控窗格头“空闲”与侧栏一致；问题等主控而两个主控都空闲时项目行 `waiting_user_answer`；worker 窗格头与侧栏同为“等主控回答”，底栏无“执行：”；关掉的终端行显示“结束 刚刚” |
| 回归 `test_t157_stop_input_e2e.py` | PASS（其负例原期望“侧栏未知、窗格头忙”正是本票要消除的不一致，改为窗格头“未知”） |

截图：`shots/red-controller-header.jpg`、`shots/green-04-tree.jpg`（窗格头“空闲”）、`shots/green-05-issue-waiting.jpg`。

## 没做

- 没用真实模型复跑（本票用脚本化接口即可证明界面取同一来源；真实额度留给必须的地方）。
- 普通终端（未申请角色）的行在 shell 活着时仍是“运行中”转圈图标，这是 shell 的生命周期，不属于 L03 的会话回合状态；记为观察。

## 第一轮审查（`review-agy-01.md`，INCOMPLETE）与处理

| 发现 | 处理 |
| --- | --- |
| P1 家目录“独立终端”的窗格头恒为“未知”：它不在侧栏数据里，窗格头取不到状态（本票第一版引入） | `sidebar_snapshot` 的普通终端列表也收家目录终端（`project` 为空，界面只在项目下列出有项目的终端，所以侧栏不变） |
| P2 主控都空闲、worker 等主控答复时，项目行只在读屏文字里写“等待用户回答”，看不见 | 项目行此时显示“等你处理”（悬停说明：有上报在等主控答复，但没有主控在回合中） |
| P2 新增检查在修前版本上只跑到第一项 | 本票的检查改为“记下失败继续跑、最后一起判定”，修前每项都有观察值 |

新增检查 `home_terminal_header_known`（家目录终端窗格头是“运行中”）；`project_waits_on_user_when_no_controller_in_turn` 加上“项目行可见文字含‘等你’”。

| 运行 | 结果 |
| --- | --- |
| 修前 main `--revision 8f36d6495`（`red-main-02.json`） | 红：本票四项都失败，各有观察值（主控窗格头“运行中”而侧栏空闲；项目行 `waiting_controller_answer` 且无可见提示；worker 窗格头“空闲”而行为等主控、底栏“执行：运行中”；结束行“刚刚”）。家目录终端一项在 main 上通过（这个缺陷是本票第一版引入的） |
| 第一轮候选 `--revision 2e1f33266`（`regression-review01-candidate-01.json`） | 红：`project_waits_on_user_when_no_controller_in_turn`（可见文字为空）与 `home_terminal_header_known`（“未知”），即两条审查发现 |
| 修后 `green-03.json` | PASS，18 项 |
| `test_t157_stop_input_e2e.py`（`regression-t157-02.json`） | PASS |

运行输出：`runs-03.log`。
