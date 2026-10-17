# 09B 双角色 fake API／阶段 driver／独立 oracle

本轮只实现可审阅的确定性夹具，不启动 HTTP、CLI、daemon、Electron、目标或模型。driver 在 `workbench/tests/t078_09b_driver.py` 内直接记录 fake Messages 请求、broker dispatch、stop/request/inbox ID 和目标字节；没有 operator 业务代理。

## 红、绿与反例

[红态](09b-driver-red-feedback-05/results.json) 让反馈观察正文多一个字符，独立 oracle 以登记 dispatch 正文比较并拒绝 `registered_feedback_text`。绿态 [PASS](09b-driver-green-05/results.json) 通过：ideation 4 roots/6 Messages、executor 6 roots/11 Messages，合计17；实际 stop/request/inbox/ack ID 全部由本次 scenario 生成，dispatch.seq 在两角色之间全局连续，反馈正文逐字等于登记正文。

三个独立变异也被拒绝：[seq-reset](09b-driver-mutant-seq-reset-05/results.json) 捕获 `global_dispatch_seq`，[identity](09b-driver-mutant-identity-05/results.json) 捕获 `target_identity_lifecycle`，[duplicate-esc](09b-driver-mutant-duplicate-esc-05/results.json) 捕获单目标只能有一个 `0x1b`。这些检查只用内存对象和固定字节，不是实时角色或目标验收。

driver 的因果序列按批准预算展开：I1 tool→stop、I2 send feedback；E1 stop wake/wrong target、E2 target stop、E3 ack、E4 duplicate ack、E5 already-acked stop、E6 final feedback；I3 foreign ack、I4 final feedback。每个根的 prompt 取实际注册 Dispatch.text，未写死 `#1/#2`；oracle 读取 dispatch 全局 seq、完整正文、实际 request/stop/ack IDs、role、target attempt/session/fence 和 received bytes。

## 可执行 launch 包

提交脚本在产品与夹具首提交后运行 `prepare-09b-executable.py`，冻结新 root、两个 role approval、独立目录、manifest、target card（含 `oracle_paths`）、空 approvals 和 source tar。它只调用 `prepare_t078_p1.ts` 构造 argv，不启动任何过程；`static-check.json` 明确 `launch_status=NO_GO`。运行前仍需真实受管 target dispatch/claim 填充 attempt/session/fence/workspace，不能用 null 或 operator 代写。

两角色 proposal 共用 broker/state/repo，各有独立 HOME/config/tmp/shell/requests/hooks/user-data/debug；拟预算 I=4/6、E=6/11、模型0。真实 launch 前要逐屏、逐窗口、逐次一次性工具批准；真实 Stop/UPS 与权限反例另行取得红绿证据后才可批准。09C 不在本包内。

主控 #189 另收紧 launch role card：只接受 `roles/<preset>/role.md`。旧 root/role.md 兼容分支的红态与拒绝绿态单独保存；P1 generator、run_p1 和 profile tests 均使用 preset role card，避免双路径 fallback。
