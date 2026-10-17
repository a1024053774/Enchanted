# T-093 前置探针交接（2026-10-17）

状态：INCOMPLETE。probe-02 已证明精确钥匙串读取与无 BASE_URL 时的隔离登录识别；
主控已从 probe-07 脱敏输出定位到 onboarding 的官方连通性检查；该临时文件已由主控删除。
静态发现见 [ONBOARDING-STATIC-08.md](ONBOARDING-STATIC-08.md)。probe-08 的完成状态已生效；主控 #70 要求 probe-09 保留状态并导出新屏幕，见 [PROBE-09.md](PROBE-09.md)。
原权限保持、旧探针全部保留，未改产品代码。终端正文不进入本目录或 Git。
4 处真实 HOME 引用的说明仍见 [PROBE-05.md](PROBE-05.md)，主控 #67 已表示可接受。
本轮不做 fs_usage 或归属采集，原始清单差异继续照实记录，验收修订等待构思主控裁定。
绑定：T-093-1 / attempt a1 / writer s16-t093 / ready_rev 1 / 起点 `61786370428c3ec5f894ea60acccf2695d54c2dc`。

目标是核对三件事实：现有订阅登录的存储位置、只复制登录凭据后隔离 HOME 的登录识别、
指定本地地址后请求是否携带同一登录凭据。非目标为真实上游请求、模型回复、产品实现或门禁变更。
探针失败或结果含糊时停下交主控，不尝试改用真实 HOME，不增加凭据来源，不刷新登录。

## 待主控审阅的只读清单范围

| 路径（相对真实 HOME） | 读取内容 | 比较项 |
| --- | --- | --- |
| `.claude/`（递归） | 文件名、lstat 元数据；只在选中 auth 来源时读 `.credentials.json` | 存在性、类型/权限、字节数、mtime_ns、inode、符号链接目标文字 |
| `.claude.json` | 文件名与元数据 | 同上 |
| `.claude.json.backup` | 文件名与元数据 | 同上 |
| `Library/Keychains/`（递归） | 文件名与元数据，不读数据库正文 | 同上 |

不跟随符号链接（包括 Library 等祖先，以目录 fd 和 `O_NOFOLLOW` 逐级打开），不读设置、历史、钥匙串数据库正文；
不记录 atime，不读取或比较其余 HOME 路径。
前后完整清单只在内存中，报告保存条目数和差异路径。无差异仅表示这些元数据未变，
不能证明正文未曾变化。其他正在运行的 Claude/系统钥匙串服务可能造成差异，脚本不判断因果。
证据目录和源码位于 `~/Documents`，在比较范围之外。

凭据来源限 `~/.claude/.credentials.json` 与钥匙串精确服务 `Claude Code-credentials`。
只执行该服务的 `security find-generic-password`，显式限定到 `~/Library/Keychains/login.keychain-db`，
不使用隔离 HOME 的默认搜索位置，不枚举其他条目、不写钥匙串。该文件已只读核对为现存普通文件，路径含链接或文件缺失即停止。
精确查询的只读 profile 与隔离环境均不变，不添加 Mach allow 或放宽其他权限。
若出现系统钥匙串授权对话框，不点 Allow 或 Always Allow；让 5 秒期限结束并报告失败。
若文件和精确服务同时存在、来源为自定义 `CLAUDE_CONFIG_DIR`、登录过期或格式未知，立即停止。
仅将 `claudeAiOauth` 对象写入隔离目录的 `.credentials.json`（0600）；不复制设置、账号资料、历史或其他凭据。

## 方法与停止条件

REALITY GATE: INCOMPLETE

- **observed**：现有产品只构造固定假 token 的本地 API profile；`controller_start → startController → claudeLaunch` 是现有通路。
- **observed**：本机 CLI 链接指向 `~/.local/share/claude/versions/2.1.302`；未在本 worker 中运行它。
- **observed（主控 #58）**：probe-01 在隔离环境不可见的精确服务，在主控未加 profile 的环境中查询返回 0；未读取密码。
- **observed（主控 #61、#65）**：显式单一钥匙串读取退出 0；隔离 HOME 中无/有 BASE_URL 的状态均识别 claude.ai 登录。
- **unknown**：交互启动为何未产生本地 HTTP；自定义地址实际请求是否携带复制的登录凭据。
- **probe owner**：执行主控在沙箱外运行下面脚本。证据为新建的 JSON 摘要，始终不覆盖旧结果。

1. 建立 `/private/tmp/t093-probe-*`，所有 CLI 工作目录、HOME、配置、tmp 均在其中。
   `sandbox-exec` 禁止子进程写隔离目录之外的位置，禁止读取真实 HOME（仅放行 CLI 可执行文件本身），
   禁止访问名称含 Security/security 的 Mach 服务，禁止网络和创建子进程；写保护反例仅尝试写隔离夹具，绝不尝试写真实 HOME。
   启动前用无凭据子进程检查真实 HOME 读保护、隔离夹具写保护、活跃的本地拒绝端口与实际 fork 拒绝。
   精确钥匙串读取单独施加只读、无网络、禁止 fork 的 profile；假上游禁止 fork 与主动外连。
   如 CLI 需要创建辅助进程才能完成初始化，本次探针停止，不自动放宽限制。
   复制凭据前，先在带端口 profile、无凭据隔离 HOME 下单独验证版本与读/写/fork 限制、许可端口正例和另一活跃端口反例。
   probe-08 显式选项只预先生成完成状态，其他文件不复制；未选时保持空配置。
   网络例外仅为 `remote tcp4 "localhost:<固定端口>"`，其余限制不变。
2. 先执行 `--version`、`--help`、`auth --help`、`auth status --help`。
   帮助里有 `status` 和必要启动参数、版本精确为 `2.1.302 (Claude Code)` 才继续读取登录凭据。
   官方 CLI 文档将 `auth status` 定义为本地登录状态查询；探针仍禁止其所有网络。
3. 只复制 auth，再执行帮助确认支持的 `auth status --json`。要求 JSON 的 `loggedIn=true`、`authMethod=claude.ai`，
   `configDirectory` 精确为隔离目录。原始状态输出可能含邮箱，始终只在内存，不写证据。
   在解析前记录 stdout/stderr 的退出码、字节/行数、固定前缀类别及结构布尔值；不保存原始前缀或内容。
   非 JSON 或包含警告前缀时停止，不剥离前缀继续，不改成文本格式。
4. 启动独立假上游，设置 `ANTHROPIC_BASE_URL=http://127.0.0.1:<端口>`，只放行该端口。
   先用 `--version` 核对新端口 profile 能启动同一 CLI，再做一次状态查询；失败时保存同样的安全结构摘要并停止。
   然后通过 PTY 启动交互式 CLI，传入一条固定探针输入；不用 `-p`/无头模式。
   自动按键仅限已知主题、说明、隔离工作目录信任屏，每种只按一次；未知屏幕 35 秒内停下。
   假上游固定返回 400，没有上游地址、外连或转发代码，不生成任何模型回复。
   最初复制的 token 通过匿名管道进入假上游内存并固定，不从 CLI 可写副本重读。
   逐条记录方法、去 query 的路径、body 字节数、是否含 messages、bearer 是否等于最初复制的 access token；
   不记录 header 值、请求正文或凭据，URI 路径含 token 时在落盘前脱敏。
   收到携带匹配 bearer 的 `POST /v1/messages` 后即停止 CLI。
   这是发往本地假上游的协议请求，不是真实模型回合。
5. 再查登录状态，停止所有子进程组，对比真实 HOME 清单，删除整个隔离目录（正常退出、异常、SIGINT/SIGTERM 均走清理）。
   SIGKILL、断电等不可捕获中断不能保证清理；若出现这类中断，先由主控清理残留，不继续下一次运行。
6. 摘要写盘前扫描 access/refresh token 原值、JSON 转义、URL 编码和 base64；命中则不输出对应内容，
   只保存 NO_GO 和命中数。CLI 原始输出另在内存扫描，只保存命中数；probe-07 的脱敏临时文件按上面专页的限定路径和规则导出。

实际可执行文件路径在真实 HOME 内，探针不复制可执行文件、不隐藏这个事实：
`launch` 保存实际 `sandbox-exec` argv、CLI argv 与环境；`real_home_path_mentions_in_launch` 如实计数，
包括沙箱规则中用于拒绝读取的真实 HOME 前缀。未尝试路由启动时该计数为 null，不冒充零命中。
报告正文用 `<REAL_HOME>` 代替真实前缀。
这不等于产品启动参数“无真实 HOME 路径”已通过；后续实现须由主控结合结果判定。
探针 PASS 也仅表示前三项事实成立，不能替代 `controller_start/hook/Stop` 产品验收，不能放行真实调用。

## 主控执行命令

先审上面的目录范围。此 worker 不请求升级、不执行下列真实凭据探针。

```sh
python3 workbench/tests/probe_t093_normal_login.py
```

必须使用实际可执行文件（不复制），输出路径必须是已存在目录中的新文件。
主控本轮的完整 --run 命令见 [PROBE-09.md](PROBE-09.md)。后续运行使用新的报告名，保留旧结果；不自行更换脱敏文件的授权路径。
脚本不打印捕获的 CLI/security 输出，不把凭据放到参数或环境中，不把隔离目录归档进 evidence 或 Git。
后台假上游及 CLI 子进程都通过 `start_new_session=True` 脱离调用者进程组。
脚本退出 0 表示探针范围 PASS；退出 2 为 INCOMPLETE 或 NO_GO。产品工作仍等待主控读回探针结果。

## 依据与本地检查边界

2026-10-17 读取的官方说明（可能随版本变化，本机行为以探针为准）：

- [Claude Code 认证](https://code.claude.com/docs/en/authentication)：macOS Keychain、凭据文件 fallback、`CLAUDE_CONFIG_DIR` 与 `ANTHROPIC_BASE_URL`。
- [CLI reference](https://code.claude.com/docs/en/cli-reference)：`auth status` 的 JSON、退出码、`configDirectory` 和 `authMethod`。
- [Environment variables](https://code.claude.com/docs/en/env-vars)：`CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`。环境变量仅减少额外流量，网络隔离由 OS 沙箱承担。

隔离测试需要验证的失败方式：扫描遗漏凭据；假上游写入 header/body；错误 bearer 被视为匹配；
清单漏掉变化或跟随链接；异常退出残留子进程或隔离凭据。只用合成 token 验证这些辅助逻辑，
不能据此宣布 macOS 沙箱、钥匙串或真实 CLI 边界通过。
