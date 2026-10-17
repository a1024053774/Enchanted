# T-093 产品本地检查 01

结论 INCOMPLETE：局部检查通过，尚待主控在沙箱外运行无模型全链；未 submit，未声明可集成。
真实模型回合、真实上游请求、供应商 CLI 启动、真实认证读取均为 0。

实现增加正常登录分支、私有 auth 读取与隔离配置、先记录后转发的 HTTP 层、只读事实命令。
controller_start、三个 hook 和 Stop 转交仍用既有入口；未修改 gates、acceptance、地图或全局配置。
隔离目录随 CLI 退出清理；剩余进程组必须先确认消失，无法确认时保留私有现场并记录失败。

局部证据与复现命令（输出需选新路径）：

- 构造红态 profile-red-01：在 main 617863704 的实际构造函数上，正常登录合同失败；假 API 仍拒绝真实地址。profile-green-01 为相同合同通过，4 项。
  `node workbench/tests/test_t093_launch_profile.ts /private/tmp/新构造报告.json`
- forwarder-green-02：6 项；独立假上游在收到请求时读回先前 fsync 的请求行；400 和重试 200 共两次，凭据与正文不入原始记录；HOME 引用、凭据变体、漏记反例均有效。
  `node workbench/tests/test_t093_forwarder.ts /private/tmp/新转发报告.json`
- private-files-green-01：5 项；只返回登录对象、清单不含正文、拒绝凭据或祖先符号链接、拒绝过期登录。不读真实认证。
  `python3 workbench/tests/test_t093_private_files.py /private/tmp/新文件报告.json`
- counterfactuals-03：未改对照与 7 个错误候选均按预期区分，包括修复前 OSC/DCS 泄漏候选。首次 counterfactuals-01 的测试解析缺陷仍保留，不上调。
  `python3 workbench/tests/test_t093_counterfactuals.py /private/tmp/新反事实报告.json`
- paste-fixture-01：实际 C 夹具在修复前把一个多行 paste 拆成两次；修复后只交付一次完整正文。测试子进程脱离调用者进程组，不用 ps。
  `python3 workbench/tests/test_t093_paste_fixture.py /private/tmp/新粘贴报告.json`
- fixture-version-regression-01：现有 T-091 测试 8 项通过，原缺陷及移除版本检查的变异均被拒绝；不运行 CLI/PTY/模型。
  `node --experimental-vm-modules workbench/tests/test_t091_claude_version.mjs /private/tmp/新版本报告.json`

只读审查 PRODUCT-REVIEW-01 为 FAIL，绑定旧候选 ff625c371。其 OSC/DCS 泄漏已修复，新增对原始公开字节、所有分片位置和 CSI 的检查；旧候选仍被新测试拒绝。新候选还须在全链结果之后完成独立审查，不能用自测覆盖旧审查结论。

沙箱外命令为 `python3 workbench/tests/run_t093_login_chain.py --output evidence/2026-10-16-batch16/T-093/product-chain-02.json`。
它只运行合成登录与编译的假 CLI；真实 daemon、PTY、进程身份、子进程 sandbox、hook 和 Stop 均不替换。
检查子进程读写源 HOME 与连接其他端口被阻断，再以独立收件箱哨兵核对 Stop 转交与反馈。
此项尚未运行，不写 PASS。脚本结果不能替代供应商真实行为，后者仅有 probe-10 的指定版本事实。

probe-10 的 PASS 来源为主控 #72：两个本地 POST /v1/messages、携带复制的 bearer、假上游 400、真实上游 0、扫描 0、清单无差异、隔离根已删除。
该事实依赖 2.1.302 内部 onboarding 与项目信任状态；升级重新核对。
onboarding 的两个官方 hello 候选绕过 BASE_URL，正式 profile 阻断直接外连，事实报告单列可见预检迹象；未观察到迹象不能证明没有网络尝试。
真实 HOME 清单的所有差异保留，不做归属采集、不以其他会话为由自动忽略。该验收裁定仍由主控处理。

当前 project_map.py status：0 problems、0 stale living docs；最终交付前仍须重跑并保存新证据。
