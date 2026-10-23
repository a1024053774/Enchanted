# T-153 全路径身份核对（主控 #11 后）

来源：T-123 明确任务身份为 `<项目>+<任务名>`；短名通过请求 project 或终端角色项目解析。新建卡片不能靠尚未存在的 task 反查项目。

| 调用或数据 | 本次核对结果 |
| --- | --- |
| card_save | 原为短名 T-153-fixture、无 project，是此次 unknown_task 根因。改为短名 T-153-1 + --project B-fixture。 |
| create | 已有 --project B-fixture；沿用同一项目，任务短名改为 T-153-1。保存返回的完整 task_id 覆盖局部 task。 |
| dispatch | 位于 create 之后，--task 使用其返回的完整 id，不依赖隐式项目。 |
| status（worker 等待、交付读取、reviewer 等待、setup-only） | 全部位于 create 之后，--task 使用完整 id。 |
| verify、integrate | --task 使用同一完整 id，attempt 显式绑定原 attempt；没有裸短名调用。 |
| events | --task 使用完整 id；review_reclaimed、submitted、integrated 等均在此身份内读取。 |
| orchestration_events（业务检查） | --task 使用完整 id。收尾另有无 task 的全局诊断读取，CLI 明确允许，不参与短名解析。 |
| 四个注入请求、delivery 回放与 A2A-Task 尾注期望 | common.task 与尾注期望均使用 create 返回的完整 id；不会继续使用初始短名。 |
| worker 的 submit、reviewer 的 review_submit | 由实际派发提示与启动环境给出完整身份；runner 不另外生成裸短名的交付命令。 |
| daemon_start/daemon_stop、execution_settings_save | 全局命令，无 task 参数，不走 task 身份解析。 |
| pane_status/pane_process_info、launch_show | 以 thread 或 launch 定位；无 task 参数，不走短名解析。 |

## 同路径发现的卡号缺陷

加项目后，registration-03 的真实 card_save 到达卡片校验，拒绝 T-153-fixture：绑定 ticket T-153 的卡号还须包含序号。现改为 T-153-1（任务卡约定的编号形式），不修改产品校验器、不去掉 source ticket。预期完整身份依据 T-123 和输入字段独立写为 `B-fixture+T-153-1`。

## 沙箱内实跑

同一个 run_worker_delivery.py 增加 --setup-only；真实 CLI、daemon、门禁、Git、SQLite 跑到 create/status 后停下，不派 worker。auth.json 复制移到交付分支，注册模式不再复制登录凭据。

- registration-02：先被 /bin/ps 权限拒绝，未到 card_save；0 模型回合。该次尚未移动 auth 复制位置，隔离 home 待主控确认退出后清理。
- registration-03：card_save 加项目后不再 unknown_task，进到卡号校验，报 invalid_task_card；0 模型回合。
- registration-04：card_save/create/status 均成功；完整 id 与尚无 attempt/candidate 两项检查通过；0 模型回合。
- 三次收尾均因沙箱禁止 /bin/ps，无法取得退出确认，整体为 BLOCKED，不报 PASS。各次 daemon_stop 已返回自有 PID 的成功停止回执，仍保留现场和隔离 home。RUN-OUTSIDE-02 先核对这些明确 PID 已退出和 daemon.pid 已消失，再只删除其隔离 home，不删除失败现场；随后重新做完整注册检查。

registration-04 只证明注册阶段，本轮真实 worker/reviewer 绿态与通知变异红态仍待主控运行。
