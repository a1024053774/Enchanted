# T-093 probe-06：保留权限，补全退出分类（2026-10-17）

状态：INCOMPLETE。尚未确认 fork 被拒，CLI profile 不作放宽；只补终端分类。
task T-093 / attempt a1 / ready_rev 1 / session `67f986cc-92e4-4089-9c22-802a1143b645`。
代码起点 `151d96bf8bd6099cd06af0f36d5d5d2e8a8b0bbc`；未提供新 fence。

## 已知事实和本轮判断

- **observed（probe-05）**：交互 CLI 自己退出 1，终端 1583 字节、49 行、有 ANSI；
  `mentions_spawn=false`、`mentions_permission_error=false`、`tail_marker_classes=[]`，
  `mentions_official_api_host=true`。没有原生 user 记录，读取范围不完整，不能据此证明未提交。
- **observed（本轮只读检查）**：指定 probe-05 日志只有 110 字节、6 行摘要，没有 ANSI、fork、spawn 或权限错误标记。
  原终端正文只在 probe-05 进程内存中，隔离目录已删除，无法从该日志重新取得它。
- **observed（主控 #67）**：只读残留核对返回 `[]`。这说明该次快照没有匹配夹具，不补称历史中断时没有残留。
- **inferred**：fork 被禁只是待验证解释；官方主机文字也不能单独证明发生了官方外连，或 CLI 忽略 BASE_URL。
- **unknown**：本次原生退出的具体原因。现有摘要未提供 fork/exec 拒绝证据，也未定位到另一确定原因。

因此本轮不启用主控 #67 的条件放宽。精确凭据读取、假上游和 CLI 的 profile 均保持；
不加 process-fork/process-exec 例外，不调整真实 HOME、网络、Security Mach 或进程组限制。
原 CLI profile 的 `allow default` 本已涵盖未被单独拒绝的 exec；本轮没有修改该事实。
真实 HOME 清单继续照实比较，不做 fs_usage、root 或归属采集。

## 新增的固定分类

`route_diagnostic.terminal` 新增：

- `process_denial_operations`：固定值 `fork`、`exec`、`spawn` 的列表。
  去 ANSI 并折叠空白后，操作词与 EPERM/EACCES/denied 等拒绝词相距不超过 160 字符才匹配。
  支持 vfork、execve、posix_spawn、spawnSync 等形式；不保存命令、路径、错误正文或前缀。
- `official_host_connectivity_failure`：failed/unable to connect 后紧接的完整目标主机，
  或“主机名: failed/unable to connect”中的主机，是否精确为 `api.anthropic.com`。
  支持 URL、端口及主机尾点；只出现主机名、本地失败旁边的官方文档链接、带其他域名后缀或 URL 用户信息均不算。
- 对应的固定类别加入 `tail_marker_classes`；连接失败词补充 `failed to connect`。

这些都是终端文字信号，不能替代 syscall、实际连接或沙箱归属证据。
尤其是 spawn 拒绝不能直接等同于 fork 拒绝；exec 也可能因目标文件不可读而失败。
脚本不根据分类自动放宽、不跳过联网前检、不切换认证、不改变 BASE_URL。
若输出定位到其他原因或需要额外权限，停止并交回主控；不继续试放宽。
若后续明确确认 fork 被拒，再按主控裁定单独修改 CLI profile，并在任何凭据复制前验证子进程继承限制。
本轮未启用 fork，因此没有把“子进程同样不可写真实 HOME/不可连其他端口”写成已验证。

## 主控执行

在 worktree 根目录运行，保留 probe-01～05：

```sh
python3 workbench/tests/probe_t093_normal_login.py --run --claude /Users/luckye/.local/share/claude/versions/2.1.302 --output evidence/2026-10-16-batch16/T-093/probe-06.json
```

仍不转发真实接口；本地假上游固定返回 400。凭据只在隔离 HOME 与进程内存中；
所有输出落盘前扫描，原始终端正文不落盘，最后删除整个隔离目录。
若新分类仍为空，结论继续为 INCOMPLETE，不把“没有匹配词”推断为某种已排除的原因。

## 本地证据

`terminal-classification-red-06.json` 保存旧候选缺少分类的合同红态。
`probe-helper-checks-11.json` 是首次辅助绿态；独立审查随后发现目标绑定和主机名前置的缺口，
原 FAIL 见 `PROBE-06-REVIEW.md`，反例红态见 `terminal-target-red-06.json`。
修正后 13 项辅助检查及 19 个被断言拒绝的变异见 `probe-helper-checks-12.json`，包含恢复旧错误匹配方式的变异。
这些辅助检查不运行真实 CLI、不读取真实凭据，也不证明 probe-06 的实际退出原因；修正后未再做独立审查。
