# T-265 原生材料投递验证

PASS：第六轮经真实交互 Codex 完成父版红态、候选绿态和自有进程清理。整张票仍待独立审查、安装及接回原大候选审查，不能据此宣布整个工作台完成。

Works：`native-cli-06.json` 记录父版实际投递 1,665,447 字符，被原生 1,048,576 字符上限拒绝，没有开始回合。候选的入口为 177 字符；原生工具读取了全部 2,150,753 字节、1,665,453 字符，55,000 行 diff、50,000 行验收数据和随机头中尾标记均与生成输入相符，材料写入被沙箱拒绝（errno 1），原生回合正常结束。期望来自外部生成的输入；实际 probe 源码未改，材料原字节未改。完整启动参数、实际工具调用和结果在 `native-cli-06-artifacts/`。版本为 Codex 0.167.0、Node 26.5.0、Python 3.9.6；请求模型 gpt-6-astra、xhigh、default，不把请求 tier 当作供应商执行 tier 的证明。

No regression：本轮调用 worker 原脚本的父版和候选用例，没有改业务断言、权限、onboarding 或 240 秒期限。`native-cli-06-exit.json` 确认运行期间产品和驱动与冻结快照逐字节一致。两条自有 CLI 都由同一个 Popen 的 wait 确认退出；676 个文件、1,203,963,649 逻辑字节的隔离夹具已记录后删除。产品长短材料、四家 CLI、隔离身份和错误路径的开发检查由 worker 保存；机械检查和独立审查仍由门禁执行。

早期结果保持原状：native-01/02 是启动或驱动 INCOMPLETE；native-03/04 已观察到真实父版拒绝，但整体因退出清理未完成；candidate-05 的原结果也保持 INCOMPLETE，其独立业务核对在 `native-candidate-05-behavior.json` 为 PASS。主控逐项确认相应自有进程消失、记录文件统计后才清理夹具，没有删除失败文本。原生工具最初的 cat 输出发生截断，随后用完整字节读取和指定 probe 完成核对，未把截断输出算成全文读取。

`process-wait-probe-02-events.jsonl` 保存直接清理原因：TERM 三秒后 getpgid 返回 ESRCH，Popen.poll 仍无退出码，ps 仍看到退出中的同一 PID；关闭本次测试的 PTY master 后，同一 Popen.wait 立即返回 -15。最终驱动先保存诊断、释放自有 master，再确认退出。ESRCH 本身没有被当作成功；EPERM 和身份不符仍拒绝。该探针只证明这一次资源顺序，不证明所有进程消失都可视为已回收。

Risk / undo：真实 CLI 探针没有执行完整 review_submit/Stop 审查生命周期；该路径及实际大候选恢复由后续门禁审查和安装验证覆盖。产品修改仍限 createReview 的完整材料文件与短入口；需要撤销时只撤该候选，保留上述失败证据。原自动派发预算保持 6，后续输入经工作台正常 UI 完成，人工介入见 `manual-continue-04.json`、`manual-continue-06.json`、`manual-submit-06.json`。正式数据库未手改，没有 push。
