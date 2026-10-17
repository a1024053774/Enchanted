# T-093 probe-08：仅新建最小 onboarding 状态（2026-10-17）

状态：INCOMPLETE，实际跳过和本地认证请求待主控执行。静态依据见 [ONBOARDING-STATIC-08.md](ONBOARDING-STATIC-08.md)。
task T-093 / attempt a1 / ready_rev 1 / session `67f986cc-92e4-4089-9c22-802a1143b645`。
起点 `e5da995988d49409ed8931013197475cb0d8af3e`；未提供新 fence。未改产品代码。

## 唯一新增准备动作

使用显式 `--prepare-onboarding-state` 时，在创建本次隔离目录后、首次 CLI 和凭据读取之前，
新建 `<隔离 HOME>/.claude/.claude.json`，0600，正文只有：

```json
{"hasCompletedOnboarding":true}
```

这是当前 CLAUDE_CONFIG_DIR 内的全新文件，不是从真实 HOME 的 `.claude.json` 复制或合并。
不添加主题、版本、账号、信任、项目、权限、hooks 或其他字段；若文件已存在或祖先为链接，拒绝继续。
未传该参数时不准备该状态，保留先前全新 HOME 探针方式。
报告 `onboarding_state` 仅记录相对路径、键名、模式、生成来源和准备阶段；只表示准备事实，不等于 CLI 已采用。

这是本版内嵌代码支持、主控 #69 允许研究的状态候选，不是官方公开稳定设置 API。
没有找到所查官方资料明确支持的 onboarding 预检关闭/改地址环境变量；本轮不使用未公开变量。

## 主控执行命令

在 worktree 根目录运行，保留 probe-01～07：

```sh
python3 workbench/tests/probe_t093_normal_login.py --run --prepare-onboarding-state --claude /Users/luckye/.local/share/claude/versions/2.1.302 --output evidence/2026-10-16-batch16/T-093/probe-08.json
```

不带 terminal-output；不复用已删除的 probe-07 临时文件，也不新增终端正文落盘。
原 fork、exec、Security Mach、真实 HOME 读写和网络规则不变，仍只放行一个本地端口；不设置新环境变量。
只复制已限定的登录凭据；原始 CLI/auth 输出留在内存，证据只保存原有结构摘要和扫描次数。
停止所有子进程组、照实对比清单并删除整个隔离 HOME；不做归属采集、不申请升级、不放宽验收。

成功条件仍是登录被识别，且假上游收到携带最初复制 bearer 的 `POST /v1/messages`，body 含 messages。
假上游固定返回 400，不转发真实接口，不产生真实模型回合。
仅有完成字段、无欢迎页或零 JSONL 都不能替代这条正向请求证据；即使通过，也不证明整个产品或所有辅助请求均已验证。
若仍出现预检或另有阻断，保留 INCOMPLETE 回主控，不追加状态、认证来源、内部开关或外连许可。

## 本地检查

`onboarding-state-red-08.json` 保留准备功能缺失红态；合成复验与单点反例见 `probe-helper-checks-18.json`。
新检查独立读取生成 JSON，要求精确单字段、布尔 true、正确隔离路径、0600、不可覆盖/跟随祖先链接；
通过替身 capture 验证它在第一次 CLI/凭据步骤前准备，未传参数时没有该文件，异常后隔离目录仍删除。
没有执行真实 CLI、读取真实 auth 或读取真实全局配置；这些检查不替代主控 probe-08 的边界证据。
独立只读审查在准备范围内为 PASS，见 [PROBE-08-REVIEW.md](PROBE-08-REVIEW.md)；实际运行结论仍为 INCOMPLETE。
