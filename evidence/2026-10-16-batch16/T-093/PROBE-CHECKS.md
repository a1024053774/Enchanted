# T-093 探针本地检查记录（2026-10-17）

状态：INCOMPLETE。只证明合成数据下的辅助逻辑；真实 CLI、钥匙串、macOS 沙箱均未实跑，产品实现未开始。
task T-093 / attempt a1 / writer s16-t093 / ready_rev 1 / 启动记录 `launch-45148b6732394eccab3b21224b238513`。
环境读回 session `67f986cc-92e4-4089-9c22-802a1143b645`，native session `01a14ae2-a3df-7731-a7b0-1b679b3bce95`；
本进程未提供 `A2A_FENCE`，不补造其值。
源码起点 `61786370428c3ec5f894ea60acccf2695d54c2dc`；请求配置为任务卡中的 Codex CLI、gpt-6.1-sol、xhigh、fast，
不把请求配置当作供应商实际 tier 证明。

| 检查 | 结果 | 证据边界 |
| --- | --- | --- |
| `python3 workbench/tests/probe_t093_normal_login.py` | PASS：只显示范围 | 不读真实凭据、不启动 Claude |
| `python3 workbench/tests/test_t093_probe_safety.py` | PASS：4 项 | 合成 token、实际本地 HTTP、超时子进程、临时目录清单 |
| 验证驱动首次运行 | INCOMPLETE：路径错误，退出 1 | 非红态；保留 `probe-helper-checks-01.json` |
| 修正后的验证驱动 | PASS：基线绿态与 4 个断言红态 | `probe-helper-checks-02.json`；真实 CLI/凭据读取均为 0 |
| v1 独立只读审查 | NO_GO：三项发现 | `PROBE-REVIEW-v1.md`；不把辅助检查通过当作安全设计通过 |
| v2 首轮反例检查 | INCOMPLETE：一个反例由 KeyError 结束 | `probe-helper-checks-03.json`；驱动正确拒绝把它当有效红态 |
| v2 当前辅助检查 | PASS：基线 4 项、5 个单点断言红态 | `probe-helper-checks-04.json`；新增副本 A→B、Library 祖先链接、URI token 脱敏场景 |
| project-map status | PASS：0 problems、0 stale living docs | 本 session 开始与辅助检查后均运行；不代表 ticket 验收通过 |
| T-093 产品红/绿/反例 | INCOMPLETE：未运行 | 等主控返回前置探针结果后才能开始产品工作 |

当前五个变异体分别遗漏扫描、接受错误 bearer、遗漏清单范围、将超时当成功、重读可写凭据副本。
每次只改一个表达式，对应测试以 `AssertionError` 失败；没有用导入失败或环境失败充当反例。
完整检查输出和退出码保留在上述 JSON。这里未取得真实 CLI 登录、真实 OS 隔离或产品通路证据。
03 中清单遗漏反例访问不存在的 Library 键引发 KeyError；补充“Library 必须有记录”的业务断言后，
04 才取得有效红态。验证驱动同时修正了单项测试选择；当前每个变异仅执行对应测试。

v2 针对第三项审查发现采用 OS `deny process-fork`，而非声称进程组清理能终止另建 session 的后代。
CLI 的无凭据前检必须实际证明 fork 被拒绝，失败即停；此边界尚未在沙箱外实跑。
完整隔离 HOME 删除亦需由真实探针记录 `isolated_home_removed`，TemporaryDirectory 辅助测试不替代它。

重放（必须使用新的输出文件，保留此前记录）：

```sh
python3 evidence/2026-10-16-batch16/T-093/check-probe.py --output evidence/2026-10-16-batch16/T-093/probe-helper-checks-replay-01.json
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
```

只读审查结果另存本目录，不把审查脚本或模拟结果上调为真实边界通过。
所有产物均为小型脚本或文本摘要；未生成需要外置盘归档的真实 run/fixtures、二进制包、数据库或监视器日志。
