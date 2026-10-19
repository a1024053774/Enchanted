# T-093 probe-10：只信任本次隔离工作区（2026-10-17）

状态：INCOMPLETE，等待真实 probe-10。按主控 #71 的首选方案准备，静态依据见 [WORKSPACE-TRUST-STATIC-10.md](WORKSPACE-TRUST-STATIC-10.md)。
task T-093 / attempt a1 / ready_rev 1 / session `67f986cc-92e4-4089-9c22-802a1143b645`。
代码起点 `850c955a783a880cd2cf3ceb3b31bf2f97957025`；未提供新 fence。未改产品代码。

`--trust-isolated-cwd` 必须与 `--prepare-onboarding-state` 同用。
首次 CLI/auth 前，隔离配置的新 `.claude.json` 只有完成字段和 `projects[本次规范 cwd].hasTrustDialogAccepted=true`。
不读取或合并真实配置，不写父目录、兄弟目录、其他项目或通配符条目；链接、已有文件或无效 cwd 即停。
CLI 对 cwd 内子目录有目录信任继承；范围仍是本次隔离工作区，不是 cwd 外的其他路径。

此模式禁用全部业务启动按键，报告 `route_diagnostic.startup_controls_enabled=false`，`startup_controls=[]`。
终端协议回复保留。不增加新按键，也不在状态方案不通时自动转去选择 Yes。
fork、exec、Security Mach、真实 HOME、网络规则、认证来源、脱敏和请求记录逻辑不变。

在 worktree 根目录运行，保留 probe-01～09：

```sh
python3 workbench/tests/probe_t093_normal_login.py --run --prepare-onboarding-state --trust-isolated-cwd --claude /Users/luckye/.local/share/claude/versions/2.1.302 --output evidence/2026-10-16-batch16/T-093/probe-10.json
```

不带 terminal-output，不新建终端文本文件。报告 `onboarding_state.trusted_cwd` 给出唯一生成的项目键；这只证明准备，不等于 CLI 已采用。
仍须登录识别及携带最初复制 bearer 的本地 `POST /v1/messages` 才有正向路由证据；假上游固定 400，不转发真实接口。
任何新屏幕或阻断均保留 INCOMPLETE，不补状态或改权限。真实 HOME 差异照实记录，不实施归属采集、不自动忽略。
整个隔离 HOME 和凭据副本最后删除，不跑真实模型回合，不申请升级。

## 合成证据

`workspace-trust-red-10.json` 保存新准备功能和无按键模式缺失的合同红态。
初次复验见 `probe-helper-checks-20.json`；加强到核对全部非协议输入字节后的最终复验见 `probe-helper-checks-21.json`。
检查包含：只生成当前 cwd 键、false/父目录/链接反例、显式选项与准备顺序、已有文件与 0600、
真实合成 PTY 的协议回复及零业务输入，并注入方向键验证能被观察者抓住。
不运行真实 CLI、不读真实 auth；合成检查不替代主控运行结果。
独立审查未发现可达合同违例；因真实边界尚未运行，结论为 INCOMPLETE，见 [PROBE-10-REVIEW.md](PROBE-10-REVIEW.md)。
