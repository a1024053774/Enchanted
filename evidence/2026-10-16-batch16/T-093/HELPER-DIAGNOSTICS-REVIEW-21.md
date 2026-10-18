STATUS: PASS
TARGET: a4fdee0b8ebf7b60ec26ceea32515ee0ef694832

EVIDENCE:
- 本结论只覆盖 pane_process_info 新增诊断及其直接影响的 L0/L1；整票 T-093 仍为 INCOMPLETE。真实 OS helper、真实 daemon 传输和原生七场均 NOT_RUN；没有请求或默认批准重跑。
- 审查合同来自本轮任务：helper 失败时保留 stdout、stderr、退出码／信号和耗时，身份错误继续立即停止，原异常／错误码和正常成功行为不变，诊断进入原 daemon 回复和事件库。先保存 ORACLE.md，随后才阅读候选源码与测试；没有使用实现者报告或既有绿态作 oracle。
- 起止 HEAD 均为冻结候选，所有受控文件与候选相同；初始未跟踪文件未操作。完整核对见 freeze-initial.json、freeze-final.json。session 开始和结束的 project_map.py status 均为 0 problems、0 stale living docs。
- Git 只读导出候选及基线 19c2973157b31e5f6c51320e6dcc77e53e0bce7d 的完整 panes.ts、daemon.ts、store.ts；Refusal 从各版本原始类体提取。Node 26.5.0 内建类型擦除加 VM 执行生产方法和原 daemon 请求处理器，未改写生产行为。
- 全新独立输入：inputs.json。15 个输入，包括空输出、含中文换行的 stderr、带新 nonce 的截断 JSON、执行错误的部分 stdout/stderr、数字退出码 73、同步 ENOENT、SIGTERM／SIGKILL、maxBuffer 错误、错误 root/schema、相对 command、重复 PID、无关进程树，以及 Claude/Codex 正常查询、空树、领导者不符和 Codex 会话结束。
- 候选 run-02：15/15 PASS。10 个失败输入各通过真实 Panes.processInfo、daemon pane_process_info、daemon pane_release 三个入口；每个入口恰好一次合成 helper 调用。原 SyntaxError、Refusal 实例及错误码保留，helper Error 保持同一对象；失败后状态仍 unknown，终端 write=0、drain=0，没有释放或派发事件。
- 诊断的 stdout/stderr 逐字核对，包含空串和换行；helper PID、root PID、退出码、signal、killed、error_code 均与外部夹具事实对应。10 个失败输入使用不同的单调耗时，覆盖 0.5～203.5 ms，逐值准确。新输入会改变诊断，固定输出无法通过。
- 对 20 个失败 daemon 请求，从原 request_rejected 事件读出的完整 result 与送回调用方的 JSON 相等。每个案例使用真实新建 SQLite，关闭后另开只读连接，全部事件与关闭前一致；并非仅比较内存日志。
- 5 个非 helper 失败／正常生命周期输入 PASS；包括健康 Claude、健康 Codex、空进程树、领导者替换标记和 Codex shell-only 会话结束。候选与基线全部 15 个案例的业务结果、错误消息、Refusal 类型和返回码在去掉新增诊断后完全相同。
- 每个版本合计 40 次合成 helper 调用，25 个原 daemon 处理器请求；不执行进程枚举或真实 helper。所有外部模块均白名单注入；意外 import、进程信号、定时器、真实 CLI、auth 和其他外部动作均被拒绝。文件访问限定本次拥有的全新临时目录。net.createServer 只保存回调；listen 为内存无操作，无 OS socket 或 listener。
- 候选自带 test_t093_process_diagnostics.mjs 已作静态阅读，未运行。其测试同样覆盖原处理器和真实 SQLite，并以 helper/连接/时钟为合成边界。独立结论依赖本报告的新输入及基线反例，不依赖该测试的绿态。
- 原始结果：/private/tmp/t093-independent-21.Vq4MAx/run-02/raw-results.json；精确 argv、stdout、stderr、退出码 0：run-02-command.json。完整夹具：replay.mjs、inputs.json；冻结源码在 candidate/、baseline/。
- 精确重放命令（末尾必须为尚不存在的新目录）：
  node --experimental-vm-modules /private/tmp/t093-independent-21.Vq4MAx/replay.mjs /private/tmp/t093-independent-21.Vq4MAx/run-replay-03
  该命令预期退出 0，报告 candidate_pass=15、candidate_total=15、known_bad_business_rejections=10、baseline_infrastructure_errors=0。

FINDINGS:
- 本次限定 L0/L1 内没有复现候选违反合同的情形；不据此作整票或真实系统验收。
- 首轮 run-01 的审查夹具用 deepStrictEqual 直接比较不同 VM realm 对象，出现“结构相同但原型不同”的假红。已只将本临时夹具的 JSON 对象先序列化再比较；保留 run-01/raw-results.json、replay-run01.mjs、inputs-run01.json，没有覆盖、删除或把它当作产品缺陷。另将预期 metadata 明确写入外部 inputs.json，避免由生产代码求出预期值。

COUNTEREXAMPLE:
- 同一业务断言在旧版 19c2973157b31e5f6c51320e6dcc77e53e0bce7d 的 10/10 失败输入上为 FAIL；每个都精准失败于 direct complete diagnostic、pane_process_info: complete diagnostic in reply、pane_release: complete diagnostic in reply，实际值为缺失诊断。旧版仍执行同一真实解析／拒绝路径，原错误码、一次调用、无释放和正常成功比较均通过，没有导入错误或环境失败。因此红态来自缺少所需业务诊断。

LIMITATIONS:
- 本次只证明合成外部边界下的 L1 逻辑和真实合成 SQLite 持久化，不证明 macOS libproc、系统进程 metadata、真实子进程退出时序、原生 CLI、OS 沙箱、socket、Electron、auth 或真实模型行为。
- 原生七场及真实 helper 均依用户要求未运行，运行时机由用户决定；禁止把本次 PASS 外推为 T-093 整票 PASS、发布许可或恢复七场通过。
- 领导者替换仍以原有 failed 标记返回，本报告核对其结果与基线一致；未修改或重审原网络／恢复白名单。未对所有 helper 错误与 OS 竞态作穷举。
- 本次报告和 SQLite 仅保存在新建 /private/tmp/t093-independent-21.Vq4MAx；未修改工作树、分支、提交、旧证据、用户 HOME 或外部状态。
