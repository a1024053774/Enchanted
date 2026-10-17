# T-093 工作区信任状态静态核对（2026-10-17）

状态：INCOMPLETE，字段与键格式已定位，实际跳过仍待 probe-10。
主控 #71 已确认 probe-09 停在工作区信任屏，默认 No, exit；脱敏文件读后删除，未出现邮箱或账号。
本轮采用裁定 (1)：生成私有 cwd 的项目状态，不实施裁定 (2) 的按键替代路径。
task T-093 / attempt a1 / ready_rev 1；起点 `850c955a783a880cd2cf3ceb3b31bf2f97957025`。

## 只读证据

仍只读已指定的 2.1.302 可执行文件，没有执行 CLI、读取真实 auth 或用户全局配置。
REA 工具未启用；未安装或修复，使用只读 mmap 记录内嵌代码。12 项摘录及字节偏移见 `workspace-trust-static-10.json`。

| 摘录 ID | 静态事实 | 对本次准备的含义 |
| --- | --- | --- |
| `trust_setter` | CLI 确认信任时，把 `projects[key].hasTrustDialogAccepted` 写成 true | 不需要复制 allowedTools、MCP、账号或其他项目默认字段 |
| `trust_getter`、`trust_exact_lookup` | 直接核对该字段，精确条目优先 | 只为本次 cwd 生成一个键 |
| `trust_key`、`canonical_repo_key`、`canonical_repo_root` | 项目键可取规范化仓库根；无仓库时使用 cwd 的绝对路径 | 探针 cwd 是新建空目录；不因仓库映射不符而改信任父目录 |
| `project_state_key`、`path_normalize_import`、`path_normalize`、`unicode_normalize` | 路径使用 resolve/normalize；字符串按 NFC 规范化，macOS 不改为 transcript 的短横线目录名 | 本次固定 `/private/tmp/.../cwd` 使用其规范绝对路径并做 NFC |
| `trust_parent_walk`、`trust_repo_boundary` | CLI 会在仓库边界内向父目录查找已有信任，部分仓库情形可能只接受仓库根 | 不写任何父目录信任；若当前项不生效，保持失败回主控 |

CLI 的目录信任可由该 cwd 树内的子目录继承，因此不把它描述为逐字符串精确授权。
本次只生成一个隔离工作区项目项，不给父目录、兄弟目录、真实项目或其他 cwd 写信任条目。
不生成通配符、全局信任或 sandboxed 环境开关，不复制真实 `.claude.json`。
这些是版本绑定的内部状态语义，不宣称官方公开稳定设置接口。

## 生成内容及拒绝条件

原有完成字段保留，只在同一个新文件中加入：

```json
{
  "hasCompletedOnboarding": true,
  "projects": {
    "<本次隔离根>/cwd": {"hasTrustDialogAccepted": true}
  }
}
```

键由本次随机隔离根生成，不接受外部 cwd 参数；目录必须已存在、不是链接，且解析后仍为该路径。
任何条件不符、文件已存在或祖先为链接都停止，不合并旧内容、不改信任对象。
文件仍为 0600，在首次 CLI/凭据读取之前准备，最后随整个隔离 HOME 删除。

启用 `--trust-isolated-cwd` 还会关闭主题、说明和信任屏的所有业务按键。
保留现有终端协议查询回复；它们没有 Enter，也不选择菜单。没有“状态失败后改按 Yes”的 fallback。
独立 Python PTY 夹具读取实际输入字节，只允许其请求的协议回复，任何额外字符（含方向键）均让检查失败。

主控指出 probe-09 的三处 `.claude/skills/synced/815211c2-…` 差异来自其他会话同步。
按主控转述记录，不补称为独立写入归属证据；原报告保留，清单比较及有差异时的 INCOMPLETE 逻辑不改。

## 复查

```sh
python3 evidence/2026-10-16-batch16/T-093/inspect-workspace-trust-10.py --output evidence/2026-10-16-batch16/T-093/workspace-trust-static-10-new.json
```

只读指定文件，摘要必须新建。实际探针命令见 [PROBE-10.md](PROBE-10.md)。
若状态未被采用或出现其他屏幕，仍不发业务按键，不扩大信任，交回主控。
