---
id: T-265
title: 完整审查材料内联导致原生 Codex 拒绝超长输入
type: build
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---

## What to build

2026-11-09 T-249 候选 d8f55c9 通过三项机械验收后，审查启动被 Codex 0.167.0 拒绝：输入 1318486 字符超过 1048576 上限，native turn 未开始。现场在 evidence/2026-11-09-batch35/T-265/controller/。GateCore.requestReview 将任务卡、完整 diff、verification 内联为 prompt，PaneManager.createReview 再整体写进 CLI 输入框。

保留完整材料，存为每次审查独立、绑定原身份的文件；原生交互终端只接收简短入口和文件路径。优先用已有 request_dir，与 review-template/result 同属该 launch。不新增公开 API、schema 或依赖，不按大小保留两条路径，不截断材料，不改变正常 Stop、只读候选和 review_submit 门禁。

授权来自本轮用户“修复现在 enchanted故障并继续”“主线是完成主要的两个面板的任务以及 bug 修复”。本票修复原面板审查的阻点；T-264 的额度错误状态恢复单独处理。

## Acceptance

- [x] 保留真实旧版本拒绝；新检查在父版对超长内联输入失败，原因对应本缺陷。
- [x] 完整材料原字节可读，含任务卡、diff、机械结果、先前问题和提交方式；原生消息简短且指向本 review/launch，不截断、不串会话、不覆盖旧材料。
- [x] 文件写失败不发送缺失或半写材料；原候选身份可追溯，只读与提交门禁保持。
- [x] 长短材料、Unicode、两个审查隔离及 2-5 个已知坏实现有明确结果；隔离真实 Codex 能开始回合并读到完整长材料。
- [x] 独立审查、标准打包安装后接回 T-249 大候选；保留历史拒绝，不 push，不手改数据库。

## 当前状态

PASS。候选 a322c79e29e2a3f1102eeefa8411abd1db322951 经独立审查 58c4718e-ef14-4130-b2a2-4c9f5c05625c 通过，2026-11-09 经门禁集成为 a91519dd2a44b1716d83575ad33f2daa93396fa5，worker 正常回收。该合并版本已标准打包、签名验证、包内 Electron 五项材料检查通过，并替换正式应用、正常重启；窗口已显示“后台已连接”和本任务“已集成”。旧包留作回退。

证据在 evidence/2026-11-09-batch35/T-265/：controller/native-cli-06.json 为真实父版超长拒绝、候选完整读取与只读边界、退出清理的完整 PASS；final-candidate-binding.json 绑定最终代码与已测快照；review-01/result.json 记录独立五变异及限制；controller-install/ 保存标准构建、包内检查与安装读回。历史 native-01～05 的 INCOMPLETE 原样保留，不改写。

## Resolution

2026-11-09 07:38:37Z，已安装版本对 T-249 的恢复候选 `63304e0fcb3510d9cf4b1cbea5c3064fbb8286dd` 正常启动独立审查 `f8f9674e-bf70-40b4-852e-d2958d4e92eb`。专属材料文件为 1,838,790 字节、1,624,030 字符，权限 0600；审查员已完整按 UTF-8 读取 35,300 行，进入代码和证据核对。原超长内联拒绝保留，新的原生回合身份与材料绑定见 [接回证据](../../evidence/2026-11-09-batch35/T-265/controller-install/t249-large-review-resumed.json)。这证明审查启动阻点已修复；T-249 自身是否可合并仍由它的审查和 Terra 验收决定。

**Works**：真实旧版超长输入被拒，修复版完整读取长材料；已安装包接回原 T-249 大候选。材料不截断、不覆盖、不串会话，写入失败不派发缺失入口。

**No regression**：长短材料、Unicode、两个审查隔离与五个已知坏实现完成针对性检查；独立审查和包内 Electron 五项检查通过，未改门禁身份、只读和 Stop 契约。

**Risk / undo**：T-264 额度错误后的状态恢复独立处理，本票不声称覆盖该故障。旧失败现场不改写；需要撤回时使用保留旧包，并另走受管回退，不手改正式数据库或重放旧请求。
