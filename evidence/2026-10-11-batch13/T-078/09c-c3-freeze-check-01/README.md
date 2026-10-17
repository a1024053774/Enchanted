# 第3场冻结：收据选择与版本

主控#370的无豁免排练 `09c-caffeinate-parity-rehearsal-02` 为 **PASS**，源码 `77865b044b5a5fedeeec12e62eae1314b87bf885`：POST7/1、roots4/1、scene_age_ms123416.47998046875、completion_age_ms123590.11303710938、协调器1次、重复拒绝PASS、九进程完整拓扑与标准回收PASS，停后SQLite读0、root已删。新原Popen REAPED与所有受管PID实际ps缺席收据均留存。

本轮只改冻结校验/生成元数据，不改任何workbench/app/acceptance/scripts代码。`runtime_source_revision`严格绑定上面的实际排练提交；`revision/source_revision`如实记录包含本轮元数据的完整冻结提交，两者不混同。

原校验仍指向失败的-01；即使临时换成-02，其“内核检查后整个workbench必须不变”的断言也拒绝后来已实跑的waitpid修复。[两条现状红态](binding-red.json)保留。新校验分开证据范围：

- 整套运行工具、产品与acceptance/scripts必须逐字节等于-02的77865b044；实际角色/准备器/Stage A runner也保持相同。只允许c3-revalidation与freeze-c3这两个收据/生成元数据文件的更新；它们自身进入新的标准源码冻结，冻结后不能再改。
- 内核正反例仍绑定原 `09c-caffeinate-kernel-outside-01`（e26a7379d）：逐段核对测试文件、imports、require/save、NativeRuntime.helper_identity/executable_path原文与已实测版本相同。它不为新waitpid逻辑背书；后者由-02完整生命周期实跑与原handle/ps收据背书。不是删除内核检查，也不将旧版本冒称当前实跑。
- 四份原业务回归组合不变：02整组整体INCOMPLETE仅因CAS分类器判定；cas-03替代该判定、lock-04补齐、T078自身回归PASS。原件状态与显式例外留在新Stage A校验结果。
- 同时绑定原协调器排练收据与最新九进程排练收据；前者保留历史范围，当前全工具/拓扑/回收由最新排练约束。

[新收据核对](binding-green.json)与[九项边界](gate-check.json)PASS：四份收据/例外正确、缺收据/错排练/错内核/错协调器/错运行版本/错差异集合均拒绝；旧整体INCOMPLETE排练仍拒绝；内核函数原文变化也拒绝。全程没有prepare、运行root、角色CLI、API、daemon或模型。

冻结采用两步提交：先提交这些元数据和主控的-02运行原件，再由标准prepare生成materials-05，最后提交产物、未签Stage A与静态读回。这样snapshot每个成员都能与完整冻结提交的Git原文逐字节比较。最终材料目录为 `09c-attempt-3-materials-01`，实场Stage A输出为全新 `09c-stage-a-03`；c3两角色P1与preparation全新，不复用第2场身份。整票与第3场实际运行仍INCOMPLETE，未获阶段批准前不启动。
