# A-16 回收待批材料（主控 #349）

**只写命令，未生成实际owner/cleanup批准，未归档、停机或删除。** 根为 `/private/tmp/t078-2-09b-run-z9ov_cco`；源码7a6edbff87df85077b3a05d38f3cfd5654cde9c1。本套复用已冻结的 `prepare-rev2-owner.py` 与 `t078_raw_retention.py`，不另写停机实现，不直接给Claude/target发信号，不清理build slot。

| 原身份来源 | PID（仅原收据预览，未实测当前存活） |
|---|---:|
| Stage A daemon | 34333 |
| Stage A target shell / leader | 34430 / 34433 |
| Stage A ideation / executor API | 34330 / 34331 |
| ideation实际B1 shell / CLI | 36360 / 36361 |
| executor实际B1 shell / CLI | 41345 / 41346 |

完整argv/lstart、PID未复用、进程图与九身份必须由步骤01/03/07在执行当时核对；不能拿这张PID表代替owner收据。任一不符即BLOCKED保留现场，不跳过或盲发信号。

## 主控逐步执行，签字处停下

1. `01-OWNER-COMMAND.txt`：读真实Stage A和两份实际B1 manifest，完整argv/lstart双读、原始五进程及两角色生命周期/进程图核对，通过后写主包owner.json及identity收据；只在隔离root写600权限的fixture脱敏secret inventory，不读用户HOME，不把secret值入Git或tar，不发信号。当前owner不存在。
2. `02-DRAFT-APPROVAL-COMMAND.txt`：只从该真实owner绑定生成本目录cleanup-approval.json，签字留空。核对九PID/完整身份、root、source、target、archive后由主控签；没有脚本代签。此批准带“归档及独立重数先行”条件。
3. `03-DRY-RUN-COMMAND.txt`：只读核对全部身份/拓扑，输出仓内09b-a16-cleanup-01-dry-run；不采集、不归档、不停机、不删除。必须PASS才继续。
4. `04-CAPTURE-COMMAND.txt`：在daemon/角色/API仍活着时，结构脱敏全量HTTP/hook/已列证据树、目标baseline/received和一致只读事务导出的live-rows.json。staging、raw、tar及逐原件pointers全在外置盘；tar生成后逐成员类型/字节读回，失败绝不进入停机。
5. `05-TAR-READBACK-COMMAND.txt`：从tar原件重新计POST、UPS根、PermissionRequest与未结束原件，不信collector汇总。生成仓内09b-a16-raw-readback-01/readback.json，两项签字为空。
6. `06-TAR-VALIDATE-COMMAND.txt`：只读tar/owner/readback，核对17 POST＝6/11、10根＝4/6、7许可＝2/5、无unfinished、目标单Esc，以及停机前行导出中的原stop/request、pending→delivered→I2一次与时点；不打开活SQLite。archive中identity是脱敏版本，核对公开PID/start/roles；完整argv/lstart/图仍由owner-bound停机工具执行前核对。结果写a16-review-check.json。主控检查原件与结果，通过后亲自签readback.json的approved_by/approval_ref。
7. `06B-SAVE-MANIFEST-COMMAND.txt`：停机前保存轻量bundle.archive.json和raw-pointers.archive.json到本目录；不复制raw payload、HOME或secret inventory。外置pointers树为每原件保留单独archive指针，不能仅留这张汇总。
8. `07-FINISH-COMMAND.txt`：先核对步骤06 PASS和readback已签，再调用原finish。原finish会再次逐成员验证tar/staging、源原件集合及字节稳定、九身份/拓扑及签字，持久写独占shutdown-intent之后才认证daemon_stop→panes.shutdown，关闭两Claude/target；随后两只原API各一次SIGTERM、确认九进程退出；最后只查归档/文件及关停尾部，全部通过才删root。

以上每条分开运行，不能把本目录全部命令拼成无审批串行脚本。03仅身份dry-run通过不代表归档已完成；05/06完成也不自动签字。原HTTP/hook有变、更晚输出或tar不一致，07应BLOCKED，不删除root；独占shutdown-intent使未知停机不能换输出重发。无强杀、重启或slot删除计划。

## 外置原件与仓内指针

- tar：`/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078/09b-a16-raw-01/scene.tar.gz`
- 外置capture/staging：同批T-078下 `09b-a16-capture-01/`，包含redacted、capture-result.json和archive-pointers；不把大块raw写入worktree。
- 每原件指针：tar父目录 `pointers/<logical>.archive.json`；HTTP为logical `roles/<role>/http-exchanges/NNNN.*`，hook为 `roles/<role>/hooks/<trace-id>/*`，tar成员统一 `files/<logical>`。
- 顶层原始清单：tar父目录bundle.archive.json；06B保存仓内同名原件及指针索引。里面有实际字节数、成员/映射与source/root绑定，不用哈希替代字节读回。
- 库证据：tar内live-rows.json为停机前的一致事务行导出，不携带SQLite/WAL文件。停机后不运行capture/export、不打开原SQLite。

认证头从未进入HTTP捕获接口。正文中正常的authorization单词保留；结构脱敏只处理真正敏感字段/fixture secret值并记字节映射。原stdout/stderr/失败/unfinished都纳入源集合；本场允许的s11采集拒绝与worker核对器首轮失败保留，不覆盖改判。当前HTTP/hook已完整，cleanup批准的retain_failed_scene=false只禁止强行删未结束现场，不表示丢弃失败材料。

当前本目录所有归档/owner/停机结果均 **INCOMPLETE（未运行）**；只有命令/语法/路径材料可报静态PASS。A16实际业务worker核对见仓根本票的A16-FINAL-READBACK.md，不能把本计划当作已回收。
