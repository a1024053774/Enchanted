# T-188 结果：发 0.1.5，补齐产品页与 GitHub 各处，替换 /Applications

## 状态：PASS（一项与 ticket 字面不同：从 Dock 启动做不到，改用干净环境经 LaunchServices 启动，见下）

## 依据

ticket T-188（ready_rev 1）。用户 2026-10-26 原话：“再发一个版本,完善现在没更新的产品页,GitHub 之类的所有以及我的 applications里的.”（构思主控 assign `20261026T034537Z-ideation-assign-001`）。签名问题按用户“先不管”，照实写 ad-hoc。

## 结果

| 项 | 状态 | 依据 |
| --- | --- | --- |
| 版本号 | 0.1.5 | `workbench/package.json` 与 `package-lock.json` 顶部两处 |
| 发行说明 | PASS | `release-notes.md`：四种 CLI、agy/opencode 作 worker 与审查员、Git 元数据守护、没接入检测；升级提醒写了 agy 主控启动方式、agy 目录信任写 `~/.gemini`、Codex 钩子信任框（钩子命令与 0.1.4 相同，信任过的不再问）、换版后 macOS 收回“文稿”授权；已知限制照实 |
| 产品页 | PASS | `docs/index.html`：描述与首屏改为四种 CLI；角色申请一步写四种命令；“目前支持的 CLI”改为 0.1.5 已带；“0.1.4 更新”换成“0.1.5 更新”；已知限制加 ad-hoc 签名与“文稿”授权。演示是可点击的虚构界面，没有静态截图；`demo.js` 设置说明改为四种 CLI |
| README | PASS | 仓库 `README.md`：四种 CLI、项目终端主控经 `a2a request`（删掉“普通终端没有门禁身份”的过时说法）、agy 主控启动方式、`~/.gemini` 例外、“文稿”授权提醒。`workbench/README.md`：任务卡 CLI 值、主控启动、没接入提示、打包启动配置找 agy/opencode、agy/opencode 主控不记用户输入 |
| 门禁回执文字 | PASS | `card_validate` 的规则说明原写“13 个字段……CLI 为 Claude Code 或 Codex”，改为 14 个字段、CLI 列表由 `workerClis` 生成 |
| 残留说法 | PASS | `git grep` 两种 CLI 的说法：剩 `RecordsPage.tsx`、`demo.js` 的“只记你批准为主控的 Claude Code 或 Codex 收到的整条提示词”与 `workbench/README.md` 用户输入一节，都符合事实（agy、opencode 主控不记） |
| 安装包 | PASS | `build.py r2`：浅克隆 `d68a5d50e`，`npm ci` + `npm run package:mac`；`CFBundleShortVersionString` 0.1.5；`codesign --verify --deep --strict` 通过，ad-hoc；`spctl` 拒绝（未公证，与之前各版相同）；包里有 `terminal/bin/agy`、`opencode` 与 `terminal/orientation/AGENTS.md`。r1（`e34300d70`）在审查第一轮后作废，因 `core.ts` 改了 |
| 推送 | PASS | `credential-scan-01.json`：`fa1ab8b57..main` 0 命中（两个用户邮箱、agy 账号邮箱、密钥样式），无凭据文件、无大于 1 MB 的文件；`fa1ab8b57..16bd0b514`，没有 force push |
| Release v0.1.5 | PASS | 目标 `d68a5d50e`（安装包源码）；正文 `release-notes.md`；附件 `Enchanted-0.1.5-macos-arm64.zip` 147,701,583 字节，下载回来逐字节相同；标为 Latest，v0.1.0～v0.1.4 保留 |
| 仓库 About、topics | PASS | 描述改为“让 Claude Code、Codex、agy 与 opencode 在门禁下协作的 macOS 工作台……”；topics 加 `opencode`、`antigravity-cli` |
| Pages | PASS | 构建 `built 16bd0b514`；线上 200，含“0.1.5 更新”“0.1.5 已带” |
| 页面检查 | PASS | T-182 的 `check.mjs` 原样复制：`local-01`、`local-02` 43/43，线上 `live-01` 43/43；截图在外置盘（`shots-*.archive.json`） |
| Chrome 复看 | PASS | lcu 在 Chrome 打开线上页下载一节，显示正常（`page-chrome-0.1.5.jpg`），标签页已关 |
| 替换 /Applications | PASS | 替换前运行情况：0.1.4 应用（pid 60214）与其后台（pid 60387）是 T-186 复看时由执行主控启动的；后台下只有一个空闲 zsh（pid 60619，T-186 测试项目的终端），没有运行中的 agent 会话。SIGTERM 停后台与应用；从 Release 下载的包解压替换，0.1.5、签名核对通过；0.1.4 包暂存后删除 |
| 启动核对 | PASS（方式不同） | lcu 选不到 Dock（`timeoutReached`，与 T-186 相同），改用 `env -i /usr/bin/open -a /Applications/Enchanted.app` 经 LaunchServices 启动；核对应用与后台进程的环境里没有 `HERDR_*`、`AI_AGENT`、`CLAUDECODE`、`CODEX_*`。窗口显示“后台已连接”，侧栏列出用户原有项目（a1024053774.github.io、a2a、a2a-lcu-demo），只读核对，没有点按 |

## 独立审查

- 第一轮 `review-agy-01.md`（候选 `e34300d70`）：`T-188 REVIEW INCOMPLETE`，7 条：工作台说明任务卡 CLI 值（P1）、`card_validate` 规则文字（P1）、主控启动与打包启动配置（P2）、没接入提示写死 claude、演示设置说明、仓库 README 缺“文稿”授权提醒（P3）。全部修正。
- 第二轮 `review-agy-02.md`（候选 `bc97dc98e`）：`T-188 REVIEW PASS`。

## 备注

- 隐私授权弹窗：本次启动后没有在 Enchanted 里启动 CLI，没有触发“文稿”授权；换版后第一次在 Enchanted 里用 CLI 读“文稿”下的目录时会弹，需要用户本人允许。
- 侧栏里 a2a-lcu-demo 项目的目录已在 T-187 清理时删除（显示“无法读取 Git”），它是测试项目；是否从列表移除留给用户。
