STATUS: INCOMPLETE
TARGET: 67d04d1387ec897a0c45edba4715679107434e94（对比 c77c56fde8c85e84fcf291dc138db8f2b03cf37f）

EVIDENCE:
- 验收依据：T-140 ticket、外部任务卡和最新逐例失败隔离要求；本次仅只读检查，没有启动 Electron、CLI 或后台。
- RUN-OUTSIDE-03.sh:71–126 的逐例边界保存退出码、业务错误和 case_error；异常强制 INCOMPLETE，写入 run.json 后继续。未发现把诊断失败转换为成功的 fallback。
- 旧驱动在后台停止前采集设置事件；新驱动通过 orchestration_events 和 launch_show 读取持久化记录，避免重新打开已关闭的 WAL 数据库。预期的请求失败会记录 snapshot_error，并继续清理。
- 保存的故障隔离自检包含损坏 JSON、非对象 JSON、摘要缺失和诊断缺失；四项均 INCOMPLETE，后续 sentinel 为 PASS。独立读取核对该矩阵及新 Python 语法均通过。
- t140_cdp_click.mjs 使用浏览器 Input.dispatchMouseEvent；检查可信移除、同坐标两次 Save 的 pointerdown、Save 时空草稿，以及后台精确的 [[X], []] 事件序列和新 worker 的写入拒绝。
- 普通用户两次点击由浏览器分别处理；当前 React Save 首先设置 busy 并禁用按钮。因此旧驱动“同一 JavaScript 任务内移除后立即调用旧渲染 Save”的证据，不能证明真实快速双击会保存旧列表。

FINDINGS:
- 未发现本轮新增代码中可确认的设置失败或必然误通过断言。

COUNTEREXAMPLE:
- 故障隔离自检拒绝四类异常摘要／诊断输入，且没有阻止 sentinel。
- 新 runner 要求旧驱动在 T-RC 写入断言失败且保存事件为 [[X], [X]]；变异还必须具备业务反例并有普通绿态。当前候选尚未取得这些原生结果。

LIMITATIONS:
- RUN-OUTSIDE-03 的原生绿态、红态、变异、回归和可信快速双击均待运行；当前不能判定整体验收 PASS，也没有已确认的真实双击产品故障。
- 保存的自检记录 candidate_revision 为父提交 c77c56fde，而非本次固定候选；本次仅核对其内容，没有重新执行自检。
- 脚本化模型接口能验证真实 CLI／沙箱边界，不能证明真实模型理解。
- 本轮确认覆盖的是预期的请求异常；没有运行清理故障注入。

RULE:
- 无新增重复故障类规则；逐例诊断错误必须保持 INCOMPLETE 并继续后续用例的检查，已放在 runner 自检中。
