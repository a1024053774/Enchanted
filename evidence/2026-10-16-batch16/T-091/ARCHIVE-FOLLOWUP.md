# close-03 与 red-02：符号链接归档和退出策略

日期：2026-10-17。状态：**INCOMPLETE**（本地检查通过；原夹具归档与 red-02 等执行主控实跑）。本次只改 T-091 的证据脚本和记录，产品、门禁及原有验收文件未改。

## 已发生的处置，按来源记录

| 事项 | 来源与结果 |
| --- | --- |
| close-01 正常退出被拒 | 执行主控 #6／本对话主控 #35；外置 `red-01-close-01/run.json` 为 BLOCKED、rc 2，错误为 `electron_normal_quit_request_refused` |
| 对 6599 发一次 SIGTERM | **执行主控亲自操作，不是 worker 或脚本发出的**。主控先核对完整 argv（red_window.mjs、red-01/window-plan.json、observer-events.jsonl）、06:30:34 启动时间、ppid 1，再发一次 SIGTERM；报告 2 秒后退出且无残留。2 秒是主控报告值，worker 未测量；未提供精确命令 argv／毫秒时间戳，不补造 |
| close-02 核对已退出，复制前失败 | 外置 `red-01-close-02/cleanup-events.jsonl` 记录 6599 及七个原 writer PID 均不存在，走 already_absent，没有退出请求；随后 inventory 以 `fixture_archive_contains_symlink` 拒绝，BLOCKED、rc 2。原日志 `/private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/4cb6cda5-1e37-4e3e-8ff5-2755a799eb7c/scratchpad/t091-close02.log` 保留 |
| 本次 worker 操作 | 只读查看原件与链接元数据，在本 worktree 内修脚本、跑本地文件复制和纯逻辑检查。未启动 Electron／agent／PTY，未查实时进程，未发信号，未写外置盘或改原夹具 |

**对本票卡在 ready 之前的进程，正常退出请求不可用**；6599 已实测被拒。red-02 预先按此情况处理，不再把它当作可依赖的收尾手段。此前记录与 close-01／02 的失败状态原样保留，不补判成功。主控已明确本轮没有按键或模型回合，手工 SIGTERM 是进程处置，不是终端按键；本次脚本也不增加按键或模型回合。

## 符号链接怎么归档

`run_red.py` 的 `archive_fixture()` 同时供 red-02 和 close-03 使用：先按 lstat／不跟随链接的 scandir 盘点，再用 `shutil.copytree(..., symlinks=True)` 复制，最后重新盘点并比较。

- 每条符号链接本身计作一个文件条目，记录原样 target 字符串；不打开、stat、resolve 或递归遍历 target。悬空链接、自环和目录链接都按链接保存。
- `files` 是普通文件数加链接数，不含目录；`bytes` 是普通文件字节数加链接目标字符串的文件系统编码字节数。清单另列 regular_files／regular_bytes、symlink_count／symlink_bytes 和 directories，避免与旧版只统计普通文件的数值混淆。
- 比较普通文件与目录的相对路径／类型、普通文件尺寸，以及每条链接的相对路径、类型、目标原文和目标字节数；目标被换成同样字节长度的其他字符串也必须拒绝。没有校验值或指纹。
- 每条链接在清单记录 `outside_fixture`（原目标是否在原夹具外）、`outside_archive_fixture`（同一目标文字复制后是否在归档夹具外）以及两侧 lexical_target。范围判断仅做字符串路径规范化，不跟随目标或链接链，也不假装已验证最终物理目标是否存在。
- 绝对链接不改写。原夹具内的绝对目标复制后仍指向原路径，可能位于归档目录外；清单明确标记，不复制外部目标，不靠改链接“修复”归档。

本次只读盘点原夹具：普通文件 69 个／2,482,554 字节，链接 2 条／目标文本共 138 字节，合计 files 71、bytes 2,482,692，目录 63。读回摘要为 `red-01-link-readback-01.json`，不是已完成复制的证明。

| 链接 | 原样目标 | 原夹具外 | 复制后的预期 |
| --- | --- | --- | --- |
| `roles/executor/latest` | `/private/tmp/t078-2-t091-red-05cht89k/roles/executor/claude-debug.log` | 否 | 仍指向原路径，位于外置归档目录之外 |
| `roles/ideation/latest` | `/private/tmp/t078-2-t091-red-05cht89k/roles/ideation/claude-debug.log` | 否 | 同上 |

## 先执行 close-03

当前 `close_red01.py` 已收窄为“核对原进程已不存在，然后归档”。不调用 AppKit，不发送正常退出请求或信号。如果 6599 或任一原 writer PID 仍存在，立即 BLOCKED，不复制。它继续核对原 run、argv、时间、state／user-data 和夹具归属，不能替换 PID 或夹具。

执行清单：新 CLI／agent／daemon／PTY／API 启动 0，hook 0，按键 0，模型回合 0；仅 `/bin/ps` 只读检查、链接自身复制与比较。主控核对当前脚本后运行：

```sh
python3 -B evidence/2026-10-16-batch16/T-091/close_red01.py \
  --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/red-01-close-03 \
  --label red-01-close-03 \
  --approval-ref '主控对 close-03 已退出核对及符号链接原样归档的本次批准位置'
```

成功为 **PASS / rc 0**，只代表退出核对与复制完成；原 red-01 仍为 INCOMPLETE。新 `red-01-close-03.archive.json` 包含链接清单、original、archive、files、bytes、replay 和 comparison。原夹具保留，不删原件，不覆盖 close-01／02。

## 再执行 red-02：ready 前卡住就停等主控

**事先选择的策略是停下等主控，脚本不发 SIGTERM。** 未收到匹配 PID／版本的 ready 握手，且进程仍活着时，`Observer.close()` 不尝试正常退出、不强退，报 `electron_startup_unconfirmed_wait_for_controller`；后台清理与归档暂缓。`electron-owner.json` 已在等待 ready 前保存，主控可据此处理现场。本次对 6599 的手工 SIGTERM 不成为脚本对后续 PID 的自动授权。

只有 ready 已确认，才由脚本对同一已核对进程请求正常退出；确认 Electron 退出后才停后台、核对 writer、归档。正常退出被拒或退出未确认仍停报。管道丢失继续只记录 protocol_failed，不因迟到 ready 的 EPIPE 直接退出。脚本自己的拒绝式假 API 在父脚本结束时停止，保留的后台／CLI 不声称仍构成完整可复用运行。

启动清单与既定预算不变：两个固定 Claude CLI 2.1.296、一个受控 receiver、一个 Electron；loopback 拒绝式假 API，隔离 HOME/state/user-data；供应商模型回合 0、假 Messages POST 0、按键／粘贴／放行 0；不复制 auth.json，不做真登录。需要核对 red-02 的本次批准，不能复用旧轮批准。

```sh
python3 -B evidence/2026-10-16-batch16/T-091/run_red.py \
  --source /Users/luckye/Documents/Code/a2a-wt-t091 \
  --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/red-02 \
  --label red-02 \
  --approval-ref '主控对 red-02 启动清单、零按键零模型及 ready 前停等策略的本次批准位置'
```

取得有效红态仍为 rc 1；须同时核对 red_observed=true、expected 3／observed 1、electron_ready_confirmed=true、electron_exit_confirmed=true、cleanup_complete=true、最终假 POST 0，以及原始单帧和新链接归档清单。环境或收尾错误仍为 INCOMPLETE，不能算产品红态。

## 本地检查与未运行项

`test_fixture_archive.py` 的真实本地文件复制检查 **PASS**：两个普通文件、十条链接，覆盖内部／外部目标、绝对／相对路径、目录链接、悬空链接、自环和中文目标；外部 65,536 字节哨兵未被计入或复制为链接内容。旧提交 `2f29e666c76d1581ea554b9c5d7595cb5a13639e` 的实际 inventory 以原错误拒绝这份合法输入；当前复制与清单断言通过。同字节长度的链接目标替换反例也被拒绝。结果在 `archive-script-checks-01.json`；成功后仅清除了本次自行生成的本地测试数据。

`test_red_cleanup.py` 的四项纯 Python／Node 检查 **PASS**，新增“未确认 ready 时不请求正常退出、不发信号、停等主控”；旧提交实际进入正常退出请求而被断言拒绝。结果在 `red-02-script-checks-04.json`。这些检查不证明实际 AppKit、进程退出、外置盘复制或 Electron ready。

```sh
python3 -B evidence/2026-10-16-batch16/T-091/test_fixture_archive.py --output evidence/2026-10-16-batch16/T-091/archive-script-checks-01.json
python3 -B evidence/2026-10-16-batch16/T-091/test_red_cleanup.py --output evidence/2026-10-16-batch16/T-091/red-02-script-checks-04.json
```

上面是本次已跑命令；报告已存在，重放需换新输出名，不能覆盖。close-03、原夹具外置复制、red-02、截图与产品实现均未运行，等待执行主控读回结果。
