# T-093 probe-05 交互启动诊断（2026-10-17）

状态：INCOMPLETE。probe-04 已证明带端口 profile 可运行同版本 CLI，且自定义地址下仍识别 claude.ai 登录；
未收到本地认证请求的真实原因尚未知，不推断订阅登录忽略 BASE_URL。
task T-093 / attempt a1 / ready_rev 1 / session `67f986cc-92e4-4089-9c22-802a1143b645`。
起点 `b01524e5c1a878ef488e37e04f8cf1f0b943bc26`；本轮未提供新 fence。

目标：区分交互进程早退、终端协议、已知/未知屏幕和输入记录，并保留只含结构事实的诊断。
非目标：改变权限、认证来源、模型配置或全局配置；模型真实请求；系统级写入/网络归属采集。

## probe-04 的 4 处真实 HOME 引用

| 字段 | 内容类别 | 作用 |
| --- | --- | --- |
| `launch.argv[2]` 第 7 行 | `(deny file-read* (subpath "<REAL_HOME>"))` | 拒绝真实 HOME 读取的规则 |
| `launch.argv[2]` 第 8 行 | 精确允许 `<REAL_HOME>/.local/share/claude/versions/2.1.302` | 只让 CLI 可执行文件可读，未允许整个目录 |
| `launch.argv[3]` | 同一 CLI 可执行文件路径 | 实际 sandbox-exec 后的被启动程序 |
| `launch.cli_argv[0]` | 同一可执行文件路径的重复记录 | CLI argv 视图，不是另一个启动或额外读取路径 |

这是序列化 launch 的 4 次文字出现，不是 4 个不同目录，也不表示 4 次文件访问。
该计数只覆盖交互 launch；准备阶段精确钥匙串读取另有明确来源记录，不把此计数宣传为所有准备进程的路径清单。
启动环境中的 HOME、CLAUDE_CONFIG_DIR、TMPDIR、ZDOTDIR 均为隔离路径，没有真实 HOME 前缀。
probe-05 新增 `real_home_path_references`，逐项给字段和行号，不保存新的路径正文。

## 已知诊断缺口与修正

- probe-04 的 `startup_controls=[]` 和零 HTTP 请求不能区分早退与等待；旧报告没有退出状态、终端结构或原生输入记录。
- 原循环在读取前检查退出状态，可能漏掉子进程最后的 PTY 输出。合成的真实 Python 子进程复现了此缺口。
  现在先读可用数据，保留 parent 的 slave fd 到排空结束；观察到退出或执行停止后，只读完剩余字节，不再发键。
  独立审查还发现读取输出后未检查已退出状态的缺口；`route-exited-red-05.json` 复现了两次不应发生的 PTY 写入。
  已在处理协议及按键前核对退出状态，同一合成进程场景修正后写入为零。
- 工作台 `workbench/src/panes.ts:terminalProtocol` 会回复终端能力查询，旧 Python 探针没有。
  现沿用同一组固定协议：光标位置、主/次设备属性、键盘协议和背景色。只回复识别的协议查询，不含 Enter，不作为业务提交。
- 已知主题/说明/隔离目录信任屏的按键白名单不变。不会因诊断匹配到“可能是某屏幕”就增加按键，更不会对未知屏幕发 Enter。
- 保留原来的 PTY `start_new_session` 启动方式。未采用强制控制终端的实验；失败记录见 `route-rehearsal-05-01.json`。

静态只读检查已安装 2.1.302：`manual` 被接收为 `default` 的别名；SDK 构造中存在传入 ANTHROPIC_BASE_URL 的分支。
这些片段没有观察本次执行路径，也不证明订阅请求一定走自定义地址，因此未据此改权限模式或认定路由能力通过。
没有运行真实 CLI 或读取真实凭据来做本地检查。

## probe-05 的诊断字段

1. `sink_tcp_preflight`：在原 profile 下只建立并关闭到实际假上游端口的 TCP 连接，不发 HTTP、不发凭据；
   验证可达性且不增加 HTTP 请求数。它不证明 CLI 采用了该地址。
2. `route_diagnostic`：进程是否启动、停止前/后退出码、是否由探针停止、是否超时、前台组观察值、PTY EOF 和协议回复计数。
   探针发送 SIGTERM 后的退出码与原生退出码分开，不能把主动停止当作 CLI 自己崩溃。
   协议回复及主题按键计数只表示 PTY 写入成功，不证明 CLI 消费或 prompt 提交。
3. `route_diagnostic.terminal`：只给字节/行数、固定类别、固定关键词/地址是否出现、prompt 是否回显、类似提示符的标志。
   末尾标记可能包含此前重绘内容；它不是完整终端渲染器，不能凭标记声称精确知道最后一个可见屏幕。
   原始屏幕和前缀、错误正文、邮箱、凭据始终只在内存，不写文件。
4. `query_via_argv`：固定查询通过位置参数交给 CLI。仅有 argv 或回显不证明提交成功。
5. `submission`：只在本次隔离 HOME 的 `projects/<project>/*.jsonl` 中，内存读取是否存在匹配本次 prompt 的原生 user 记录。
   路径逐级 `O_NOFOLLOW`，不跟随链接；最多 64 文件/8 MiB，记录解析、IO、半行和范围不完整的计数。
   不保存路径、记录正文、JSON 字段、邮箱或 token。找到记录只证明 CLI 记录了该输入，不证明模型调用。
   零记录、不同存储后端、格式不兼容或范围不完整均不能据此断定“没有提交”。

固定标志中有官方 API 主机、连接错误或权限错误，只能提供屏幕文字事实，不是网络尝试/连接归属证据。
不会从“有官方主机文字且本地零请求”直接得出忽略 BASE_URL。若后续取得“订阅 CLI 不走自定义地址”的确证，
按任务卡停止并交回用户决定 2，不切换认证、不加代理、不放宽外连或读取真实 HOME。

## 主控先做只读残留核对

```sh
python3 evidence/2026-10-16-batch16/T-093/check-route-processes.py
```

这是主控 #66 要求的沙箱外脚本，本 worker 不执行。只调用一次 ps，原进程参数只在内存筛选，
stdout 只输出本票 `t093-route-peer-* / interactive-peer`、`t093-route-exit-* / exit-peer` 的 PID、PGID 和状态。
ps 使用宽输出，避免夹具可执行路径被终端列宽截断；完整参数仍只在内存中筛选。
不按任意 Python/Claude 名称筛选，不匹配 `python -c` 或 grep 中提到的路径，不终止任何进程，不读取凭据。
退出 0 表示快照查询成功；`[]` 表示快照时未匹配，不补称中断当时无残留。非零退出且无输出表示未取得核对结果，不能当作空列表。
若有结果，请由主控核对后处置，不由本脚本自动清理。

本地只验证解析器，不调用 ps 的命令为：

```sh
python3 evidence/2026-10-16-batch16/T-093/check-route-processes.py --self-test
```

此前 /bin/ps 被当前沙箱拒绝，沙箱外请求被主控拒绝并中断，未取得残留事实；记录已保留，不重试升级。

## 主控执行 probe-05

```sh
python3 workbench/tests/probe_t093_normal_login.py --run --claude /Users/luckye/.local/share/claude/versions/2.1.302 --output evidence/2026-10-16-batch16/T-093/probe-05.json
```

只创建新报告。所有原沙箱限制、精确凭据复制、原始输出内存扫描和隔离目录整体删除均保持。
不做 fs_usage，不申请 root，不实施写入归属采集；清单差异照实保留，仍按原条件给出 INCOMPLETE，等构思主控裁定。

## 检查与边界

旧候选两项断言红态见 `route-red-05.json`；强制控制终端实验失败和 PTY 关闭顺序失败分别保留在 `route-rehearsal-05-01/02.json`。
最终检查使用独立 Python peer，通过真实 PTY 发送协议查询、等待主题按键、写入合成原生 user 记录并向本地假上游请求；
外部随机 prompt 改变记录，HTTP 接收是独立进程记录，全部不是 Claude 或真实认证。
另测快速退出仍读回输出、报告不泄漏原文、输入记录不越过祖先链接、真实 HOME 引用不漏报。
冻结候选的独立审查见 `PROBE-05-REVIEW.md`，结论保留为 INCOMPLETE；修正后的候选未再做独立审查。
最终 12 项辅助检查和 16 个被断言拒绝的单点变异见 `probe-helper-checks-10.json`；
其中包括已退出子进程不得再收按键的反例，不替代主控真实 probe-05 的边界证据。
