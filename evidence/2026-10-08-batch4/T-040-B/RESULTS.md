# T-040 B：工作台启动器与主控门禁入口（2026-10-08）

**INCOMPLETE：B 部分的真实隔离验收已 PASS；全仓测试有 5 项失败，尚未证明基线也失败。** 最终产品提交在 fork 的 `a2a` 分支：`28e2f1b4ca6634d4faba9bd921a55a51640407e4`；初稿 `c426a5f939e26a69606616cc88df59cd898efe25` 和失败审查均保留，起点为 `d3b5bcc61cc212572f38e01139e1b9af2196b820`。未 push。T-040 保持 open，日常真实分派和专用目录首次启动留给主控；本次没有登录或调用 Synara provider，另做了一次模型独立审查及一次限定复审。

## 交付与使用

fork 新增 `a2a/scripts/workbench`、`gate`、共享运行身份模块、Electron 启动脚本和中文 `a2a/WORKBENCH.md`。桌面源码只增加 26 行生命周期接入。默认数据目录为 `~/Library/Application Support/a2a-workbench`，Electron profile 放在其 `electron-profile/`，与官方 Synara 分开。

在 fork 根目录运行 `./a2a/scripts/workbench`；查状态用 `workbench status`，停止用 `workbench stop`。启动器检查真实外置挂载点与设备，每次新启动经 `a2a/scripts/bun run build:desktop` 检查标准产物，由既有构建系统处理缓存与恢复，不另做一套构建记录。启动成功还要求后端 `/health` 的 `startupReady=true`。构建缓存留在外置盘，没有移动、替换或链接 dist、node_modules。

后台 Electron 使用独立进程组。重复启动保留同一实例；停止前核对 PID、启动时间和命令，用工作台专用 SIGUSR2 进入既有优雅退出流程。初稿用 SIGTERM 时进入界面退出确认并超时，失败及 UI 收尾保留在 `live-01/`；专用信号仅为工作台注册，普通界面退出仍保留确认。

主控调用 `./a2a/scripts/gate status TASK_ID` 或传门禁请求 JSON。它读取专用目录的 `a2a-gates/endpoint.json`，经现有 `packages/a2a-gates/src/cli.ts` 的 HTTP transport 调用唯一门禁，不直接访问数据库。token 来自桌面每次运行生成的 backend auth token；endpoint 原子写入、0600，后端重启重新发布地址，后端退出删除。泄露会获得本次 Synara 后端的 owner 权限，范围超出门禁；不得提交或分享 endpoint、token、认证 URL 与环境转储。本次证据仅保存地址、PID、权限和轮换的布尔结果，没有 token。

启动器保留用户 HOME/CODEX_HOME，沿用 Synara 正常 overlay，不复制认证、不改写 `~/.codex`。验证使用空的隔离 HOME/CODEX_HOME/Claude/XDG 目录和全部 disabled 的 provider 设置，未实际验证用户登录或模型会话。

## 证据与结果

最终的 `live-03/result.json` 和逐命令日志是实际入口证据，预期来自任务书；测试输入为新建独立 Git 夹具、随机 task/project id。标准构建、Electron、后端、HTTP、进程组和端口均使用真实边界。

| 检查 | 结果 |
| --- | --- |
| 原入口缺失的合同红态 / 新入口调用 | `red-entry.json` 退出 1；`green-entry.json` 退出 0 |
| 缺盘拒绝、无数据目录副作用 | `missing-volume.log` 退出 2；`environment.json` 的 `data_created=false` |
| 默认目录 | 前后均不存在；只读 status 返回准确路径与 `running=false` |
| 启动与重复启动 | Electron PID 48530、后端 48570；独立进程组；重复启动保持原 PID 与 endpoint；独立 HTTP 读回 `startupReady=true` |
| HTTP gate status | 独立夹具任务 `probe-t040b-f52yl5yd` 返回 `ready`；不存在的 task 返回失败 |
| endpoint / 鉴权反例 | 0600 正例通过；改为 0644 被 gate 拒绝；错误 token 的 HTTP 请求被拒绝 |
| 停止与重启 | 两轮 stop 均退出 0；IPv4/IPv6 无监听、endpoint 删除；新 token 与 PID 不同、任务仍可读 |
| 最终收尾 | `cleanup-reviewed.json`：三次运行的全部桌面进程组无残留、无 auth.json、默认目录未创建 |
| 格式 / lint / 全仓类型 / 进程边界 | reviewed/final 日志均退出 0；lint 有既有 warning，不称零 warning |
| 全仓测试 | 继续执行模式退出 1：desktop 3 项失败、server 2 项失败；其他 5 个 workspace 成功 |

首轮 `live-01` 缺 project id 的创建请求返回 `invalid_id`，这是夹具输入错误，不能充当产品修复的红态。首轮跨目录 TypeScript 模块触发 TS6307，失败保留在 `desktop-typecheck-01.log`；最终将小接入留在桌面原生命周期代码，全仓类型检查通过。所有失败均保留，没有重写旧结果。

独立审查首次发现“HTTP 200 提前成功”和自建构建记录跳过恢复两个缺陷，原文见 `independent-review-01.txt`。`probe-review.py` 的同一输入在完整旧提交上失败、新提交上通过，见 `review-parent-red.json` / `review-candidate-green.json`：真实 loopback HTTP 分阶段返回 false、false、true，候选等待到 true；旧构建记录不再跳过标准命令。该探针替代了桌面和构建进程，只证明等待与调用逻辑；实际 Electron、标准构建及 4/4 缓存重启另由 `live-03` 证明，没有实际破坏共享构建产物。

复现命令（从 a2a 根目录执行；label 必须换新值，脚本拒绝覆盖）：

```sh
python3 evidence/2026-10-08-batch4/T-040-B/run-e2e.py --label NEW_LABEL
python3 evidence/2026-10-08-batch4/T-040-B/probe-review.py --revision c426a5f939e26a69606616cc88df59cd898efe25 --output NEW_RED.json
python3 evidence/2026-10-08-batch4/T-040-B/probe-review.py --output NEW_GREEN.json
```

脚本新建外置盘测试根目录，准备 disabled 设置，执行真实启动、独立任务创建、HTTP status、反例、停止和重启。完整 argv、cwd、退出码见对应 `result.json`。三轮外置原目录保留；独立夹具 Git 元数据、门禁状态、oracle 与输入已完整归档为各轮 `retained-fixture.tar.gz`，没有登记 gitlink，没有归档 Electron profile、运行秘密或认证副本。

## 范围与待主控处理

独立限定复审见 `independent-review.txt`，仅对两项修正返回 PASS。本次不宣称全仓测试通过、用户登录可用、真实模型闭环通过或 T-040 切换完成。全仓失败为 `appSnapManager` 批次保留、`cuaDriverHost` 权限变更后退休、native 图标持久化，以及 `ProviderCommandReactor` 两项慢响应行为；未在父修订上复现，本轮不扩展范围修复。主控需决定先做父修订对照，还是单独跟踪这 5 项失败并接受 B 的限定功能验收，再决定日常首次启动和分派。

中途项目地图报告过 A 部分删除 `coop.py` 所触发的 `CONTEXT.md` stale，原记录保留；最终 `project-map-reviewed.txt` 为 0 problems / 0 stale。B 未改地图、术语或治理规则，仅在 T-040 Resolution 追加本部分结果。原有 `.grok/`、其他 worker 的改动、官方 Synara/用户浏览器数据和 Herdr 未处理。

中文报告、使用说明和 ticket 已回读，UTF-8 无 BOM、无替换字符。`git diff --cached --check` 退出 2，原因是原始 lint/build 日志中的尾部空格和空行，原输出保留在 `diff-check.txt`；未为格式检查改写运行证据。产品源码的 diff 检查通过。

## 追加：主控决定 01 的父修订对照（2026-10-08）

**PASS，仅指本轮有界对照执行完成；原全仓失败及上文 INCOMPLETE 记录不覆盖。** 按 [主控决定 01](controller-decision-01.md)，4 个完整测试文件在父修订 `d3b5bcc61cc212572f38e01139e1b9af2196b820` 和候选 `28e2f1b4ca6634d4faba9bd921a55a51640407e4` 上，各单独运行 3 次，共 24 次。每一对都是父 → 候选，全部串行，24 次退出码均为 0。原 5 个失败用例在两边分别 3/3 通过，其余同文件用例也没有父过候选挂的信号。

| 完整测试文件 | 每次实际用例数 | 父修订三次 | 候选三次 |
| --- | ---: | --- | --- |
| `appSnapManager.test.ts` | 52 | 52/52、52/52、52/52 | 52/52、52/52、52/52 |
| `cuaDriverHost.test.ts` | 150 | 150/150、150/150、150/150 | 150/150、150/150、150/150 |
| `macAppIcon.native.test.ts` | 1 | 1/1、1/1、1/1 | 1/1、1/1、1/1 |
| `ProviderCommandReactor.test.ts` | 436 | 436/436、436/436、436/436 | 436/436、436/436、436/436 |

完整原始输出、Vitest JSON 与版本/时间/argv 绑定记录在 [parent-comparison-01](parent-comparison-01/summary.json)。`summary.json` 核对 24 个文件/版本/轮次组合、串行时间与 5 个原失败用例；同时扫描同文件全部用例，没有发现基线各次通过而候选失败的用例。没有修改产品代码、上游测试、测试断言或用例超时，没有执行真实 provider 调用，因此 fork 不新增提交。

准备阶段首先建立两个 detached worktree，尝试标准 frozen-lockfile 安装；父安装持续读取外置缓存，在我自设的 1,800 秒安装保护期限到达时被收尾，未执行或计入任何测试。部分安装目录、原日志和 INCOMPLETE 事件原样保留。随后使用主控已经允许的共享 checkout 方式：重新确认 A 的 160 次计时已结束、无活动的 A 计时/恢复测试/门禁 `--state` CLI，且受控文件干净，才开始切换。`switch-preflight.json`、`execution-method.json` 与 `switches.jsonl` 保存这一过程；没有移动、替换或链接任何构建输出或依赖目录。

每次测试经该修订的 `a2a/scripts/bun` → `env TMPDIR=/Volumes/WD-Elements/b4-dzu7pil6/t` → `bun run --cwd apps/desktop|apps/server test FILE --reporter=json --outputFile=...`。使用既有依赖、空的隔离 HOME/CODEX_HOME/Claude/XDG 数据；Bun/Node 仍为 1.4.2/24.13.1。运行前检查 A 进程，运行中每秒采样；24 次均未观察到 A 重叠。采样不能证明任何亚秒级活动都不存在，不据此宣称全机无并发负载。结束后恢复 `a2a` 分支和候选完整提交，受控源码无差异，测试进程无残留，默认专用目录仍不存在，隔离根无 auth.json。

此轮没有触发回归修复条件。准确结论是“原全仓失败在短 tmp、单文件串行及隔离 HOME 的本轮条件下未复现，未检出 B 候选独有失败”。这些条件同时变化，不能锁定路径或负载为根因，也不能把两边均通过直接当作已证明的上游缺陷。原全仓退出 1 仍是真实失败，T-040 整体继续 open，由主控结合 A 的结果决定后续切换。

复现入口为 `parent-comparison-01/run-shared.py`；再次运行必须创建新的证据目录与短路径 setup，脚本拒绝覆盖已存在的结果矩阵。原始脚本、失败安装现场、源码与 Git worktree 元数据归档均保留。独立只读核对另存 `parent-comparison-01/independent-review.txt`，其结论只覆盖本轮比较的完整性和上述限定声明。

独立审查对冻结证据提交 `62c4618689981814cfe641b8afbe3f9f4facb3fa` 返回 PASS，逐份核对了 24 份原始 JSON、3,834 个断言、原 5 项的全部出现次数、交替顺序和完整版本绑定，没有仅相信汇总。它同样保留“一秒采样不能排除未观察到的短暂并发”及“原全仓失败根因 INCOMPLETE”的边界，不授权把 B/T-040 整体或全仓验收改称 PASS。
