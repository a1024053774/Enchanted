# T-093 probe-05 冻结候选审查（2026-10-17）

以下为独立只读审查 `/root/route_probe_review` 返回的结论。候选 T093-route-v6，
基于 `b01524e5c1a878ef488e37e04f8cf1f0b943bc26` 的未提交变更；审查期间未改候选。
审查员使用 gpt-6.1-sol / xhigh、新上下文，未读取 worker 对话。

```text
STATUS: INCOMPLETE
TARGET: T093-route-v6，基于 b01524e5c1a878ef488e37e04f8cf1f0b943bc26 的冻结候选。
EVIDENCE:
- test_t093_probe_safety.py：12 项通过；解析器 --self-test 通过，未调用 ps。
- 独立合成检查：协议按 1/2/3/39 字节分块均得到预期回复；未知查询无回复；改变 prompt 后匹配记录由 1 变 0。
- 终端摘要仅保存固定类别、计数和布尔值；原权限及启动按键白名单未扩展。
- project_map.py status：0 problems、0 stale living docs。
FINDINGS:
- [P2] workbench/tests/probe_t093_normal_login.py:522 — 已退出子进程的输出仍触发协议回复与启动按键。
  合成 peer 输出查询及主题标记后退出 17，且在 Popen 返回前已 wait；候选仍写入 ESC[1;1R 和 1\r。
  这违反 PROBE-05“退出后只排空、不再发键”的说明。写入前核对退出状态，已退出时仅捕获输出。
COUNTEREXAMPLE:
- 上述已退出且含可应答标记的 peer 暴露当前缺口，既有 12 项检查未拒绝它。
- 保存的变异证据拒绝了不回复协议、保存终端原文、跟随祖先链接及恒空 HOME 引用等实现。
LIMITATIONS:
- 真实 probe-05、零 HTTP 的原因、自定义地址路由及中断前残留进程均未证明。
- 未执行 ps、真实 Claude/security、真实凭据读取、沙箱应用、归属采集或权限升级；仅清理自有合成子进程。
RULE:
- 在 test_t093_probe_safety.py 加入“已退出 peer 输出协议查询及主题标记”的场景，
  断言退出后 PTY 写入为零，并纳入 helper checker 基线。
```

worker 后续处理：补充协议查询及主题标记到快速退出夹具，并从父进程观察实际 PTY 写入。
`route-exited-red-05.json` 保存修正前两次写入导致的断言失败；随后在输入处理前核对已退出状态。
`probe-helper-checks-10.json` 的基线通过，并拒绝跳过该核对的单点变异。
这是 worker 的修正与复验，不改写上述审查结论，不声称修正后已取得新的独立验收。
