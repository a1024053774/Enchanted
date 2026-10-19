# 主控 #121：合并依赖与已准备的修正

状态 INCOMPLETE，未提交或冻结新候选。主工作区 HEAD 仍为 630291ca7a07086d231e38a15fe1f1c9e6411bf0，受控文件未改；本轮新增脚本、局部检查和摘要均尚未提交。
independent-review-02.md、REVIEW-OUTSIDE-03.sh 原文与开始时副本逐字节一致，没有修改。

## 必须由主控执行的合并

worker 的 `git merge --no-commit --no-ff 0e92f78ec6824265cdfcbb9387ba4b454d7eee7f` 在创建共享 Git 目录的 ORIG_HEAD.lock 时以 Operation not permitted 退出 128，未建立 MERGE_HEAD，未开始合并。
依任务约束不申请升级，脚本 [MERGE-MAIN-16.sh](MERGE-MAIN-16.sh) 交主控沙箱外执行。它校验分支／原 HEAD／受控文件清洁，只合并、不提交、不 push、不 rebase，保留全部冲突。
当前 main 比指定 fd5c93e6e 多一项 0e92f78ec 的 T-095 验收措辞变更；脚本固定当前 main 的完整 SHA。收到退出码／冲突列表后，worker 才解决冲突并写入下面的产品修正。

## REALITY GATE: INCOMPLETE

GOAL / NON-GOALS：落实新的 F 端口＋应用主机锁定，合入 T-096 并保持旧记录／argv／版本／session 合同。不运行真实模型、真实 auth、真实上游或 worker 内的真实 CLI／OS profile；不改门禁。
DECISION：按主控修订，F 的 OS 规则不再按主机限制，只准 TCP 443；应用在连接边界锁定配置主机，忽略入站 Host，不跟随重定向。C 仍只能连 F。
OBSERVED：profile-compile-review02-red.json 保留非 loopback 编译失败；主工作区合并被文件沙箱拒绝；两份 reviewer 原文未改。
MEASURED：forwarder-host-red-01 在旧实际 HTTP handler 的非配置目标故障注入下命中 non_configured_host_must_not_connect；另外三个配置目标／入站 Host／不重定向对照通过。forwarder-port-red-01 拒绝旧 OS 规则及非 443 配置未在 auth/OS 前拒绝。
INFERRED：F 改用 remote tcp4 "*:443"，prepare 提前拒绝非 443，转发器捕获配置 hostname 并在实际 transport 前和 lookup 边界核对，可满足新合同；不增加 DNS/fallback。
UNKNOWN：新 profile 本机编译、443 上的独占本地假 U、同 profile OS 拒连与合并后的 T-096 原生恢复尚未执行。
PROBE：主控在冻结后用 compile-profiles-16.py 编译 loopback／203.0.113.31 两个实际 F profile；不发网络、不读 auth。随后完整假链改用本地 443，原 F 的另一个本地端口负例改称 non_443_port，必须仍 EPERM。若 443 被占或权限不够，保留 INCOMPLETE，不能换端口或申请 root。应用非配置主机负例使用 supplied transport，绝不对假主机联网。
DECISION CONSEQUENCE：OS 不再提供按主机隔离，须在报告明确披露；应用主机锁定和 pinned IPv4/TLS 仍为产品保证，C 权限不变。
NEXT ACTION / OWNER：主控先执行合并脚本；worker 解决冲突、修正式代码／测试；主控随后在沙箱外运行冻结候选的 OS 与 T-096 入口。

## 已完成的独立准备

两个新局部检查位于 workbench/tests/test_t093_forwarder_host.ts 和 test_t093_forwarder_port_policy.py，均不使用真实网络／进程／认证。旧源码的业务红态已保存。
临时源码修正副本位于 /private/tmp/t093-network-proposal-16/，主工作区产品未改。proposal-green 两份只证明这些临时副本的 L1 逻辑，不是当前候选已修复或 OS 边界已通过的证据。
拟修正为：配置 hostname 单独捕获；target hostname 漂移先记录 upstream_host_mismatch 并拒绝 transport；lookup 再核对 hostname、只用 pinned IPv4；OS F 为 *:443，prepare 非 443 提前拒绝。
合并后应在实际产品上重跑相同信号，并删除主机 guard 的单处变异，确认负例仍命中业务断言。

T-096 恢复拟在原版本与 native session 核对后、PTY spawn 前取得 realpathSync(argv[0])。原记录有 executable_path 时必须一致；合法旧记录缺字段时只给运行时 record 副本补齐。不可写回历史记录，不改完整 argv，不固定 leader，不绕过版本／session。既有测试只更新 subprocess JSON 与 virtual realpath IO 边界，保留旧记录正例及原变异。
[T096-REGRESSION-16.sh](T096-REGRESSION-16.sh) 已提供 tracer、three、missing-argv、version-mismatch、missing-session、isolation、empty-reopen 七种入口；固定 2.1.302，初始化仍由主控逐屏批准，脚本不自动按键或设置内部状态。
该 wrapper 沿用原 T-096 runner，外置盘原件位于 T-093 新标签目录；小型 run/archive 摘要由原 runner 写 T-096 目录的新标签，不覆盖旧记录。脚本仅做语法检查，未运行。
