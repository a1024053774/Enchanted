STATUS: INCOMPLETE
SUMMARY: 自动行为测试 PASS；整票 INCOMPLETE。未发现当前候选已复现的产品缺陷，原生 select 完整键盘 Computer Use 与独立审查仍缺失。本报告是用户 #111 要求的实现者自查。
TARGET: base 3647a07bdacb514cdc303965be8c52b84d9356b2 上的三个候选源文件；与主控 candidate-after-green04 逐字节一致，来源和副本见 provenance-08.json。
EVIDENCE:
- 验收依据来自 T-262 任务卡与冻结 ticket：用户输入和门禁回执分区、统一项目/任务/会话过滤、倒序、同名主控区分、完整原文、窄窗和键盘。实现不修改这些验收文件。
- 主控在本 worktree 为外层 cwd、原生沙箱外运行真实 Electron、IPC、后台和 SQLite；green-outside-04.json 完整 38 项 PASS，退出 0。实际模型回合为 0，未启动供应商 CLI。worker 没有把主控运行称为自己执行。
- 期望从独立夹具的原始记录 ID、时间、项目、任务和会话计算，未从产品输出生成答案；完整回执对照原始 relay_results，人工介入对照原始输入场景。数据来自三个隔离项目，含同名任务、多 worker、同名主控、只含回执和只含输入的会话。
- 刷新场景在启动后新增带随机 nonce 的输入与回执；真实 UI 必须显示这些不可预先硬编码的记录并保持过滤。两种真实响应分别被延迟或断开；代理不替换 window.a2a、不合成结果，green04 中传输计划均完成且 errors=[]。
- 五次导航读回均先显示预期项目/独立终端和“终端”，再显示相同身份和“记录”。beta 已显示记录后释放迟到 alpha，原断言确认 beta 未被覆盖；错误与恢复、空项目、清空项目均通过。
- BrowserWindow 原生读回为 900×700，内容尺寸 900×700；长内容无溢出。details 通过真实 Enter 展开/收起，焦点可见；完整回执通过真实鼠标展开。select 采用标准表单选择与正常 input/change，报告 native_keyboard=false，不能代称原生选择器键盘证明。
- 原 red05 有效业务红态保留。green02 的 Browser CDP INCOMPLETE、green03 的导航 FAIL 原样保留，用于证明驱动失败没有被改写成产品通过；修订后才取得 green04 完整绿态。
- 父版、完整候选和四个 mutant 的 core_cleanup 返回 stopped=true，cleanup.removed=true；目录、文件数、字节数和清理时间在各原始 JSON。没有修改正式应用、其他 Test 窗口或数据库。
FINDINGS:
- 无当前候选的已复现产品缺陷。没有将本轮自查视为门禁独立审查或整票验收。
COUNTEREXAMPLE:
- red-outside-05.json：父版排序和任务双区过滤两项业务断言 FAIL，退出 1；这两个断言在当前脚本中未改。
- mutant-no-sort-02.json：取消排序，业务 FAIL，退出 1，检出排序及相关行次序。
- mutant-receipt-task-02.json：回执忽略任务，业务 FAIL，退出 1，检出任务过滤和项目级过滤。
- mutant-ignore-session-02.json：忽略会话过滤，业务 FAIL，退出 1，首先检出同 launch、无 launch 和同名主控过滤；后续数据等待失败同样保留，未当环境错误替代首个有效反例。
- mutant-no-full-receipt-02.json：替换完整回执原文，业务 FAIL，退出 1，检出原始存储与展示不一致。四个 02 后缀均是 green04 后使用 navigation-07 当前脚本的实跑，非旧证据，未重复执行后缀 04 命令。
LIMITATIONS:
- 原生 select 完整键盘 Computer Use、准确提交的独立审查和 Test 包观察未完成；主控负责后续验收集成。因此整票 INCOMPLETE。
- 本自查不是 fresh-context 独立审查。证据层为隔离真实桌面入口和本地依赖（L3/L2），不外推正式环境或任意未来数据。
- 能力边界：异步读取、项目/任务/会话展示范围和桌面交互适用并有上述证据；受管派发/门禁状态机、模型判断、检索记忆、生产写入、文件媒体处理和发布运维为 N/A，本票不改变这些能力。
- 旧 T-133/T-179 全流程依赖 Claude，按卡未运行；新场景验证其相关记录页行为，不替代旧全流程或全仓回归。README stale 由主控集成时同步。
