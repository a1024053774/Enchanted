# T-093 probe-07：仅导出脱敏终端（2026-10-17）

状态：INCOMPLETE，退出原因尚未知。主控 #68 授权将脱敏终端写到指定临时文件，由主控读后删除。
task T-093 / attempt a1 / ready_rev 1 / session `67f986cc-92e4-4089-9c22-802a1143b645`。
代码起点 `c7cf6e434fbe1b4784d38156c0cc8e4014ebd69f`；未提供新 fence。
本 worker 不运行真实探针，不生成或读取该真实临时文件。

probe-06 仍退出 1、本地请求 0，新分类为空。没有匹配输入记录，读取范围不完整，不据此认定根因。
fork、exec、Security Mach、真实 HOME 和网络限制全部保持。不做归属采集、不申请升级、不跑真实模型回合。

## 脱敏和写盘

父探针排空交互 PTY 后处理内存正文，原文不经过中间文件。只允许主控指定的完整路径：

```text
/private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/4cb6cda5-1e37-4e3e-8ff5-2755a799eb7c/scratchpad/t093-terminal-07.txt
```

- 读取凭据前检查精确路径和新文件要求；逐级 `O_NOFOLLOW` 打开祖先目录，不创建目录、不覆盖已有文件。
- 先去 ANSI CSI、OSC、控制字符串和单独转义，再去换行/tab 以外的控制字符；这也让颜色序列拆开的凭据重新连续。
  未知/不完整 ESC、C1 控制或无效 UTF-8 会停止导出，不写文件。
- 凭据原值及 JSON 转义、URL 编码、普通/URL-safe base64（含无填充）变体替换为 `<CREDENTIAL>`，长值先替换。
  URL 百分号十六进制在替换和全部凭据扫描前统一为大写，识别大小写混合形式；普通字符大小写不变。
- 邮箱替换为 `<EMAIL>`；组织或账号值替换为 `<ACCOUNT>`。
  身份值只取自已经读取的 auth status JSON 中 email/name、org/organization/account/user 的名字或标识字段、嵌套字段和以 name 结尾的字段。
  值及其编码变体仅在内存中用于替换，不加入报告或隔离 HOME；另匹配正文邮箱、账号/组织标签行和 welcome/signed-in/logged-in 欢迎语，支持 ASCII 管道、加号及 Unicode 盒线前缀。
  这是字段和值的机械替换，不能保证识别未提供且无标签的任意人名。
- 写盘前再次扫描全部已知凭据和身份值的变体；命中即停止，不创建文件。
  扫描成功后才以 `O_EXCL | O_NOFOLLOW` 创建；模式为 0600，首次写入前显式设置 0600。
- CLI 的写权限不扩大到 scratchpad；只有父探针执行这次导出。
  evidence 仅保存是否导出、字节数、权限及扫描计数，不保存脱敏正文或身份值。
  导出文件不进入 evidence、Git 或归档，也不跟随隔离 HOME 自动删除；主控读后删除。

失败时 `terminal_export.written=false` 或无导出字段，探针保持 INCOMPLETE。
`terminal_export_credential_scan_failed` / `terminal_export_identity_scan_failed` 表示写盘前拦截；报告自身扫描计数另行保留。

## 主控执行

在 worktree 根目录运行，保留 probe-01～06：

```sh
python3 workbench/tests/probe_t093_normal_login.py --run --claude /Users/luckye/.local/share/claude/versions/2.1.302 --output evidence/2026-10-16-batch16/T-093/probe-07.json --terminal-output /private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/4cb6cda5-1e37-4e3e-8ff5-2755a799eb7c/scratchpad/t093-terminal-07.txt
```

rc 2 仍可能是未收到本地请求；需看 `terminal_export.written` 判断是否导出。
不要把文件正文粘进 evidence 或终端日志；按主控裁定读后删除，只转述要点。
假上游仍固定返回 400、没有真实转发；隔离 HOME 和凭据副本最后整体删除，真实 HOME 清单差异照实保留。

## 合成检查

红态见 `terminal-export-red-07.json`；两次 macOS `/var` 夹具路径拒绝保留在 `terminal-export-rehearsal-07-01/02.json`，未放宽链接限制。
`probe-helper-checks-13.json` 保留 INCOMPLETE；规范化夹具路径后的最终结果为 `probe-helper-checks-14.json`。
首次绿态后的独立审查 FAIL 见 `PROBE-07-REVIEW.md`；新反例红态见 `terminal-export-review-red-07.json`。
`probe-helper-checks-15.json` 保留了无填充反例未改变输入的缺口，说明见 `terminal-export-rehearsal-07-03.json`。
`probe-helper-checks-16.json` 已通过混合百分号编码、无填充 base64 和边框身份的复验。
随后新增 ANSI 单字符/字符集及不完整控制字符串的合同红态见 `terminal-export-ansi-red-07.json`；修正后的最终复验见 `probe-helper-checks-17.json`。
另含凭据颜色分段、邮箱和账号、预写扫描、0600、已有文件、祖先链接、精确目的地及真实合成 PTY 导出。
修正后未再次独立审查；这些检查不证明真实 probe-07 的脱敏结果或退出原因。
