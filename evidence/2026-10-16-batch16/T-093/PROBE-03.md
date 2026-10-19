# T-093 probe-03 状态输出安全诊断（2026-10-17）

状态：INCOMPLETE。诊断脚本已修正；实际非 JSON 原因仍未知，未宣称已经恢复自定义地址能力。
task T-093 / attempt a1 / ready_rev 1 / session `67f986cc-92e4-4089-9c22-802a1143b645`。
起点 `447ab5780161862e1752bbfe0ff360386061910d`。本轮未取得新 fence 值，不补造。

目标：区分设置 BASE_URL 后的 CLI/沙箱启动错误、输出前缀与 JSON 状态失败，同时不保存可能含邮箱或凭据的原文。
非目标：放宽任何权限，接受非 JSON 状态，切换认证来源，产品实现或真实模型回合。
验收：所有状态查询无论成功失败均留下安全结构摘要；仍严格要求 JSON 对象、退出 0、原有三项登录事实。

## 已知事实与未知

- **measured（主控 #61）**：probe-02 rc 2，`auth_status_not_json`。精确查询与读取密码 exit 0。
- **measured（probe-02.json）**：无 BASE_URL 时，隔离 HOME 的状态 exit 0、loggedIn true、使用 claude.ai、配置目录为隔离目录。
  凭据复制后能被识别的事实已成立，绑定该次候选与证据；后续失败不将这项事实抹掉。
- **measured**：probe-02 真实上游请求 0、本地请求 0、凭据扫描命中 0、清单无差异、隔离目录已删除。
- **observed**：旧 auth_status 在解析 JSON 前未保存退出码和结构，原始 stdout/stderr 按隐私要求只在内存，退出后没有保留。
  因此无法从旧报告追溯是警告、文本、空输出还是报错，也不能据此认定自定义地址不支持订阅登录。
- **observed**：设置 BASE_URL 时同时启用带端口的沙箱 profile。原报告没有在该 profile 下独立验证 CLI 启动。
- **unknown**：本机该次实际失败原因、自定义地址下的登录识别、本地携带原始订阅 bearer 的请求是否可达。

## 静态证据

REA 工具和 CLI 均未连接/安装。本轮遵循 reverse-engineer-anything 的只读取证边界，使用普通 Python mmap/find，
只读 `/Users/luckye/.local/share/claude/versions/2.1.302` 的内嵌 JavaScript；未执行该 CLI，未读真实 auth。
以下为普通工具的静态观察，不是 REA Evidence，也不是运行输出：

- 字节位置 231395941 附近注册 `auth status`，帮助标明 `--json` 默认、`--text` 为人类可读格式。
- 字节位置 239305385 附近的状态处理分支，仅在 text 选项下选择文本；否则构造 JSON，包括可能存在的邮箱与组织资料。
- 字节位置 239168285 附近创建子命令根，说明状态渲染前还有初始化路径；静态片段不能证明本机是在这里失败。

没有发现足以判定“自定义地址必然不支持订阅登录”的运行证据。不从上述片段推断真正 stdout，
也不把显式添加 `--json` 当作已被证明的根因修复：静态注册表显示其本来就是默认值。

## 本次变更

1. 帮助必须确认 `--json` 存在，所有状态查询显式使用它；不请求文本格式。
2. 在解析前保存 `<查询名>_output`。只包含退出码、stdout/stderr 字节数、行数、JSON 起始/可解析性、
   JSON 是否存在于前缀之后、ANSI 是否存在，以及固定类别/关键字出现布尔值。
   前缀类别只可能是 `empty/text/json_object/json_array/warning/error/usage/ansi_escape/sandbox_exec`；
   不返回原始前缀、JSON 字段名、邮箱、错误正文或凭据。关键词只记录是否出现 OAuth、subscription、base URL、
   unsupported/not supported、权限错误，不保存匹配内容，不据此自动判定不支持订阅登录。
3. 不接受警告后的 JSON 作为成功，不剥离任意前缀，不合并 stdout/stderr。数组、非 JSON、非零退出或登录字段不符均停止。
4. 在新端口 profile 下先执行同一 CLI 的 `--version`，报告 `bound_profile_probe` 的安全结构与版本是否匹配。
   失败标为 `bound_profile_cli_version_failed`，不把 launcher/profile 错误误判为订阅认证结论。
5. 真实 HOME、精确钥匙串查询、配置与网络/fork/Mach 限制、原始输出内存扫描、完整隔离目录清理均不变。

## 主控在沙箱外运行

```sh
python3 workbench/tests/probe_t093_normal_login.py --run --claude /Users/luckye/.local/share/claude/versions/2.1.302 --output evidence/2026-10-16-batch16/T-093/probe-03.json
```

只创建新文件，不覆盖 probe-01、probe-02。主控读回重点：

- `bound_profile_probe`：启动是否成功；stderr 是否为 sandbox_exec 前缀、是否出现权限错误关键词。
- `status_with_base_url_output`：退出码、stdout/stderr 行数、JSON/前缀/ANSI 结构。
- `status_with_base_url`：仅在 stdout 为 JSON 对象时才有，继续检查 exit 0 和三项登录事实。

如本次仍失败，保留新结构证据后停止，不改认证方式、不断言底层已修复。若后续证据确认 CLI 在自定义地址下不支持订阅登录，
按任务卡停下报主控，不绕过限制。首轮前缀/关键词只能提供结构事实，不能替代完整语义判断。

## 合成检查

独立输入覆盖干净 JSON、警告+JSON、含合成邮箱/token 的错误、sandbox-exec 启动失败、JSON 数组和非零退出。
检查结构准确、诊断不含原文、仍停止在无效状态，且全部查询显式带 --json。
修正前红态见 `auth-output-red-01.json`；其中五项为诊断缺失的有效断言失败，另一个数组 TypeError 不冒充有效红态。
完整辅助套件与新增“泄漏原文/接受警告后 JSON/忽略退出码”单点反例见 `probe-helper-checks-06.json`。
所有本地验证只用合成数据，不运行真实 CLI/Keychain；真正原因仍待主控的新真实入口证据。
