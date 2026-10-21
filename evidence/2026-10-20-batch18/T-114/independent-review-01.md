# T-114 第一轮独立审查

STATUS: INCOMPLETE
TARGET: `b71fc9b36beb64d9adf811ead64669b2d964fb33..425258993957948f1a7e22507e4e810e5194ed24`，分支 `exec/t114`。

审查目标：只判断指定 diff 的软件改名、中文 README、名称调用方和结构风险。非目标：实现或修复、安装、发布、凭据扫描、清缓存、调用模型。通过条件：必审五项有出处，真实启动反例有证据，并完成角色卡要求的独立变异检查。未知：没有提供门禁一次性副本；没有本轮独立的日常数据前后快照。

已读 T-114 第 2、5 步、WORKER-RESULTS、WORKER-FIX-02、地图、术语表、intent、相关已合入 ticket。候选起止 HEAD 一致。已有两个未跟踪的 outside-build JSON 保持原样；它们是主控运行记录，不算候选提交内容。

## EVIDENCE

### 1. 数据路径与 bundle id：源码核对 PASS

- `workbench/app/package.mjs:48` 的 `appBundleId: 'org.a2a.workbench'` 与起点相同。
- `workbench/app/desktop.mjs:15–20` 仍以 `~/Library/Application Support/a2a-orchestrator` 为默认 state，`user-data` 默认取其 `ui/`，在申请单实例锁之前显式 `app.setPath('userData', userData)`。productName 不参与这条路径计算。
- 用 `git show` 读两版 desktop，起点只替换错误框标题后与候选逐字节相同，结果 True。`main.ts` 也只改窗口标题；其第 620–634、678–679 行的显式数据目录处理未改。
- 因而指定 diff 没有引入因改名而更换默认数据目录的路径，不需要数据迁移。主控报告的安装后行数检查属于主控观察，本轮未访问用户数据库，不能升级为审查者独立的数据完整性实测。

### 2. 旧名称检索：当前调用路径 PASS

全部使用 Git 对固定候选搜索，包含稀疏 checkout 未检出的受控文件，没有以 worker 的搜索输出代替复查。

```sh
git grep -n -I -E 'a2a[.]app|MacOS/a2a|a2a Helper' 425258993 --
git grep -n -I -E 'a2a[.]app|MacOS/a2a|a2a Helper' 425258993 -- workbench scripts acceptance docs README.md
git grep -n -I -E 'a2a[.]app|MacOS/a2a|a2a Helper' 425258993 -- ':!evidence' ':!.project-map' ':!workbench' ':!scripts' ':!acceptance' ':!docs' ':!README.md'
git grep -n -I -E 'a2a 工作台|a2a 启动失败|a2a.*工作台|title\(\)|document[.]title|[.]brand' 425258993 -- workbench/tests acceptance scripts workbench/app ':!workbench/app/*.css'
```

结果：第一条退出 0，共 52 行；第二、三、四条均退出 1、无命中。52 行全部在历史 ticket、收件箱和日期证据中：

| 分类 | 命中行数 | 路径或内容 |
| --- | ---: | --- |
| `.project-map/inbox/` | 9 | 20261019、20261020 的历史报告与决策请求 |
| `.project-map/tickets/` | 8 | T-102、T-105、T-106、T-107、T-114；T-114 明确要求替换旧安装 |
| `evidence/2026-10-19-batch17/T-102/` | 21 | 旧安装脚本、基线、结果和安装记录 |
| `evidence/2026-10-20-batch18/T-114/` | 14 | BUILD-01、WORKER 报告及名称搜索的历史输出 |

旧 T-102 安装脚本仍会操作 a2a.app，它是日期证据，不能当作本候选的新安装步骤。当前 `run_t102_packaged.mjs:16` 已用新应用与主程序路径；`RUN-OUTSIDE-LOCAL-PACKAGE.sh` 已从自身位置定位 workbench 并检查 Enchanted.app。门禁、hooks、scripts 未发现旧可执行名称依赖。没有为追求零命中改写历史。

### 3. README 真实性与出处：内容核对 PASS

以下按根 README 行号覆盖其功能、限制及操作说明；已合入事实以 ticket Resolution 为准，不拿旧候选的运行通过结论证明本次改名。

| README | 核对内容 | 出处 |
| --- | --- | --- |
| 3 | macOS、多 agent、Claude Code/Codex 交互终端、项目→任务→会话、常驻后台、关窗口继续运行 | `docs/index.html:7,30–31,141,149`；T-075、T-091、T-102、T-096 |
| 7 | 虚构预设演示，不连后台、不调用模型 | `docs/index.html:51`；T-113 Resolution |
| 9 | 任务卡、唯一门禁、交付身份与版本绑定、不能自报通过、可信协作者约束而非安全沙箱 | `docs/index.html:93–104`；T-070、T-075、T-080；CONTEXT 的 attempt/session/fence 术语 |
| 13 | Electron/React/xterm.js/node-pty、门禁源码入口、Synara 复用 | T-075、T-102；workbench/package.json、workbench/LICENSE.synara |
| 15 | arm64、两家 CLI、各功能有验证边界、双主控/恢复/日常切换未完成、没有收益承诺 | `docs/index.html:170–174`；T-102、T-096、T-069；intent 切换条件 |
| 17 | 正常登录主控与 worker 后台重启后未恢复 | `docs/index.html:173`；T-096 与 workbench README |
| 21–29 | zip、拖入应用程序、安装登录官方 CLI、ad-hoc、未公证、首次右键打开或 xattr、数据不迁移 | `docs/index.html:170–171,196–202`；T-102、T-114 第 2、3 步；上述路径源码核对 |
| 33–79 | Node 版本、内置盘、构建槽、产物路径、隔离启动、凭据、多个 launch、权限经参数传入 | T-102、T-103、T-075；AGENTS 构建裁定；package.json；build/package/start/desktop 直接入口与 workbench README |
| 89 | 文本证据、外置盘归档、历史映射限制 | T-088、T-101；本段原有内容未改 |
| 93 | GPL-3.0、Synara MIT | 根 LICENSE 为 GPL v3；workbench/LICENSE.synara 含 T3 Tools / Emanuele Di Pietro 的 MIT 原文 |

没有发现 README 把路线图写为已完成功能，或增加可靠性、吞吐、成本收益主张。第 23 行明确“没有经过 Apple 公证”，第 52 行另有“未公证”；右键打开及解除隔离命令都存在。

T-113 指出的两处旧文档已改：根 README 第 35–41、62 行不再要求外置盘构建；workbench README 第 11–14 行与 T-111 Resolution 的 RUN-OUTSIDE-03、REVIEW-OUTSIDE-02 及计数/缺 attempt/写库反例相符。

产品页与下载链接是发布后的目标地址，本轮不核验在线状态，不宣称 Pages 或 Release 已发布。

### 4. 界面产品名：应用内最小改动 PASS；产品页有同步项

应用源码仅改四处可见文字：desktop 错误框、HTML 标题、BrowserWindow 标题、侧栏品牌。保留 a2a 内核、window.a2a、IPC、包内 name、目录、缓存和任务身份，符合 Ubiquitous language 中产品与内核的分工。未发现把内部协议名称过度改成产品名。

范围外发布前同步项：`docs/assets/demo.js:203` 侧栏仍为 `a2a / 工作台`，第 411 行仍为 `a2a 工作台（演示）`。独立执行的命令：

```sh
git grep -n -I -E 'a2a 工作台|a2a.*工作台|a2a 启动失败|a2a Helper|a2a[.]app|MacOS/a2a' 425258993 -- docs
```

命中上述两处。这两个文件位置不在指定 diff 中，未修改，也不将其冒称为 diff 内代码缺陷；现产品页与新应用可见品牌不一致，交主控在发布范围中同步处理。

### 5. design-integrity-review：结构核对 PASS

- Packager 的 name、executableName、最终 app 路径统一为 Enchanted；候选中没有 afterCopyExtraResources 或改 plist 的钩子。名称生成由打包器自身负责，消除了原来主包名与 helper 名不同的根因。
- 没有增加依赖、兼容路径、备用入口、重试、平行 API 或浅层包装；Deep modules 没有新增设计成本。
- 对指定 diff 调用 skill 的 `scan_unified_diff`（不扫描任意工作树改动）：定位到 BUILD-01:97、BUILD-02:101 的 BaseException。人工确认均记录失败后重新抛出，不吞错或降级为 PASS。
- 扫描器不覆盖 .mjs，另人工检查启动探针：外层 catch 记录错误，清理 catch 保留隔离现场；仅 startup_passed 与 cleanup_complete 同时成立才 PASS，进程退出码相应非零。清理只指向本次子进程及隔离 state，经既有门禁 daemon_stop 收尾，没有按名称批量杀进程。

## COUNTEREXAMPLE

已读回主控的真实边界证据，未重跑或改写：

- `outside-build-build-02.json`：revision 精确为候选完整提交号；四个 plist 字段、四类 helper、codesign、主进程、renderer helper、独立进程组 daemon、界面就绪、退出及清理均记录通过。启动使用随机临时 state/ui，无 agent CLI。
- `/private/tmp/t114-helper-counterexample-20261021T030118Z.json`：旧产物被同一启动探针拒绝，状态 NO_GO、cleanup_complete=true；stderr 实际含 `Unable to find helper app`。这能拒绝上一轮“签名和 plist 都通过但无法启动”的错误实现。
- 角色卡要求的审查者 2～5 个变异：NOT_RUN。没有提供门禁创建的一次性副本；没有在作者 worktree 或自行创建的非门禁副本里改实现。已有主控反例不能冒充这项独立工作。
- 若补验，至少应覆盖“默认 state 改为 Enchanted 目录”和“bundle id 被改动”两种变异。当前启动探针显式传入 state/ui，因此单独一次启动通过不证明默认路径不变；本轮对此使用独立的起点 diff 核对。

## FINDINGS

指定 diff 内没有确认的可达代码缺陷。范围外的产品页旧品牌已列出，未用问题面板另行上报，遵照派发限制直接交给主控。

## LIMITATIONS

- 总评 INCOMPLETE 的直接原因是角色卡的独立变异检查未完成。behavioral-acceptance-review 要求“PASS requires independent behavioral evidence”；本报告不将主控运行记录改称审查者复验。
- 未独立启动 GUI、重打包、调用模型、检查用户数据库或验证线上发布；用户安装与数据行数保持是主控提供的观察。
- 项目 status 起止均退出 1：8 项 findings/旧 grilling 文件缺失，stale living docs 为 0。未修稀疏 checkout，不能报 T-114 全部验收通过。
- 已执行 `git diff --check b71fc9b36 425258993`、四个相关 JS/MJS 的 `node --check`、候选新增/修改 shell 的 `bash -n`，均退出 0。它们仅证明格式或语法，不替代行为证据。
- 只新建本报告；未 commit、push、gh、升级权限、写全局配置或开子 agent。

## RULE

helper 名不一致这一失败类已有对应机械检查：BUILD-02 必须经过同一个真实启动探针，COUNTEREXAMPLE-02 必须拒绝旧产物。保留该检查作为发布前门禁证据，不再以 plist/codesign 单独通过替代真实启动。

T-114 REVIEW INCOMPLETE
