# 审查 worktree 衔接：已实现候选，待 final-02 绿态

授权：主控 #110 明确将 issue `20261014T023857Z-worker:s13-t077s-issue-001` 并入本卡，要求保留 T-076-2 的审查绑定、复用与未知暂停语义。实现状态 **INCOMPLETE：尚未运行新的入口绿态**，不是 ticket 通过结论。

先红证据为 `review-lifecycle-recorded-red-01/`。独立断言在 final-01 的原受控真实入口现场读回：review `7bd12904-7b38-4dc2-a4ae-ef204e84a134` 的结果和回收事件已落库，目录仍存在且 `git worktree list --porcelain -z` 仍登记它。1 failure、0 errors，red_confirmed=true。原事件、Git 场景与失败文件不改；这次只读回放没有新启动 daemon 或模型。

重建该读回的命令记录在 `check-review-recorded-scene.py`；同名输出拒绝覆盖。final-02 另会以修复前提交 `7b3463c4a55381d0fb97f782e69cc0029522f6da` 的产品源码，在新夹具里经真实 CLI 运行四条反例，再在候选运行同四条绿态。局部读回不冒称新的入口已通过。

实现要点：

- requestReview 的 detached 目录改为 `<state>/worktrees/<project>/<task>-a<fence>-review-<ordinal>`。序号按同 attempt 已持久化的 review_requested 事件计数，失败意图也占号；同 C 的有效结论复用提前返回，不创建目录或增号。
- 有效结论入库、原 reviewer 已 idle、停止与归档均确认后，才核对审查身份、目录的真实路径、Git 登记、detached HEAD 等于 C、目录干净。然后记录清理意图、用不带 force 的 Git worktree remove 删除，读回目录及登记均消失，记录删除完成，最后发布 review_reclaimed。
- 清理结果只追加事件，不向已通过的 review 对象补写 cleanup 字段。`requireReviewed` 对 review_result 与当前审查对象的严格绑定比较保持原样，R8 可在目录已删除后沿用有效结论。
- 目录脏、HEAD 改变、身份或退出无法核对、命令结果未知，都经原 reviewLifecycleFailed 暂停和上报，不清别的目录、不自动重试、不改写历史审查结论。审查 home 和原生日志不在删除范围内。

新增 `test_review_worktree_lifecycle_e2e.py` 四项覆盖：已存结果后的 detached 目录/登记删除及事件顺序；同 attempt 两个不同候选的用途/序号；外部脏文件保留并上报；干净但未知 HEAD 保留并上报。正常例最后仍带显式评分集成，证明删除不破坏审查绑定；T-076 原有 reviewer 创建/重启/退出未知场景与 R8 三条组合路径仍在全量阶段。

本轮没有改数据库表结构、审查交付协议、review verdict 或原生身份检查。README 同步说明当前行为。先前变基输出、final-01 的原始红态与 24/25 结果、夹具迁移和三条联合路径均按来源保留，未上调为完整 PASS。
