# T-091 红态读回：主控执行材料

状态：**INCOMPLETE**。这次交付只含变更前读回脚本，尚未实跑，未修改 `workbench/app/`、`workbench/src/` 或现有测试。界面方向已按主控 #29 确认；实现等待主控返回红态结果。

实现时按本次确认的“窗宽 <1000px”取完整窗口视口宽度作为断点；不沿用原方向稿“扣除侧栏后的会话区域宽度”的表述。其余方向保持已确认内容。

## 本次需要核对的运行清单

入口为 `run_red.py`，文件开头列有完整运行清单。它启动两个固定的真实 Claude CLI `2.1.296`，使用现有 `controller_start`、隔离 HOME、loopback 假 API，停在首屏；worker 使用现有 `t078_native_receiver.c`，不启动真实 Codex。供应商模型回合 0、假 Messages POST 预算 0、按键 0、粘贴 0、放行 0。不会复制或读取 `auth.json`，不会执行真登录。

Claude 启动参数仍由产品的 `claudeLaunch` 生成：两个原生 session、`claude-haiku-5-5`／low 请求配置、manual permission、严格空 MCP、Bash/Read 工具声明、三个会话内 hook。没有模型提示提交，不因启动记录有模型名就声称运行过模型。worker receiver 接收生产 Codex 形状 argv（含会话 hook 和 `--dangerously-bypass-hook-trust`），但不执行这些选项；没有合成 hook 标记文件。脚本会核对没有输入／派发写入事件。

hook 命令都是本 checkout 的 Node CLI：`NODE workbench/src/gates/cli.ts --state <隔离 state> signal --launch <本次 launch>`，Claude 超时 3 秒，receiver argv 超时 10 秒。只传每次启动参数；不写全局设置。产品现有 `claudeLaunch` 要求隔离根目录以 `t078-2-` 开头，且记录中的角色卡版本／hook authorization 保留其现有固定文本；脚本因此使用全新的 `t078-2-t091-red-*` 目录，**这些旧标签不构成本次批准**，本次实际批准单独传 `--approval-ref` 并保存。

另会调用 Node、clang、隔离夹具 Git、生产 daemon／zsh PTY 和 Electron。后台启动入口本身使用 detached 子进程；Electron 由脚本以 `start_new_session=True` 启动。Git 只在新夹具里建基线提交，关闭 Git hooks；不交付、验收、集成、reclaim 或 push。构建只用产品标准 build 命令和外置盘全新槽，不移动或链接输出目录。

## 精确命令

先审阅这三个文件：`run_red.py`、`red_window.mjs`、`capture_window.py`。核对清单后，用本次真实批准引用替换参数值；以下目录和标签必须尚不存在。命令的工作目录是本 worktree。

```sh
python3 evidence/2026-10-16-batch16/T-091/run_red.py \
  --source /Users/luckye/Documents/Code/a2a-wt-t091 \
  --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/red-01 \
  --label red-01 \
  --approval-ref '主控对本次脚本清单的实际批准位置'
```

这是预期失败的合同读回，正常取得红态时也退出 **1**，产品状态保持 **INCOMPLETE**。不能只看退出码：必须有 `red_observed: true`、`expected: 3`、`observed: 1`，并核对 `cleanup_complete: true`、无 `error`／`archive_error`／收尾错误。启动失败、构建失败、权限缺失或截图失败不会设置 `red_observed: true`。

## 读回与截图如何证明现状

脚本通过现有门禁／后台入口创建一个隔离 task，登记两个主控与一个受管 worker。期待的角色、task、launch、thread、session／attempt 来自启动材料，分别与三份真实 `workbench_snapshot`、`pane_process_info` 和系统 PID／启动时间／命令读回核对；不改数据库，不替换后台 processInfo。

`red_window.mjs` 调用标准构建产物导出的生产 `run()`，把三个 launch 作为 `launches` 列表交给它。基线忽略这个尚未支持的字段，按既有逻辑显示当前 worker；脚本观察实际 DOM 的全部终端区域和 BrowserWindow 数量，不把参数解析失败当产品红态，也不创建假的终端区域。单帧应显示一个真实 worker 终端，后台同时已有三个真实窗格；这证明当前窗口不能呈现要求的三个会话。后续绿态仍须用支持列表的新生产路径重跑同一“一个窗口同时显示三个明确 launch”合同。

截图只调用 `capture_window.py`，它先比较脚本自己启动的 Electron PID、完整命令和启动时间，再从 CoreGraphics 中查该 PID 唯一可见的普通窗口，取得窗口号。随后运行 `/usr/sbin/screencapture -x -o -l <窗口号> <新文件>`，截图前后再次核对窗口归属；不依赖标题，不截图整个屏幕，不拼接或覆盖标签。只保存本次 Electron 的窗口元数据，不保存其他应用的窗口列表。

若 `CGPreflightScreenCaptureAccess()` 显示缺屏幕录制权限，脚本停止截图、保存错误并进入隔离实例的收尾；主控报告给用户处理。它不请求权限，不打开系统设置，也不改用全屏截图。这里不使用辅助功能或发送按键。

原始单帧是外置目录中的 `baseline-original.png`。主控应查看原图，并把文本摘要和该原始图的位置回传；worker 在收到结果前不开始产品改动。

## 证据与收尾

外置输出保存完整命令／原始 stdout 和 stderr、三份快照、启动记录、进程身份、首屏字节、Electron 观察日志、单帧与 `run.json`。原始终端首屏只供主控检查，不意味着主题、信任、登录或权限已确认；本脚本从不代选。

结束时先关本次 Electron，再对本次 state 调 `daemon_stop`；仅观察已登记 PID 的退出，不自行 kill 不明进程。退出或归属无法核对时保留现场，报告 INCOMPLETE。停止确认后，把整个夹具复制到该外置输出的 `fixture/`，逐项统计文件数和总字节数比较，保留 `/private/tmp` 原件；操作凭据在夹具外单独生成，确认停止后清理，不进入归档或 Git。

仓库只新增 `<label>.run.json` 摘要、`<label>.RESULTS.md`、`<label>.archive.json` 清单。清单含 original、archive、files、bytes、replay，不带校验值。脚本不删除夹具原件，不覆盖旧输出。若实跑失败，换新标签重跑必须先处理原现场，不能把一次新运行写进旧目录。

本交付仅做静态语法和路径检查，不表示 Claude 启动、进程读回、截图或归档已通过；红态、Tracer bullet、三格绿态、反例和回归均为 INCOMPLETE。

本地已执行的静态检查：两个 Python 文件经 `ast.parse` 解析，`node --check evidence/2026-10-16-batch16/T-091/red_window.mjs` 退出 0；产品及现有测试相对起点的 `git diff` 为空。这些检查未启动上述运行清单中的应用或后台。
