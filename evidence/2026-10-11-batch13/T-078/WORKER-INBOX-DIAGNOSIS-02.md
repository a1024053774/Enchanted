# worker-inbox 失败诊断与 regression-02 交接

2026-10-14，主控 #146。**诊断与局部修复 PASS；新整段回归 INCOMPLETE，尚未运行。** 候选起点 `0f754a6dfd555568cb377affbbe52655a13d3d4d`。原 `rebased-outside-regression-09a3` 保留 INCOMPLETE；runtime 12／input-failures 11 的已跑 PASS 只绑定原版本，不改写、不重新运行。

## 实际返回存在，空值来自夹具

原 worker 客户端七次调用都生成请求文件，登记的 task／attempt／session／fence 与实际 launch 一致，Stop 的匹配、转交、七条结果写入和一次反馈派发均完成。撤销后的第八条也写入拒绝结果。只读原库得到：

- list 返回实际 worker 范围；issue 记录实际 worker 为 from；两次 ack 指向同一条本人确认。
- assign／ready／foreign ack 分别被 invalid_direction／controller_required／recipient_required 拒绝；撤销后的请求被 stale_attempt 拒绝。
- issue／ack 因本夹具没有实际主控接收者而附带 wake_undelivered；持久条目仍在。这是原夹具已声明的范围，不把它改为“真正送达”。原业务断言检查实际条目和来源，未要求这些请求的 ok 必须为 true。

见 [只读诊断](worker-inbox-diagnosis-02/diagnosis.json)。因此没有证据指向 claim 来源、受管派发、凭据或 attempt 绑定的产品缺陷，本轮不修改产品。

根因在 t078_worker_inbox_scenario.py：它用 `id:<request_id>` 组装 relay_results 的内部 key。T-077 的 key 已按 launch 限定，实际为 `id:<launch>:<request_id>`；八个旧查法全部错配，导致 observed={}。旧脚本仍能数到七条结果并核对反馈字节，因而“Stop 转交”通过，同时各条回复判断全空。

## 最小红态与修复

[红态](worker-receipt-lookup-red-final-02/results.json) 直接执行现有回执消费表达式，读取原失败库：三个权限拒绝、实际 issue 来源、list 范围、ack 幂等、撤销拒绝及 opaque key／同 request ID 不同 owner 共八项失败，exit 1。该检查不启动后台、CLI、UI 或模型；预期来自本卡与 T-077 的 owner 限定契约，未从消费表达式生成答案。

只改夹具消费者：通过 relay_requests 的 launch 与 request_id 绑定，把 relay_results 的 opaque key 关联回请求 ID；不依赖 key 字符串格式、不搜索其他 launch，不保留双查法或格式容忍。正常与撤销后的读取复用同一个私有 helper，原业务断言不改。

[同一探针绿态 8/8 PASS](worker-receipt-lookup-green-02/results.json)。原失败库的回执现在正确读取；另给两名 owner 相同 request ID、任意 opaque key 的 sentinel，选定 owner 只得到自己的结果，证明消费者不依赖当前内部前缀。原产品失败结论不被这份离线局部绿态上调为全回归 PASS。

原库已关闭且无 WAL，诊断使用 immutable 只读，避免 SQLite 在沙箱外尝试创建 SHM 文件。首次 SQL 命令转义及首次普通只读打开错误属于诊断设置错误，不当产品红态；没有修权限或改数据库。诊断脚本再次核对 cleanup 完成和 WAL 不存在后才使用 immutable。

## 只续跑尚未完成的部分

同一阶段脚本现使用显式 `--mode regression-02`，新目录 `rebased-outside-regression-02-09a3`。它先核对 runtime/input-failures 原记录 PASS、cleanup 完成，并比较原版本到新冻结提交的 src/app/hooks 无变化，才复用原 frontend build。旧 regression 模式不再作为当前运行入口，不重试旧目录。

执行序列只有 worker-inbox 14 → 8/9/18 → CAS 1 → 四个 worker 权限反例。实际 Electron/PTY 仍只用受控 native receiver，真实供应商模型预算 0；不启动真实 Codex／Claude／API。外置盘缺失即停，不回退；每段失败保留，不自动重试，不改业务断言。三个旧 fence/CAS/lock 变体没有加入本次阶段，不冒称已运行。

先由主控以原 worker 启动身份提交修复和证据：

```sh
sh /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/commit-regression-02.sh
```

脚本将原失败、原 source freeze、最小红／绿及本次修复一并保存；尾注由钩子产生。提交后独占写 regression-02-source-freeze.json，原 rebased-source-freeze.json/txt 不覆盖。新冻结文件作为后续材料提交内容。

再由主控在沙箱外运行：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/rebased-stage-09a3.py --mode regression-02
```

当前 worker 不 add／commit、不请求提权、不运行该外部阶段，也不改 core.ts／taskCards.ts。本轮诊断与离线探针的模型、vendor CLI 和 UI 启动均为 0；独立 reviewer 尚未运行，阶段准备不替代独立验收。T-078 保持 open、INCOMPLETE，尚未交新 launch 审批。
