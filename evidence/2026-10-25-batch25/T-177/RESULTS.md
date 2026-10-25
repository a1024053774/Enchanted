# T-177 结果：侧栏的历史折叠、清理、回收入口与启动默认选中

## 状态：INCOMPLETE（e2e 全过；待 agy 审查、合并）

## 依据

ticket T-177（ready_rev 1），来源 `findings/2026-10-25-lcu-real-use.md` 的 L04；用户 2026-10-24 原话：“然后你再用 lcu 测试一下软件看看能不能发现其他问题”。

## 根因

- 侧栏把每个 launch 记录都列出来，不看门禁的当前 attempt：修订作废、已回收的旧 attempt 会话与当前会话平铺；没有任何把会话移出列表的入口。
- 门禁集成后不回收 worker（设计如此，`integrate` 只在没有绑定会话时清理 attempt），界面上也没有回收入口，只能由主控在终端里调用 `reclaim`。
- 应用启动且没指定任务时，`run()` 打开“独立终端”区的已保存布局；布局里留着已经 exit 的家目录终端，于是一打开就选中一个已结束终端。

## 改动

- `src/sidebar.ts`：每个任务读一次门禁 `status`，得出当前 attempt 与是否已集成。会话的 `history` 为“已结束，或属于非当前 attempt”；一个会话下面还有不属于历史的子会话时它自己也不进历史，免得当前会话被一起折起来。`reclaimable` 只给“已集成任务的当前 attempt 的 worker、仍空闲”。读出 `sidebar_hidden` 事件里的会话，不列出。另加 `active_at`（该会话最后一条编排事件的时间）。
- `src/daemon.ts`：新命令 `sidebar_hide`，只接受操作员身份；每个会话都必须是已结束，否则拒绝 `session_not_ended`；只追加一条 `sidebar_hidden` 事件，不改 launch 记录、不碰门禁。
- `app/main.ts`、`app/preload.ts`：`a2a:reclaim` 调门禁 `reclaim`（task + attempt，操作员身份；是否空闲由门禁核对），`a2a:hide-sessions` 调 `sidebar_hide`。没指定任务、项目或会话就启动时，打开最近活跃（`active_at` 最新）且未结束、不在历史里的会话；没有这样的会话就打开第一个项目页；`selection()` 带回 `focus`，侧栏标出该会话。
- `app/renderer.tsx`、`app/style.css`：每组同级会话里，历史会话折进“历史 N 个”（默认收起，可展开），旁边“清理”只拿掉其中已结束的会话；可回收的 worker 行旁有“回收”。项目行的数字不再计入历史会话。

## 验收（真实 Electron，真实 Claude Code worker 与审查员，模型为本地脚本化接口，不耗额度）

`workbench/tests/test_t177_sidebar_history_e2e.py`。场景：T-1 两次修订作废并回收（a1、a2），a3 交付、审查、集成后 worker 仍空闲；T-2 一次修订作废（a1），a2 空闲；用户在独立终端区开一个终端后 exit；中途重启应用。期望按场景手算，见脚本开头。

| 运行 | 结果 |
| --- | --- |
| 修前 main（`red-main-01`） | 13 项失败：7 个会话平铺，没有历史、回收与清理；重启后选中已结束的家目录终端 `78ec0048…`。其中 `cleanup_keeps_evidence` 的失败来自测试本身（launch 数在开独立终端之前就数了），已改为开终端之后再数，不计为产品缺陷 |
| 修后 `green-01`、`green-02` | 两次都 PASS 18/18 |
| 变异 `history-too-wide`（有作废 attempt 的任务，当前会话也进历史） | 被拒：6 项失败 |
| 变异 `hide-live`（清理可藏掉仍在运行的会话） | 被拒：`live_session_cannot_be_hidden` |
| 回归 `test_t133_t107_terminal_controller_e2e.py`（含 T-176 侧栏检查） | PASS |
| 回归 `test_t171_superseded_issue_e2e.py`、`test_t174_silent_cli_hint_e2e.py` | PASS、PASS |

`green-02` 实测：T-1 只显示 a3 的 worker，“历史 3 个”默认收起，展开后为 a1、a2 的 worker 与审查员；T-2 显示 a2，“历史 1 个”；终端主控不进历史。只有 T-1 a3 的 worker 有“回收”，集成后仍为空闲（没有被自动关）；点“回收”后门禁出现该 attempt 的 `reclaimed` 事件，它进入历史（4 个）。对仍在运行的 T-2 a2 发 `sidebar_hide` 被拒（`session_not_ended`）。清理 T-1 历史后，launch 记录数与 T-2 门禁事件数不变、`launch_show` 仍读得到 a1 的会话；重启后 T-1 的历史不再出现，T-2 的“历史 1 个”还在。重启后打开 T-2 a2 的 worker（最近活跃、未结束），侧栏标出该行；没有选中已结束终端。

截图：`shots/`（修前、修后各四张：侧栏、展开历史、清理后、重启后）。夹具目录保留在 `/private/tmp/t177-*`。

## 没做 / 未验证

- 没用真实模型跑；所有 worker 与审查员的回合来自脚本化接口。ticket 写的“真实 Claude 用 claude-haiku-5-5”只在需要真实模型行为时用，本票的行为全在侧栏与门禁，不依赖模型。
- “最近活跃”按会话最后一条编排事件的时间算；没有把终端里纯 PTY 输出计入。
- 清理只按组进行，不能单独拿掉一行。被清理的会话没有“恢复显示”入口；记录页、指标与门禁事件里仍能看到它们。
