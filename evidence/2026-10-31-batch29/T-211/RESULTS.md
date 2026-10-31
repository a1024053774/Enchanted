# T-211 hc 事实探针结果（2026-10-31）

- 被测对象：herdr-core 0.1.15 的 macOS arm64 打包构件（来源见第 1 项），在隔离会话 `HC_SESSION=probe` 中运行。状态与配置目录放在会话临时目录，socket 放在 `/tmp/enc.RXDy`。探针结束后两者都已删除。
- 执行人：Claude Code（主控）。脚本是本目录的 `hcprobe.py` 与 `statusprobe.py`（最终版本）。
- 用户自己 Herdr 的 core（`default` 会话，pid 87320）全程没有连接，也没有改动。
- 总状态：**PASS**，八项都取得了实测事实。第 5 项的 Codex 部分起初因登录过期没测成（run9）；用户重新登录后补测（run10、run11）。

## 复现命令

`P` 是本会话的临时目录，`B=$P/hc-bundle/bin/herdr-core`。

第一轮（第 2、3、4、6、8 项）。core 启动时故意带上会外漏的变量：

```bash
XDG_STATE_HOME=$P/probe/state XDG_CONFIG_HOME=$P/probe/config XDG_RUNTIME_DIR=/tmp/enc.RXDy HC_SESSION=probe \
  A2A_LEAK=leaked CLAUDE_CODE_DISABLE_TERMINAL_TITLE=1 $B server start --json
python3 -I hcprobe.py $B $P/probe /tmp/enc.RXDy env,input,notes,sweep,survival   # runs/run1.jsonl
python3 -I hcprobe.py $B $P/probe /tmp/enc.RXDy notes,sweep                      # runs/run2.jsonl
python3 -I hcprobe.py $B $P/probe /tmp/enc.RXDy notes                            # runs/run3.jsonl
python3 -I hcprobe.py $B $P/probe /tmp/enc.RXDy observe,history                  # runs/run4.jsonl
python3 -I hcprobe.py $B $P/probe /tmp/enc.RXDy history                          # runs/run5.jsonl
```

第二轮（第 5 项与环境方案）。core 用受控环境启动，socket 改由 `HC_SOCKET` 指定：

```bash
env -i HOME=$HOME USER=$USER LOGNAME=$USER SHELL=/bin/zsh LANG=en_US.UTF-8 \
  PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$HOME/.local/bin \
  XDG_STATE_HOME=$P/probe/state XDG_CONFIG_HOME=$P/probe/config HC_SOCKET=/tmp/enc.RXDy/p.sock HC_SESSION=probe \
  $B server start --json
python3 -I statusprobe.py /tmp/enc.RXDy/p.sock $P/probe/out claude-dontask,claude-title-empty,claude-title-1,claude-default-perm  # run6
python3 -I statusprobe.py /tmp/enc.RXDy/p.sock $P/probe/out claude-ask-perm   # run7
python3 -I statusprobe.py /tmp/enc.RXDy/p.sock $P/probe/out agy,opencode      # run8
python3 -I statusprobe.py /tmp/enc.RXDy/p.sock $P/probe/out codex             # run9（登录过期时）
# 用户重新登录后，以同样方式另起私有 core（socket 目录换成新的 mktemp -d 短路径）：
python3 -I statusprobe.py <新目录>/p.sock $P/probe/out codex                   # run10
python3 -I statusprobe.py <新目录>/p.sock $P/probe/out codex-ask               # run11
```

另有一条手动检查。它验证终端里的 `hc` 能否经 `HC_SOCKET` 连回私有 core，输出没有入库：

```bash
env XDG_STATE_HOME=$P/probe/state XDG_CONFIG_HOME=$P/probe/config HC_SOCKET=/tmp/enc.RXDy/p.sock HC_SESSION=probe \
  $B run --bg --name inner /usr/bin/env -u XDG_STATE_HOME -u XDG_CONFIG_HOME sh -c \
  "env | sort > env-inner.txt; $B ls --json > inner-ls.json; $B get \$HC_TERMINAL_ID --json > inner-self.json"
```

探针自身的缺陷保留为失败证据，没有覆盖：

- run1 的通知一项为空：BSD `cat -v` 写文件时带缓冲，内容没刷出来。run3 改用 `cat -uv`。
- run2 的通知一项报 `name_taken`：上一轮的父终端还没结束。
- run4 的历史计数为 0：正则多转义了一层。run5 是有效结果。
- `screens/` 只收了三份屏幕：Claude 的权限框、Codex 的登录页、Codex 的审批框。`env*.txt` 含本会话的令牌与邮箱，不入库。

## 逐项结果

### 1. 固定版本与来源：PASS

- 版本：0.1.15，`https://releases.herdr.dev/core/latest.json` 当时指向它；源码 tag 为 `v0.1.15`。
- macOS arm64 构件：`https://releases.herdr.dev/core/0.1.15/herdr-core-macos-aarch64.tar.gz`。SHA-256 为 `47eba8367e0626a1efced8795fcb03d5434b2541c5a84d78c50cc02c8fb49fc8`，与 manifest 一致。
- 包内文件：`herdr-core`（5,921,232 字节）、`LICENSE`（Apache-2.0）、`THIRD-PARTY-NOTICES`。随包附带后两者。
- 签名：二进制是 ad-hoc 签名。发布没有独立的签名密钥，唯一的核对手段是经 HTTPS 取得的 manifest 里的 SHA-256。

### 2. 环境不外漏：PASS（与假设部分不符）

- core 的环境原样进入终端。core 带着 `A2A_LEAK=leaked` 和 `CLAUDE_CODE_DISABLE_TERMINAL_TITLE=1` 启动，新终端里两个变量都在（run1）。hc 只改它自己的变量：设置 `HC_TERMINAL_ID`、`HC_TERMINAL_SOCKET`、`HC_SCOPE`、`HC_SESSION`、`PWD`，并在缺失时补上 `TERM`、`COLORTERM`、`TERM_PROGRAM`、`LANG`。
- `terminal.run` 的 `env` 只能覆盖或新增，不能删除。传 `{"A2A_LEAK": ""}` 后变量仍在，值为空串（run1）。
- 所以终端环境只能由 core 的启动环境决定。用 `env -i` 加白名单启动 core 后，终端里只剩白名单变量和 hc 自己的变量。
- 新发现：给 core 设的 `XDG_STATE_HOME`、`XDG_CONFIG_HOME`、`XDG_RUNTIME_DIR` 也会进终端。终端里遵循 XDG 的工具（如 git、opencode）会因此去私有目录找配置。
- 实测可行的组合有三点：
  - socket 用 `HC_SOCKET` 指定，不设 `XDG_RUNTIME_DIR`；
  - 私有状态与配置目录照旧经 XDG 变量交给 core；
  - 终端 argv 前加 `/usr/bin/env -u XDG_STATE_HOME -u XDG_CONFIG_HOME`。

  这样终端里没有 XDG 变量，终端里的 `hc` 经 `HC_SOCKET` 连回私有 core，`hc get $HC_TERMINAL_ID` 返回的正是本终端。用户自己的环境里如果本来就设了这些变量，应改为还原原值，而不是 `-u`。
- 依据源码 `paths.rs`：
  - 状态目录只认 `XDG_STATE_HOME`，未设时为 `~/.local/state/herdr-core/<session>`；
  - 配置只认 `XDG_CONFIG_HOME`，未设时为 `~/.config/herdr-core/config.toml`，与用户自己的 hc 共用一份；
  - socket 依次认 `HC_SOCKET`、配置里的 `socket`、运行目录。
- socket 路径上限为 103 字节，计入 holder socket 的后缀。会话临时目录下的长路径会超限，必须用短路径。

### 3. 存活：PASS（core 崩溃会丢历史）

- 客户端退出：探针每次调用完客户端就退出，终端一直是 live，`ticker` 跨了多轮。
- `hc server restart`：程序仍是同一个 pid，core 的 pid 换了。屏幕与历史完整：`terminal.read` 和 observe attach 的 `history` 都取回了 0～199 共 200 行（run5）。
- kill -9 core：程序仍是同一个 pid，记录为 live。下一次客户端调用时自动拉起了新 core。但屏幕与历史丢了：read 与 attach 都取不回旧行，`complete: false`，终端记录 `screen: "inexact"`（run5）。依据源码（`runtime.rs` 的 adopt 与 nudge）：崩溃后只用 holder 留下的尾部输出重建屏幕，再把尺寸缩一行后还原，让全屏程序重画。
- 推断，未实测：自动拉起的新 core 用的是发起调用那个客户端的环境。如果第一个调用来自终端里的 agent，新 core 会继承 agent 的环境。
- 对 T-212 的含义：编排后台只是 core 的客户端。后台重启不动 core，屏幕与历史完好；只有 core 自身崩溃才丢历史。
- core 与 holder 都会自己脱离调用者：ppid 为 1，各有独立的进程组。

### 4. 输入原样：PASS

- 经 framed attach 的 DATA 帧写入 32 字节：`ESC[200~中文 paste okESC[201~`、CR、ESC、Ctrl-C、Ctrl-D、`x`。raw 模式下的程序收到的字节逐字节相同（run1，十六进制对照）。
- observe viewer 发 RESIZE 帧后，终端尺寸仍是活动 viewer 的 90×25。它发的 DATA 帧 `OBS` 没有到达程序，程序只收到活动 viewer 的 `ACT`（run4）。

### 5. 状态：PASS

各 CLI 都在私有 core 里运行，cwd 为本仓库；提示经 `terminal.send`（粘贴后回车）送入，每个已就绪的 CLI 都收到并处理了。

| CLI 与模式 | 观察到的 OSC 7501 上报 |
| --- | --- |
| Claude Code 2.1.316，haiku，`--permission-mode dontAsk`，未设 `CLAUDE_CODE_DISABLE_TERMINAL_TITLE` | idle → working → done，turn 由 0 变 1 |
| 同上，但 `CLAUDE_CODE_DISABLE_TERMINAL_TITLE=""` | 同上：空串等同未设 |
| 同上，但 `CLAUDE_CODE_DISABLE_TERMINAL_TITLE=1` | 25 秒内没有任何上报，`reported: false` |
| 不传模式（用户自己的默认模式，界面显示 auto mode on） | idle → working → done。`touch` 命令没有弹框，直接执行了 |
| `--permission-mode default` | idle → working → blocked（kind=permission）。按 Esc 拒绝后回到 idle，命令没有执行 |
| agy，`AGY_CLI_OSC7501=on`，不加 `--dangerously-skip-permissions` | 启动后先报 blocked（kind=auth）约 7 秒，之后 idle → working → done |
| opencode TUI | idle → working → idle，turn 由 0 变 1。回合结束报 idle，不报 done |
| Codex 0.164.0，`gpt-6.1-sol`，high，登录过期时 | 停在登录选择页，40 秒内没有任何上报（run9） |
| 同上，重新登录后 | 启动时先报 working，约 4 秒后报 idle，hc 把这一段计为一个回合（turn 由 0 变 1）；送入提示后 working → done（turn 变 2）（run10） |
| 同上，加 `--sandbox workspace-write --ask-for-approval on-request` | 启动直接报 idle；送入提示后 working → blocked（kind=permission）。按 Esc 拒绝后回到 idle，命令没有执行（run11） |

主控由用户自己启动，用的应当就是上表的默认模式。这一点是推断，没有核对过用户实际的启动命令。

### 6. 父子与通知：PASS

- 子终端 blocked、error、退出时，hc 把一行 `<hc>…</hc>` 粘贴进父终端并回车。run3 收到的原文：
  - `<hc>t16 child is blocked (question). See: hc read t16</hc>`
  - `<hc>t16 child hit an error. See: hc read t16</hc>`
  - `<hc>t16 child exited (exit 3). Read: hc read t16</hc>`
- 送达条件（依据源码 `notes.rs`）：
  - 父终端报过 7501，且当前不是 blocked；
  - 无人打字满 3 秒（配置项 `notes_quiet`）；
  - 父终端以自己为 caller 调过 `terminal.get` 查看子终端，即视为已读，不再通知。
- 退出通知的附带内容：子终端退出前报过 7501，所以没有附 "Last lines"；从没上报过的程序退出时，附最后 20 行。
- 父终端 blocked 时，通知会扣住，等父终端回到 idle 才送达（run3 的 parent2）。
- `no_notify: true` 的子终端，父终端一条通知也没收到（run3 的 quietchild）。全局开关是配置项 `notes = false`。
- 这次只确认在 12 秒的观察窗口内送达，没有精确测时延。
- 通知不经过我们的 attach 通道，所以不会被记成用户输入。但它直接进入父 agent 的输入，绕过了收件箱。受管窗格要不要用 hc 的父子关系，留给后续切片决定。

### 7. 私有 session 的边界：PASS

- 私有 core 的 socket 所在目录、状态目录各级权限都是 0700。socket 文件本身是 0755，靠所在目录挡住其他用户。
- 用户自己的 Herdr app 的进程链是 `Herdr.app → herdr-core connect → herdr-core serve`（`~/.local/bin/herdr-core`）。进程环境里没有 `HC_*`、`XDG_*` 变量，连的是默认的 `default` 会话（`~/.local/state/herdr-core/default/default.sock`）。私有 core 的 socket 不在它的查找路径上。探针期间，用户的默认状态目录没有新增任何会话。
- hc 的安全文档写明：会话不是安全边界，同一用户下任何知道 socket 路径的进程都能连上。
- 未测：Herdr app 的界面里能否手动指向别的会话。

### 8. 清理：PASS（macOS 上有一类逃逸）

- 子进程用 `start_new_session` 脱离、被 launchd 收养后，执行 `hc kill`。node（Homebrew）和 conda python 都被清掉了；`/bin/sleep` 活了下来（run2）。
- 原因（依据 `sweep.rs` 注释）：hc 靠进程环境里的 `HC_SCOPE` 找后代。macOS 不让读系统自带二进制的环境，这类进程只能经父进程找到。父进程已经退出、自己又是系统二进制的，就找不到了。上游把"离开 session 并丢掉环境"的进程列为可接受的逃逸。
- 漏下的两个 `sleep` 由主控手动结束。

## 其他事实

- `terminal.send` 的条件参数名是 `if`，作用是只在状态恰好为某个值时才输入。评估报告 `findings/2026-10-31-herdr-core-evaluation.md` 第 68 行写作 `only_if`，以本结果为准。
- 终端名只能由 1～32 个 a-z、0-9、`-`、`_`、`.` 组成，且不能形如 id（例如 `t216` 被拒）。
- 终端记录的 `foreground` 给出前台程序的 argv 和 pid，例如 Claude 的 `name` 是版本号 `2.1.316`。

## 与 T-209 假设不符、需要用户知道的

1. 终端环境只能靠 core 的启动环境来控制。XDG 变量会漏进终端，需要 `HC_SOCKET` 加 `env -u` 的组合（第 2 项）。
2. core 自身崩溃（不是后台重启）会丢屏幕与历史（第 3 项）。
3. 在 macOS 上，脱离后被 launchd 收养的系统二进制会逃过清理（第 8 项）。
4. Codex 启动时可能先报一段 working → idle，hc 的 turn 计数会因此比实际回合多 1；run11 那次启动则直接报 idle（第 5 项）。按 turn 计数判断回合的代码要考虑这一点。
5. agy 启动时有短暂的 blocked（auth），opencode 回合结束时报 idle（第 5 项）。按 7501 推断状态的代码，不能把前者当成真正的阻塞，也不能漏判后者的回合结束；hc 的父子通知会把 agy 这次短暂的 blocked 也报给父终端。
