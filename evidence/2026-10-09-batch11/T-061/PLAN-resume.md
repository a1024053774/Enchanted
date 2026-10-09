# T-061 恢复计划（2026-10-09，ready_rev 2）

目标：缺 `_meta.tool_name` 时，让完整原生提示中的数字工具名进入既有目录判定。三个已有名字 `a2a_submit`、`a2a_raise`、`synara_e2e_review` 在原授权条件下免确认，其余 113 个目录工具前后逐项一致。

不做：改目录或授权条件、真实模型调用、正式工作台数据与服务、其他 ticket、push 或集成。起点为 worktree `/Users/luckye/Documents/Code/synara-t045`，分支 `a2a-t061`，红态快照 `1ec64d866c6a37985ddfada5f22c39f9fcb15e54`；起始工作树干净。

验收：补第三个名字在 full-access 与显式授权下的红态；同一测试转绿；三个名字的身份、活跃 turn、授权、目录外名字边界反例；同一探针对照全部 116 个名字与两种帧；相关既有套件、fmt:check、lint、typecheck；冻结候选一次 fresh-context 只读审查。

失败方式沿用 PLAN.md：不能解析数字；缺失/撤销 lease、未授权、非活跃/过期 turn、错误 thread/server、停止中、Plan 模式被批准；目录外数字名字或非完整提示被批准；显式字段被文本覆盖；写入持久授权。补第三个已有名字的同类边界。

Ubiquitous language 沿用 CONTEXT.md。Deep modules：在现有 manager 入口修改字符范围，不增加包装或平行解析。Tracer bullet：本票只改解析边界，不引入跨层切片。

旧证据不覆盖；新命令用 run-check-resume.py，收据绑定 ready_rev 2、worker s11-t061b。恢复 brief 指定 Herdr 期交付为提交、RESULTS、终端 DONE 行，不走门禁 submit；没有工作台 attempt/session/fence。不把本地交付当成主控验收或集成。
