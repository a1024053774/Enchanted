# T-093 首次启动连通性检查：静态发现（2026-10-17）

状态：INCOMPLETE。找到主控 #69 允许的最小状态候选，可以交 probe-08 验证；尚未证明实际跳过或本地认证请求通过。
task T-093 / attempt a1 / ready_rev 1；代码起点 `e5da995988d49409ed8931013197475cb0d8af3e`。
只读指定的 2.1.302 可执行文件及官方文档，没有执行 CLI、读取真实 auth 或读取用户 `.claude.json`。
REA MCP/CLI 不可用，未安装或修复；使用只读 mmap 查看内嵌 JavaScript，未执行或 eval 该代码。

## 已观察与静态推断

主控 #69 转述 probe-07：欢迎页后报 Anthropic services / api.anthropic.com 的 ENOTFOUND，然后退出 1。
脱敏文件由主控确认 831 字节、0600、凭据扫描 0，读后已删除；这些是主控读回，worker 未读取正文。
本文不把 JSONL 为零当作输入一定未提交的证明，也不从未匹配拒绝词推断 fork 的实际 syscall 结果。
本轮按裁定继续禁止 fork。

本机文件为 Mach-O，267956720 字节，静态摘录保存在 `onboarding-static-08.json`。
下面偏移均指该文件字节位置，不是源码行号；不是对其他 CLI 版本的承诺。

| 证据 ID / 偏移 | 静态事实 | 结论范围 |
| --- | --- | --- |
| `onboarding_gate` / 237981965 | 启动步骤从 `ue()` 读状态；完成字段为真且未被内部强制 onboarding 模式覆盖时，直接返回 null，不加载 Onboarding | 可以用状态跳过这一组件；不设置内部模式变量 |
| `onboarding_factors` / 252000055；`onboarding_preflight_step` / 252001729 | 组件内仅在 `o && !h` 时加入 preflight；`o` 由 OAuth/gateway 条件计算，`h` 含 gateway/其他认证来源判断 | 预检并非每个 CLI 命令、每种认证都执行；本次全新隔离订阅登录进入了它 |
| `preflight_urls` / 251996228；`preflight_parallel` / 251996947 | 从 OAuth 配置 `ln()` 得到两个 hello URL，`Promise.all(t.map(v))` 并发 fetch；未指定 method，显式 headers 只有 User-Agent，并带运输选项展开 | 是一次预检流程里的两个请求候选，不可说固定一次外联；未穷尽全局 fetch/运输选项影响，不能仅凭片段担保所有隐式头 |
| `production_api` / 212195796；`production_oauth` / 212196007 | 生产配置对应 api.anthropic.com 和 platform.claude.com | 本分支候选地址是 `https://api.anthropic.com/api/hello` 与 `https://platform.claude.com/v1/oauth/hello` |
| `oauth_resolver` / 212198055 | 使用 OAuth 专用配置；该解析器未读取 ANTHROPIC_BASE_URL | 与主控观察相符；不能推广为模型请求也忽略 BASE_URL |
| `state_file_path` / 212291720；`state_suffix` / 212194869 | 无定制 OAuth 环境时，生产状态名为 `.claude.json`，目录优先 CLAUDE_CONFIG_DIR，否则 HOME | 本探针需要新建 `home/.claude/.claude.json`，不是 `home/.claude.json` |
| `legacy_state_choice` / 212291483 | 存在可用旧 `.config.json` 时可能选择旧文件 | 本次全新私有目录没有该文件，不复制或制造旧文件 |
| `state_merge` / 214978325；`default_theme` / 214968970 | 已解析状态覆盖默认值；默认主题为 dark | 只需一个完成字段，不需另设 theme |

`hasCompletedOnboarding` 是本版实际读写的内部状态字段，不是官方公开稳定设置接口。
主控本轮明确允许研究并新建这种最小状态；该授权不扩展为使用未公开环境开关、改认证或预置信任。
真实开关行为、是否被其他启动来源覆盖、跳过后是否另有阻断，仍由 probe-08 核对。

## 官方文档核对

- 官方说明配置目录可由 CLAUDE_CONFIG_DIR 指定；另有 CLI 自行维护的 `.claude.json` 状态文件。
  文档未把本次完成字段列作公开设置，不能把本方案称为官方支持的稳定配置 API。
  [配置文件说明](https://code.claude.com/docs/en/settings)、[目录说明](https://code.claude.com/docs/en/claude-directory)。
- 官方网络页明确提到 first-run setup 检查两个官方主机；API 网关地址覆盖不等于所有辅助网络都跟随。
  [网络配置](https://code.claude.com/docs/en/network-config)。
- 已核对官方环境变量表：BASE_URL 是 API 端点覆盖；已有 NONESSENTIAL_TRAFFIC 主要关闭非必要流量。
  fast-mode 的两个 skip 变量只用于其可用性检查，不用来替代 onboarding；没有在所查公开表、网络页、网关页及本版该组件的内嵌说明中找到受支持的 onboarding 预检关闭/改地址变量。
  这是限定范围的未找到，不是全站或所有版本不存在的证明。
  [环境变量表](https://code.claude.com/docs/en/env-vars)、[网关说明](https://code.claude.com/docs/en/llm-gateway)。

本版 OAuth 解析器存在别的内部定制变量，部分还有受限域名检查；没有找到公开支持此用途的说明，不使用它们。
不改成 API key、gateway 登录或云提供商认证，不允许官方外连，也不添加 HTTP/DNS 重定向。

## 复查命令与下一步

以下只读取指定可执行文件并生成新的静态摘要，不会执行它；旧摘要存在时拒绝覆盖：
首次通用 state_merge 匹配命中三处，检查按预期拒绝且未生成摘要；随后限定到实际合并表达式，再保存当前 13 项摘录。没有覆盖旧结果。

```sh
python3 evidence/2026-10-16-batch16/T-093/inspect-onboarding-08.py --output evidence/2026-10-16-batch16/T-093/onboarding-static-08-new.json
```

probe-08 仅在任何 CLI/凭据读取之前，于本次私有配置目录新建一个 0600 状态文件，正文只有：

```json
{"hasCompletedOnboarding":true}
```

不读取、合并或复制真实 `.claude.json`；不设置 lastOnboardingVersion、theme、oauthAccount、项目/信任、权限或 hooks 字段。
沿用现有假上游、原始请求逐条记录和原 bearer 对照；不新增环境变量，不放宽任何 profile。
只有携带复制凭据的本地 `POST /v1/messages` 才能通过路由事实检查；状态字段本身不算路由证据。
若仍出现首次启动预检或其他阻断，保持 INCOMPLETE 回主控，不追加字段或改官方地址许可。
完整命令与执行边界见 `PROBE-08.md`。
