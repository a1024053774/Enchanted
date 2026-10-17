# T-091 单格 Tracer bullet：主控执行材料

状态：**INCOMPLETE**。基线红态与 close 系列已记录、提交，见 [RESULTS.md](RESULTS.md)。本候选已将单格迁到按 sender 窗口和 pane key 路由的生产路径；没有保留旧的无 key IPC 实现，也尚未扩为三个窗格。

本阶段验收目标：从真实 renderer／preload 经六条 keyed IPC 到现有 daemon，读回同一受管 worker 的输出与输入收据；确认完整身份、键盘焦点、独立序号、错误 key 拒绝和关闭后的后台存续。门禁、紧急停止、收件箱语义与 160×45 网格不变。单格实跑通过后才扩三格，符合已确认的“先跑通读回，再扩”顺序。

## 生产变更

- main 维护 sender 与 pane key 的登记，六条 handler 进程内注册一次，不按窗口反复注册或删除；每格有自己的 launch、输入凭据、sequence、inputQueue 与 pendingRelease。
- preload 只得到非机密 pane key；六种调用都显式带 key，renderer 不接触 operator 或窗口 token。并发快照共用一次窗口凭据请求，关闭等待尚在签发的凭据后撤销，避免迟到凭据漏收尾。
- renderer 的现有单格完整走 keyed 通路，保持独立 decoder／输出游标／放行声明；显示完整身份。只有实际 textarea 焦点且可输入时才有“正在输入”和蓝线，不自动聚焦。
- daemon 仅在已有 workbench_snapshot 投影新增现成的 preset 字段。所有门禁和窗口输入命令继续使用原入口和核对。
- 真实入口驱动 `electron_driver.mjs` 现在按明确 pane key 或 launch 选择窗格；多个窗格时不允许省略选择。快照与输出 checkpoint 按 key 保存，终端 DOM 查询限制在选定 pane 内；任务门禁是共享区域。

## 本轮运行清单，须先核对

入口：`run_tracer.py`。文件开头有完整预算和收尾声明。与红态场景不同，这个最薄切片只启动一个受控 receiver：

| 项目 | 本次操作 |
| --- | --- |
| 进程 | Node 26.5+、生产 daemon、一个 zsh／受控 C receiver、一个 Electron 43.4.1；clang 编译 t078_native_receiver.c 的隔离副本，仅增加一行预先生成的 stdout nonce，原文件不改；夹具 Git 初始化。Claude／真 Codex 启动 0 |
| 网络与登录 | 仅 loopback 拒绝式假 API；供应商模型回合 0、假 POST 0。不复制 auth.json，不读写全局配置，不做真登录 |
| hook | receiver 接收生产 argv 中 UserPromptSubmit／Stop／PermissionRequest（10 秒）及 bypass-hook-trust 参数，但不会执行这些选项；没有 hook 标记文件，无合成 hook，无模型提示提交 |
| 输入 | 聚焦一次、失焦一次；一份随机中文 nonce 的 bracketed paste，submit=false；**没有 Enter、Esc 或其他控制键**。六个未知 key 的调用必须全部拒绝 |
| 其余 IPC | 对有效 key 调一次 composition-start、一次错误 window_id 的放行声明（必须拒绝、不放行）、一次 focus-observation。后者只是观察命令测试，不声称是 CLI 实际发出的模式变化，也不写 PTY |
| 记录来源 | 模拟夹具用户输入通路，核对一条 user_inputs 及对应 human_intervention；不能把自动测试字节当成用户真实输入历史 |
| 截图 | 核对本次 Electron PID／启动时间／完整命令，再查唯一窗口号，以 screencapture -l 只截隔离窗口。缺权限停报，不去系统设置 |
| 收尾 | 未确认 ready（包括提前自行退出）就停等主控，不自动 SIGTERM 或强退；ready 已确认才对原身份请求正常退出。窗口退出后核对 window_closed 与同一 receiver 仍活着，再 daemon_stop、确认 writer 退出、复制归档 |

输入预期来自生成后冻结的 nonce 和受控 receiver 开启的 bracketed paste 协议；送达以 receiver 原始字节、窗口请求／PTY intent／written 收据、任务的输入与介入记录共同核对。驱动返回 sent／attempted 只表示动作，不作送达证据。

输出 nonce 在编译／启动前生成，须同时出现在 CLI 读到的原始 trace 和 xterm 可访问文本中；UI 游标须等于独立 trace 的字节数。不以一个固定 READY 标记作为全部输出正确的证明。

## 精确命令

候选须已提交，产品和测试相对 HEAD 无未提交差异。主控核对上述清单及脚本后，填本次批准引用，使用全新输出目录和标签：

本轮生产代码冻结候选为 `7e1c68ad432f281e05c2ac58c1fc3fe2fe079d86`；其后的审查报告提交只补文本记录。只读审查结果为 INCOMPLETE，真实读回待本命令取得，见 [tracer-acceptance-audit-01.md](tracer-acceptance-audit-01.md)。

```sh
python3 -B evidence/2026-10-16-batch16/T-091/run_tracer.py \
  --source /Users/luckye/Documents/Code/a2a-wt-t091 \
  --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/tracer-01 \
  --label tracer-01 \
  --approval-ref '<主控对本次进程、hook、输入和收尾清单的批准引用>'
```

本脚本成功应为 **PASS / rc 0**：trace_passed、cleanup_complete、archive_complete 均为 true，fake_posts 为 0，无 error／post_close_error／archive_error／cleanup_errors。查看外置 `tracer-original.png`：完整身份可见，只有一个窗格；聚焦时“正在输入”和蓝线归属该格。它不是三格绿态。

外置目录保存原始命令、snapshot、process、驱动事件、精确字节／输入记录、截图和整个 fixture。仓库只生成 `<label>.run.json` 与 `<label>.archive.json`；链接原样复制、记录两侧边界，原夹具保留，输出不覆盖。若退出未确认，保留现场及早期 electron-owner.json，后台清理和归档暂缓。

## 已跑本地检查与实际边界

`pane-ipc-unit-01.json` 为 **PASS**。它执行真实 main／preload TS 模块，但 Electron、传输和 mkdir 边界由 VM 提供；不产生 GUI、socket、PTY 或真实凭据。旧版本 6974c2 的未知 key 被接受，因业务断言失败；候选通过下列八项：未知 key 拒绝、六个 handler 单次注册、每窗口 key 与序号独立、跨窗口／iframe 拒绝、输出绑定、nullable 主控可输入与历史 worker 只读、preload keyed 调用、关闭等待签发并保留另一窗口通路。

```sh
node --experimental-vm-modules workbench/tests/test_t091_pane_ipc.mjs evidence/2026-10-16-batch16/T-091/pane-ipc-unit-01.json
```

该报告已存在，重放要换新输出。main.ts、preload.ts、renderer.tsx 经已安装 Vite transformWithOxc 的内存转换通过；没有运行完整构建或创建构建缓存。Node 对 main／preload／driver 的语法检查通过。上述结果不证明真实 preload 参数、renderer 焦点、Node PTY、实际窗口退出或屏幕捕获已通过。

定向驱动选择逻辑另有 `driver-selection-unit-01.json`：在外部提供的三个窗格观察值上，旧驱动不拒绝省略目标而被断言拒绝；新驱动按 key／launch 选对角色和快照、拒绝未知与歧义选择。它是选择逻辑检查，不是实际三格 DOM 或界面通过证据。`tracer-script-preflight-01.json` 记录脚本语法和 receiver 输出 nonce 插入点检查通过，未编译或启动目标。

## 后续门槛与回归线索

单格真实读回后再扩到一窗三格，仍使用这条通路；再交三份真实 snapshot／进程身份、错 task／旧 launch 反例、原始单帧及完整回归脚本。全票的绿态与回归仍为 INCOMPLETE。

本轮读到两个既有验收材料问题，作为非阻塞问题报执行主控，不擅自改验收预期或用跳过代替通过：

1. `workbench/tests/test_electron_e2e.py:170` 仍断言 bridge 只有 output／snapshot；T-078 已有输入通路的基线实际上是六种方法，当前还增加只读 paneKeys。这一旧断言与已确认的接口不符。需主控确认其验收文件身份及正确预期，才能把该旧 window 阶段计入回归；本 worker 未改该断言。
2. `test_t078_window_binding.mjs` 依赖的仓库内 `p1-materials-09/continue-esc/electron/snapshots.ndjson` 在本稀疏 worktree 不存在。本轮只更新它的生产片段定位与定向驱动调用，未运行、不宣称通过；主控需提供对应外置原件或另定受保护输入，不能以伪造 snapshot 补齐。

完整的现有 CLI 正反例命令与另外两个包装器问题见 [REGRESSION-PLAN.md](REGRESSION-PLAN.md)；不直接用旧 --probe all 包装或未经核对的 GUI 故障收尾。本阶段没有启动这些后台或实际 Electron 测试，不能把局部 VM 检查写成 T-074／T-075／T-078 全回归 PASS。
