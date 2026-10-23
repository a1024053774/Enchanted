# T-155-1 / a1：启动交接

状态：INCOMPLETE。实例 1 的启动准备缺陷已保留并修订；实例 2 已实际运行，覆盖并行 worker、问题答复、打回重交与独审，但三票均未集成。当前模型执行已停止，下一步只做同后台的 UI-only REOPEN、停止后统计与归档。没有完整真实使用通过结论。

被测产品基线：`f3412fb4ae5cfa3c4983440eb26ea8c5b34b0697`。脚本启动前检查 `workbench/` 与该版本无受控差异。准备脚本的提交不会改产品。

## 主控在沙箱外启动

在本 worktree 根目录运行：

```sh
bash evidence/2026-10-23-batch24/T-155/START-APP.sh
```

脚本先打印 `INSTANCE=/private/tmp/t155-dogfood-...`。请保留此路径；失败也保留整个目录及日志，不重复运行来掩盖失败。成功时打印 Electron PID、daemon PID、repo、state、user-data 和 control socket 路径。看到窗口后告知 worker 窗口已就绪，并提供实例路径与 PID。

首次启动会：

1. 用 `mkdtemp` 在内置盘 `/private/tmp` 新建私有目录，创建独立 `state/`、`user-data/` 和操作员凭据 `operator.json`。不采用继承的 `A2A_*` 身份或凭据路径。
2. 创建 `demo-repo/`，以 `main` 为初始分支，写入 README 与五项食材清单并提交；不配置 remote。种子提交屏蔽继承的 Git 钩子、签名和 worker 身份。
3. 按产品标准 `app/build.mjs --slot <唯一槽名>` 构建，构建槽在本实例目录内，使用已有本地依赖，不安装或替换依赖。
4. 经产品唯一 CLI 调用 `--state <本实例>/state daemon_start --launch-config <本实例>/launch-config.json`；它以 detached 子进程启动后台。配置按 `desktop.mjs` 的 worker 启动字段提供本机 Claude 路径、worker/reviewer/monitor 角色卡及版本、产品版本、每会话 6 回合与本票授权引用；只配置 Claude，不配置 Codex 或读取 Codex auth。直接启动已安装的内置盘 Electron 二进制，显式传入 `--state`、`--user-data`，通过 `start_new_session=True` 脱离调用者进程组。

启动脚本只管理生命周期；不会创建产品内项目、角色或任务。全部业务操作由 worker 看屏幕后用 Computer Use 完成。不使用测试 Electron driver、CDP、DOM 或数据库驱动流程。

## 停止与 REOPEN

仅关闭本实例 Electron，保留 daemon、CLI 与全部证据：

```sh
bash evidence/2026-10-23-batch24/T-155/STOP-APP.sh /private/tmp/t155-dogfood-实际路径
```

停止脚本核对记录中的 PID、启动时间、完整命令后才发送 SIGTERM，并等退出确认；不按进程名关闭应用。worker 要求 `REOPEN` 时，由主控先运行上面停止命令，再运行：

```sh
bash evidence/2026-10-23-batch24/T-155/START-APP.sh /private/tmp/t155-dogfood-实际路径
```

重开沿用原 state、user-data、构建和后台，只新开界面。脚本拒绝重复窗口，以及启动结果未确认的实例。关闭再重开界面的恢复表现留给 Computer Use 记录。

整轮结束后停止界面和后台：

```sh
bash evidence/2026-10-23-batch24/T-155/STOP-APP.sh /private/tmp/t155-dogfood-实际路径 --all
```

后台停止只走本实例 `daemon_stop`，等 PID 与 socket 消失。脚本不删除目录、仓库、认证文件或证据。最终归档按 T-088 单独交接，外置盘未挂载时报错，不回退。

## 一次性测试仓库的独立建法

只创建实例目录和种子仓库，不构建、不启动任何进程：

```sh
python3 evidence/2026-10-23-batch24/T-155/app_lifecycle.py prepare
```

随后可把打印的实例路径交给 `START-APP.sh <实例路径>`。每次 `prepare` 或无参数 `START-APP.sh` 都创建全新仓库。种子是 `README.md` 和 `pantry.json`，建法在 `app_lifecycle.py` 的 `prepare()`；无模型生成的预置任务结果。

拟给应用内主控的真实需求是：为食材清单生成按类别汇总的库存说明与零库存补货单，再更新使用说明。要求拆成 2～3 个受管任务，至少两个并行；由主控走真实审查与集成。具体交互根据屏幕推进，打回、问题上报与人工介入在运行中按任务卡要求实测，不预写门禁结果。

## 预算与证据

应用内主控以 `claude --model claude-haiku-5-5` 启动；本轮优先让 worker、reviewer 和 Reflect 也使用该模型。当前外层 Codex worker 占一个 Codex 会话；应用内无需新开 Codex，若实际需要则仍遵守应用内最多两个、全局最多三个的限制。

真实模型回合合计上限 60，逐场记录主控输入、worker 回合、回执、审查与复盘；接近上限时停止新增模型回合，保留未完成项。后台启动成功不代表窗口就绪；CLI 启动成功或模型自报不代表业务验收通过。

运行证据将记录到 `RESULTS.md`，包括步骤截图索引、回合数、代批记录、REOPEN 与新实例复现。报告只记发现和建议，不改产品。系统隐私授权、登录、付款及任务卡列出的其他越界操作出现时停下报主控。

首份准备提交遗漏 `--launch-config`，实例 1 在三个主控回合后停下：派发报 `launch_config_required`，没有 worker 启动，两个任务留在 preparing。现场与截图完整保留。这是本票启动脚本缺陷，不据此宣称正式产品无法启动 worker。修订脚本仅用于新实例，不修复旧 attempt，不改产品。

修订后只做 Python / shell 语法、帮助入口、新种子仓库与启动配置字段检查，不自行启动 daemon、Electron 或模型。实际启动、停止与重开仍由主控沙箱外执行；本轮任务整体保持 INCOMPLETE。旧实例缺配置，不能用于继续派发；重新运行无参数 START，或先 prepare 再对新路径 START。
