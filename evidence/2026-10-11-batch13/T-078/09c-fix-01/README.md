# 主控 #355：09C 测试工具修复与真实链排练待运行

状态：**固定样本入口红绿 PASS；完整真实链／真实时钟排练 INCOMPLETE，待主控沙箱外执行**。仅改 workbench/tests，不改 workbench/src、app 或 acceptance。未启动真实 Claude/Codex、未调模型、未操作已回收的第1场。

## 固定样本与红绿

固定事实来自第1场已保存的 stop、relay_requests/results、原反馈 envelope、queued tool_result、完整原屏、Electron按键及 hook 原件。另从第1场外置 tar 的 ideation HTTP0001/0002生成 [request-structure](request-structure.json)：只保留真实 model/stream/max_tokens、消息 block 结构、Bash schema、tool_result 字段；上下文文字全部替换，不复制认证头、metadata 或用户凭据。它保留真实 Bash 必填 command 与 CLI trailing-system 形状。

修复前先运行 [recorded-red-03](recorded-red-03/result.json)，四项都在预期原因失败；使用最终测试器重新加载 Git父版本 `f1518b627b85edb0d170fee779cb8202ffae38b3` 的原始工具源码，得到 [known-bad-replay-01](known-bad-replay-01/result.json)，源码原字节保存在其 source/。没有回退或改写工作树中的候选。

| 缺陷 | 红态信号 | 最小修复 |
| --- | --- | --- |
| C-I1 request_id 来源 | 真实字段回放结算 callback 抛 KeyError('request_id') | origin 复用已核对的 queued/relay_requests.request_id；NativePermission/observe 统一按原 C-I1 tool_result→真实 request行→result.key 关联，核对 caller/native/prompt/entry，不向产品结果补字段 |
| C 阶段 envelope | 真实 Handler.do_POST 对实际 feedback 返回409 C_actual_delivery_required | request_id 留外层，业务判断只读取 envelope.result，C-I1→C-I2、C-I2→C-I3、C-I3→C-I4一并修正 |
| 重复输出覆盖 | permission.__main__ 在 mkdir 拒绝后仍覆盖现有 result | 先清空全局 OUTPUT，独占 mkdir 成功后才绑定本次输出；拒绝路径不触碰旧目录 |
| 初始化后重复 release | 实际 start 函数在已初始化 idle 状态派发后又 release，收到 initial_release_only | 保留 initialize 的初始 release；start 只派发，自然 drain，不二次 release |

最终 [recorded-green-06](recorded-green-06/result.json) 全部通过，另证明新鲜1秒的C-I2预检允许、100秒的迟到输入拒绝，不是“一律拒绝”。结算/start 的 I/O是第1场记录回放，HTTP为真实 Handler字节流入口，输出保护走实际 permission.__main__；这些局部证明**不冒称完整 daemon/HTTP/Electron 链路通过**。重复输出逐字节保持原 result，进程/窗口启动0、按键0。反例覆盖错launch、错key、错native session、重复request行、pending冒充delivered，均拒绝。

还补了已在诊断中列出的 C-I2按键前门：原 stop/request/clock 必须一致，check/build前和实际Enter前两次检查。**90秒是测试工具保守的提前截止，留30秒给原生工具和Stop/relay；产品及验收的 `<120秒` 不变**，实际结算仍必须证明 gate stop_too_early 且目标零字节。100秒迟到输入在 [early-gate-red-01](early-gate-red-01/result.json) 的旧入口错误放行，候选在同一实际入口零进程/零窗口/零键拒绝。C-I3新窗口先等待实际launch/thread/active/一次性Yes就绪，再生成严格模板；没有增加按键重试、旧格式兼容或降级读屏。

该窗口等待与命令框读取还用第1场真实Electron journal回放过：[recorded-window-check](recorded-window-check.json) PASS，第一次inspect未绑定，第5次才完整就绪；实际ElectronClient.wait在零键下等到该视图，visible_command对真实Claude2.1.296命令框的解析与已签命令逐字相等。不是为配合parser另造一种原生屏幕契约；完整排练中的peer仅渲染相同命令框结构，不能外推为第2场真实Claude时序通过。

其他回归：[tools-regression-03](tools-regression-03/result.json) **43项 PASS**，含150001ms整场截止零键反例（注入时钟，仅边界逻辑，不是真实时钟证据）；[handler-regression-01](handler-regression-01/result.json) PASS（旧纯逻辑HTTP夹具已改成真实 envelope 格式，仍明确是模拟业务行，不作为产品relay证明）。原工具回归曾因旧oracle要求第二次release而失败，保留在 tools-regression-01；该oracle现在严格拒绝多余release，未放宽产品条件。recorded-red-01/02保留测试器自身早期构造失败，只有03才是四项完整红态，不混算。

tools-regression-01/02/03 的全部纯夹具展开原件按本票既有惯例分别保存在同层 `*.originals.tar.gz`，顶层 result/runner-output 保持原字节，每目录有 `originals.archive.json`；[逐成员读回记录](unit-archive-readback.json) PASS。936/939/942个文件均已逐类型、逐字节比较后才收起展开副本，原失败也在tar内；没有删除历史已提交产物。压缩包各约147～150KB，本批单文件>5MiB才强制外置的规则不受影响；真实第1场仍按live-scene规则全量外置，不与纯夹具混同。

排练就绪文件也按合并后既定规则检查：实际 API.main 的 [ready-red-02](ready-red-02/result.json) 捕获“final路径先暴露空内容”和“覆盖已有ready”，候选改为先完整写pending再独占link发布，[ready-green-01](ready-green-01/result.json)两项通过（HTTPServer为无socket边界替身，只测producer）。host-ready复用已有publishReady，[既有真实文件/子进程探针](host-ready-regression-01/run.json)五项PASS，fixture字节留存后自有scratch已删。ready-red-01的观察器未覆盖keyword mode，保留为不完整构造，不计为有效两项红态。PTY host同时只准真实worker启动本scratch编译的receiver，controller一律替换peer；未知执行请求直接拒绝，避免因角色接线错误启动供应商CLI。

## 主控沙箱外运行一次完整排练

逐字命令见 [RUN-OUTSIDE-COMMAND](RUN-OUTSIDE-COMMAND.txt)：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/workbench/tests/test_t078_09c_real_chain.py --output /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-01
```

该目录目前不存在。实际运行需要本机 PTY、loopback、外置盘 build 与隔离 Electron 权限；本轮只做 [preflight](real-chain-preflight-04/preflight.json) 和 AST/路径检查，没有运行。预计业务时钟约120～130秒，准备构建时间不计入 stop.created_at 起点；外层硬超时420秒，场景自身150秒。只使用新 `/private/tmp/t078-2-a14-rehearsal-*` scratch，不复用第1场；slot唯一，不覆盖或删除旧slot。

排练内容：

1. 真实 daemon、A2AGates、native receiver受管dispatch/claim；真实两角色controller启动通路，只有 provider可执行文件/进程识别在既有PTY seam替换成确定性Python peer（明确不是Claude首启证据）。API为真实loopback phase_plan HTTP，消息形状用本次脱敏结构。
2. 调用实际 C driver 的 arm、initialize、start。两角色先初始化；C-I1唯一 dispatch 后自然送达，真实UPS、Bash命令、排队文件、Stop、relay产生 stop 并delivered。**不在测试中 INSERT成功relay、stop或反馈行，不由operator代发send/stop/ack。**
3. C-I1/C-I2许可调用实际 t078_09b_i1_permission.py，经隔离 Electron 单 Enter与真实结算 callback。C-I2必须真实 stop_too_early；自动根只用实际 gate反馈与inbox唤醒。
4. C-I3调用实际 C driver permission入口、NativePermission实际owner/prompt/window读回与完整分页reader；主控对确定性scratch工具的本次授权由夹具绑定真实模板后原子发布。真实wall/monotonic等待，按键时wall>120000、monotonic≥120100，实际daemon中断事件年龄>120000且<150000；目标恰一个Esc、actor ideation、无ack、原attempt和目标仍在。之后真实C-I4与C-E1中性收尾。
5. 独立读实际HTTP文件、事件、daemon时间与目标received.bin：ideation7POST/4根、executor1POST/1根，三次许可/CR，所有阶段精确状态，不用宽泛成功正则。driver clock记录与独立daemon事件时间交叉核对；父进程单独记录控制段monotonic（从C-I1许可入口前开始，不能冒称精确的stop观察起点）。
6. 成败都保留command stdout/stderr、HTTP/hook/peer原件、SQLite一致backup（包含已提交WAL，停机前做integrity检查），再认证daemon_stop、原Popen API各一次SIGTERM、核对peer/target退出，删除scratch与其专属worker requests目录。停机后不读现场SQLite。失败结果为INCOMPLETE并首败停止，不重发不确定键。build slot另列保留。

预期最终 result.json **PASS**、POST7/1、scene_age_ms在120000～150000之间、cleanup PASS/scratch_removed=true；任一失败就是INCOMPLETE，保留原目录，不重试覆盖。七个原持久进程为真实daemon、两个API、目标shell/receiver和两个PTY peer；NativePermission使用REHEARSAL owner真实PID/argv/lstart，**不冒充真实Claude九进程生命周期证明**。外跑还会按阶段创建并关闭隔离Electron，无供应商CLI或模型。

## 交付边界

第1场回收由主控并行完成，本轮只读取完成收据并纳入提交：archive340792字节，POST13/11、roots2/1、许可1/0，失败/unfinished明确保留，九进程退出、root删除、post_stop_SQLite_reads=0；不是worker执行了清理，也不是把该场上调为PASS。

本修复改变标准冻结闭包中的测试代码，旧四回归收据不能静默沿用。真实链排练尚未运行，独立审查未完成；没有冻结第2场或签新launch批准。后续冻结还须把本次固定输入结构及必要记录样本明确绑定到候选；不能只复制reader代码而漏掉测试数据来源。
