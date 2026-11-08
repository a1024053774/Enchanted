# T-259 启动阻塞停点

状态：BLOCKED。记录日期：2026-11-08。当前仅新增缺陷记录、任务卡、失败证据和 README 状态纠正；没有修改产品代码或正式数据库，没有安装新候选。

## 已确认

- T-258 候选 49c7b9a9435f68aec38a862125b8f00220b9b3af 保留。真实父版晚启动红态、候选 8 项业务绿态和 117 项模块检查已完成，独立审查尚未完成，未集成/安装。
- T-258 a3 dispatch 在窗格创建后、初始运行身份落库前失败；任务未发送，回收 identity_conflict。
- 执行主控依用户“修启动阻塞后继续（推荐）”在启动恢复范围内建 T-259。首次 dispatch 因 T249 旧卡宽泛测试路径而拒绝，未创建 attempt。核对 T249 真实改动只含自身三个测试且窗格已停止后，第二次以明确 overlap_reason 派发。
- T-259 a1 也返回 gate_failure / SyntaxError: Unexpected end of JSON input；attempt 260eb9eb-7007-4c59-8deb-57128d0b8629，thread 55b39039-fb45-4f00-ab43-0c00f51ab978，launch 0ec7b31b-3fab-43fc-bdd6-705cecf9c7b6。同样没有任务输入，reclaim 明确 identity_conflict。额外启动信号处理也记录 codex_startup_failed，同一 JSON 错误。
- 两个 worker 的实际 argv 都是 gpt-6-astra、xhigh、default。当前主控和这两个 CLI 达本轮 3 会话上限，未再派会话，没有启动 Claude。
- tasks、attempts 和 memberships 的持久 JSON 只读检查没有发现畸形值；之后对 T259 shell 39525 的三个只读进程观察均 exit 0、743 字节。这些后续正例不能定位此前错误，也不能消除原失败。
- README 先前提前写入 T258 候选行为，已改回未集成版本的实际启动恢复限制；详细候选说明仍在原提交与证据中。

## 具体停点与所需决定

原门禁自身的派发无法把任务交给修复 worker。现有 reclaim 需要初始绑定身份；普通重启不补这个缺失值。没有继续重派、手改数据库、伪造原生记录或借其他任务释放原路径。

已通过本对话问答框申请一次临时修复流程例外：由当前主控在隔离工作区修启动阻塞，另开干净 astra xhigh 普通速度会话独立审查；完整候选与测试证据再交用户批准，批准后才临时安装，随后恢复原门禁完成交付。当前没有收到决定。

需要这次决定的依据是 AGENTS.md 第 28 行“门禁不能省，写审分开”和第 31 行“工作台出缺陷时停下上报并开缺陷票，不回退 Herdr”。原授权允许修缺陷，不自动授权上述受管流程例外。暂不执行依赖这项决定的代码修改、独立会话或临时安装。

## 后续与保留

T-249 产品候选已 verified，Test 包实际存在且曾被 Computer Use 读取；最终 terra 验收仍未完成，敏感脚本集成批准尚未申请。T-250 未开始。恢复后按 T259 → T258 审查/标准包 → T249 最终 terra/用户批准 → T250 的依赖顺序继续。

T249 checker 的 except (AssertionError, KeyError, ValueError) 已验证是真实 CLI 顶层失败边界：原始正确输入 exit 0，两个坏输入 exit 1；打印 FAIL 并失败退出，不吞错或兜底放行，保留处理。证据为 T249/controller/exception-boundary-review.json。

Works：本次两次独立派发失败与回收拒绝有原始回执，状态准确保留；没有宣称修复完成。
No regression：本次未改产品代码；未新增运行产品回归套件。现有测试通过只绑定其原候选，不替当前缺失的独立审查背书。
Risk / undo：准备中的两个 CLI 与工作树仍保留，不直接清除；root 持有的固定 hc 缓存、验证依赖链接和原始红绿报告留待恢复使用。文档变更可按本次提交局部撤回，不影响正式应用或候选。
