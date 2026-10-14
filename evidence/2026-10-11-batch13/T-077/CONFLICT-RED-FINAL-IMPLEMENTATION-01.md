# F1 修正候选与运行口径

**INCOMPLETE：只完成夹具修正、局部分类器反事实和静态检查；真实门禁的七红/七绿尚未运行。** 产品冻结 `5d0bf1e8`，不改产品或 acceptance。final-05、原独立审查及全部旧失败保持原样。

## 分类规则

七个冲突场景各有一个固定 target_assertion_id，目标 contract 同时保存到断言记录和有序凭据。分类器要求目标恰好执行一次、目标本身失败、unittest 确有 failure、执行 1 项、无 errors/skipped/cleanup_failures；不能再把其他 contract 的失败算成该目标红态。

主控 #123 已明确：前置按目标之前、且目标成立所依赖的真实步骤逐条定义，三个重交凭据只属于 06/07。当前删除统一三项规则，改为穷举七案的前置表，没有缺省项或例外开关。每份所需凭据仍须恰好一份、为 true、有实际读回内容、且先于目标。缺失、失败或迟于目标都记 missing_preconditions、NOT_COVERED，不能计红。旧准备目录 01 保持原样，新口径冻结在准备目录 02。

| 案号 / 稳定目标 | 目标前置（runner 与每案收据逐条留档） |
| --- | --- |
| 01 / CONFLICT-ACTIVE-WRITEBACK | 原始场景完成；受控 worker 会话输入可用；真实文本冲突产生；匹配原 attempt/C1/G 的 verification_conflict 已持久化 |
| 02 / CONFLICT-ENDED-NEW-ATTEMPT | 原始场景完成；原 thread 的 stopped=true/running=false 受控输入已写入并读回；真实文本冲突及进入处理的持久化事件 |
| 03 / CONFLICT-UNKNOWN-SESSION-REPORT | 原始场景完成；原 thread 的 unknown observation 受控输入已写入并读回；真实文本冲突及进入处理的持久化事件 |
| 04 / CONFLICT-UNKNOWN-DELIVERY-ONCE | 原始场景完成；delivery_unknown=true 受控输入已写入并读回；真实文本冲突及进入处理的持久化事件 |
| 05 / CONFLICT-GIT-ERROR-CLASSIFICATION | 原始场景完成；实际 merge 返回 73、实际 unmerged 输出为空；该 C1/G 的 verify 已执行 |
| 06 / CONFLICT-REWORK-FORBIDDEN-PATH | 原始场景、真实文本冲突、进入处理的持久化事件；投递成功；显式 C2 重交成功；C2 的目标 verify/path_check 已执行 |
| 07 / CONFLICT-REWORK-FOREIGN-TRAILER | 同 06 的前五项；C2 的目标 verify/trailer_check 已执行 |

02～04 的 session 状态是原测试明确替代的受控外部边界，凭据如实标作 input_configured，不伪称真实模型或 OS 观测，也不把“门禁已执行正确处理”当作其自身目标的前置。verification_conflict 事件在 writeConflict 调用之前保存，所以它证明进入处理，不能替代回写、换 attempt 或上报目标。

凭据来源：

- 投递：原 attempt/thread 的外部 feedback 记录、相同文本的 boundary transport prompt、绑定原 verification/message 的 conflict_feedback_delivered 事件同时存在。
- 重交：真实 submit 返回成功，task/current_attempt/C2 读回一致，存在绑定该 attempt/C2 的 conflict_rework_submitted 事件。
- 目标 verify：实际命令返回后，新 verification 绑定 C2，并有该 verification 的 path_check 或 C2 trailer_check；01～05 则记录其实际初次 verify，不能误称重交验收。
- 清理：单独记录 cleanup 抛出的异常并重新抛出。unittest 会把清理中的 AssertionError 记作 failure，因此不能只靠 errors=0；新规则明确排除这类失败。

## 定向变体

只在 /tmp 的隔离副本改 core.ts，不提交变体源码。06/07 不再使用“删除 writeConflict”的变体。

| 场景 | 变体 | 目标 |
| --- | --- | --- |
| 01～04 | 保留原 no-conflict-feedback 变体 | 分别固定为 active writeback、ended new attempt、unknown session report、unknown delivery once |
| 05 | 保留 merge I/O 被错报为 text conflict 的变体 | CONFLICT-GIT-ERROR-CLASSIFICATION |
| 06 | 仅在 attempt.rework.state=submitted 时绕过 forbidden.length 的最终 requireGate；保留路径枚举/事件及正常非 rework 守卫 | CONFLICT-REWORK-FORBIDDEN-PATH：verify 必须拒收 path_boundary_failed |
| 07 | 仅在 rework.state=submitted 时跳过 trailer task mismatch 分支；其他九项结构/身份检查保留 | CONFLICT-REWORK-FOREIGN-TRAILER：verify 必须拒收 trailer_task_mismatch |

06/07 保留真实文本冲突回写和显式重交，新目标由原两条拒收断言组成等价的精确 ok/error 判断，没有允许另一种失败或跳过 verify。要求三份真实前置凭据完整，再接受目标断言处的失败。

## 当前局部证据与限制

主控 #123 的逐案契约先在修前 `a5c6d50c` 原样夹具上失败：9 项、79 failures/0 errors，见 `conflict-policy-red-01/`；fixture-at-run.py 与该提交逐字节一致。修后同一九项检查通过，见 `conflict-policy-green-01/`；对每案每个前置分别注入缺失、false、迟于目标，仍须 NOT_COVERED。旧“任意失败即红”表达式在新矩阵上产生 103 failures/0 errors，见 `conflict-policy-any-failure-mutant-red-01/`。这些是 fixture 分类证据，真实七红/七绿待主控运行。

以下为保留的前轮局部证据，不替代当前口径：

- 原 final-05 的两个错误红态对独立“前置失败不算目标红”要求失败：2 failures/0 errors，`conflict-classifier-recorded-red-01/`。
- 使用 Git 中旧 classifier 的原始 bool 表达式做内存变体：9 项检查，19 个断言失败、0 errors/skipped，`conflict-classifier-mutant-red-02/`。目标没执行、缺/假/晚前置、非目标失败、skip、cleanup assertion 等都能检出旧规则。
- 修后同一局部输入矩阵：9 项通过，`conflict-classifier-green-01/`。这些只证明 fixture 分类，不称为产品红绿。
- 7 场景的 helper/关键字静态预检：279 处绑定，0 缺口；四个变异点各出现一次，`conflict-fixture-static-01/run.json`。目标 verify、实际投递与新定向变体仍须在沙箱外运行。
- 首次旧表达式探针同时选中 predicate 和 console readback，尚未执行测试便失败。原 `conflict-classifier-mutant-red-01/` 保留为 probe error / 非反事实；只收紧 AST 选择器后换新目录运行，未改业务预期。
- 本轮一次 Python 文档替换命令在解析 stdin 时报告 Non-UTF-8，未执行文件写入；改用 apply_patch 完成局部修改并回读 UTF-8。此为编辑命令错误，不是产品或反事实失败。
- 本轮首次静态检查未等准备进程完成，过早读取仍在写入的 tar，报 ReadError: empty file。原工具错误文本留在准备目录 02 的 early-static-check.stderr.txt；等待准备进程 exit 0 后按顺序检查。没有改归档验证条件或重试业务场景。

再生成局部证据（新输出名，不覆盖已有目录）：

```sh
python3 -B evidence/2026-10-11-batch13/T-077/check-recorded-conflict-red-01.py --output evidence/2026-10-11-batch13/T-077/recorded-red-replay
python3 -B evidence/2026-10-11-batch13/T-077/check-conflict-classifier-01.py --old-rule-mutant --output evidence/2026-10-11-batch13/T-077/classifier-mutant-replay
python3 -B evidence/2026-10-11-batch13/T-077/check-conflict-classifier-01.py --output evidence/2026-10-11-batch13/T-077/classifier-green-replay
```

第二条预期 exit 1、0 errors 且目标检查失败；第一条对保存旧记录确认缺陷后 exit 0。全部为无后台、零模型回合。新的真实入口阶段为 outside-sandbox.sh conflict-red-final-01，运行结束前不补称 F1 已关闭，也不自行启动针对性复审。
