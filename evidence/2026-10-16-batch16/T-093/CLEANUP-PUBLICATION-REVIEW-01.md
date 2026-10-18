STATUS: FAIL
TARGET: de956c2de70ee0e5f8a564cad961bb132a20de40；比较基线 bc87c71fcfc2c1f43d3c97e6a565d0c663137ebc
EVIDENCE:
- 已检查测试入口、D wrapper、独立核对器、清理脚本、README 和 REVIEW-REQUEST-T093-10.md；相关文件与冻结候选无差异。
- 全新 /private/tmp 目录中的纯逻辑探针复现以下两项问题；未启动子进程、读取认证正文或探测真实 PID。
- project_map.py status：0 problems、0 stale living docs。
FINDINGS:
- [P1] workbench/tests/run_t093_login_chain.py:216 — prepare_session 的直接调用仍在发布主错误前执行内部清理（workbench/src/claudeLoginSession.py:182）。注入准备失败时，rmtree 执行时主 JSON 不存在；再注入 ENOTEMPTY，最终保存的是清理 OSError，原 RuntimeError 丢失。应让该准备路径在自身清理前发布原错误，并将清理异常单列。
- [P1] workbench/tests/check_t093_chain_results.py:23 — V 仅接受组和子进程的 exited 布尔值，没有独立核对它们的身份或存活状态。错误实现将这些值固定为 true，仍能通过清理证明。应校验 PID／组身份，并独立检查所有登记写入者已经退出。
COUNTEREXAMPLE:
- 原异常 independent_primary_probe 加清理 ENOTEMPTY：未拒绝清理覆盖主异常，保存结果为 OSError。
- 模拟组和子进程仍存活、收据均写 exited=true：cleanup_proof 返回 errors=[]；仅探测了 reporter PID。
LIMITATIONS:
- D 的真实 unlink／正文拒读边界、同 OS profile 的 primary／green 演练及正式六场均未执行，状态为 INCOMPLETE。
- 未检查或删除现存夹具，包括 /private/tmp/t093-chain-e189ndt0；未运行 sandbox-exec、供应商 CLI、网络或进程清单。
- 证据层限 L0 静态检查和 L1 合成逻辑；不能据此推断 OS 边界通过。
RULE:
- 在 test_t093_setup_diagnostics.py 中，对 R 的准备调用注入原失败及清理失败，要求每个清理动作前主 JSON 已存在，且清理异常不能替换原异常。
- 在 test_t093_chain_cleanup_oracle.py 中加入“写入者仍活着但收据声称已退出”的反例，要求独立核对器拒绝。
