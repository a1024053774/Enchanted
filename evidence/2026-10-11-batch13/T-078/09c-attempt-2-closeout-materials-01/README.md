# 09C 第 2 场回收待批材料

状态：**材料已生成；回收 BLOCKED／未运行**。原拓扑检查报了未知后代；本轮没有扩大受管集合，不能先略过它停机。先运行 `00-PROBE-COMMAND.txt`，由主控核对原 ps/argv/PPID链/时间与角色工具日志；只有严格检查恢复通过或证据支持的最小修复经批准后，才逐步执行以下材料。当前不能把本目录当成已获准的一键回收脚本。

原 root `/private/tmp/t078-2-09c-run-iznfrv18`；daemon **93964**，target shell/leader **94061/94063**，API ideation/executor **93961/93962**，ideation shell/CLI **94466/94467**，executor shell/CLI **95221/95222**。全部 PID/argv/lstart、原图、claim、launch 取自原 owner，不从本次 ps 重新采纳。`capture-owner.json` 仅在原 evidence_trees 追加外层 timed-01、诊断选行/clock原件、未来 current-topology-01；其他字段逐项相等，原 owner/identity_receipt 不改。源码仍为原冻结 `1dfa09207b34c7ccadfe81cb92a46338fa619526`，非本次材料提交。

1. 主控核对并签 `cleanup-approval.json`（approved_by/approval_ref 为空），再运行 `01-DRY-RUN-COMMAND.txt`。沿用同一标准 retention 的九身份双读与完整图；零归档、零stop/信号、零删除。若有未知/改变进程立即BLOCKED，不能把probe里看到的进程随意写入原owner。
2. `02-CAPTURE-COMMAND.txt`：标准 `t078_raw_retention.py --mode capture`，活场景一致只读事务导出、全部HTTP/hook含失败/不完整项、现有证据树、目标baseline/received和本次clock/诊断。外置 staging `/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078/09c-attempt-2-capture-01/`；tar 为同基址 `09c-attempt-2-raw-01/scene.tar.gz`。按范围脱敏，不复制HOME、认证文件、环境或原SQLite/WAL。逐成员类型/字节读回，并核对活原件集合/字节稳定；仍增长即停，不先停服务换取稳定。
3. `03-TAR-READBACK-COMMAND.txt`：独立只读tar重数POST/roots/PermissionRequest/unfinished，输出 `09c-attempt-2-raw-readback-01/readback.json`，签字为空。按逐POST原件计数，不用日志行数代替。当前只读meta观察为POST **3/11**，最终以捕获tar原件为准，不把它改为计划7/1。
4. 按 `04-REVIEW-CHECKLIST.md` 独立审阅失败原件与凭据扫描。以 `failed-scene-review-template.json` 为字段草稿，**另写** `09c-attempt-2-raw-readback-01/failed-scene-review.json`；填实际 counts，只有保留/关联检查通过才记status PASS，scene_status始终INCOMPLETE。主控审阅后分别签该文件与readback.json；模板不签、不覆盖为结果。
5. `05-SAVE-MANIFEST-COMMAND.txt`：独占保存bundle清单/逐原件archive指针入口；HTTP/hook payload留外置盘。
6. `06-FINISH-COMMAND.txt`：先核对已签的失败审阅/独立重数/本场root、source、原stop/request，再调用未改标准finish。它再次校验归档全成员与源字节稳定、原九身份/图；独占写shutdown-intent后才认证daemon_stop→panes.shutdown，正常关两角色/目标。两只API各一次SIGTERM、确认九进程退出；停后只验文件/归档、SQLite读取0，全部通过才删root。不直接给Claude/目标发信号，不动slot，不重复不确定shutdown。

`retain_failed_scene=true` 仅允许显式保留未完成HTTP/hook后回收，不改变本场失败或预算。所有目录都用独占创建；路径已存在即拒绝，不能用新label重做业务或补发Enter。本轮所有命令只写未跑；现阶段唯一可建议主控执行的是**00只读取证**，其余待证据与裁定。
