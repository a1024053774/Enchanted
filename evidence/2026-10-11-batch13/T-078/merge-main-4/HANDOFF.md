# 主控 #340/#341：合并后的复验和两场冻结

冲突取舍见 RESOLUTION.md。合并提交 43d085c5d，父为 acf8b8a3f 与 main 6d85482ff；完整值从 Git 读取于 source-binding.json。T-090 的产品修改原样保留，worker 没再改 core.ts。后续 source revision 还包含本轮测试工具/材料生成器适配，冻结包记录实际提交号及祖先关系。

## 回归交主控沙箱外运行

确切命令见 REGRESSION-COMMANDS.txt；输出目录必须全新。worker本轮**不运行**任何组，也不把此前工具排练当合并后 PASS。

1. review-followup-regressions-02：原 coop 8、recovery 9、run 18、CAS 1、cards 15，方法身份不变；然后 fence/CAS/lock 三个坏 core 分别必须被原业务断言检出（子用例 exit1、failure>0、errors/skips0，并确认实际加载坏 core），协调器才判反例 PASS。修正原 F4 runner 对 dedd4f66 的写死校验，改按新的 business_revision/source revision 核对，未改原业务断言/期限。
2. merge-main-4-t078-regressions-01：pending/online/ambiguous/controller/inbox/input 等11组、startup领域候选15项及M5、startup真实入口候选14项及M5、worker收件箱14项。startup每键后必须刷新原条目仍queued、无delivered历史、无I2，直到初始release。

T-090 issue 20261016T162759Z 记录整组时序/原短期限偶发 error，三版本单例对照 PASS。它不是自动重试/加长原期限/忽略 error 的授权。任何首次失败或期限超限就 INCOMPLETE、保留现场、停止本脚本；不能说“已知偶发”而继续冒称整组 PASS。host ready 的完整写入后发布已经通过本次合并进入两个宿主；operator 引导/失败日志仍保留。

## 新场景按顺序，不并发启动

A-16 在 09b-a16-materials-01；09C 在 09c-materials-01。两场共用标准 prepare、真实 Stage A runner、角色启动/逐屏工具和唯一假 API 服务；通过显式 scene 区分预算，不复制材料格式或借用 A15 的 root/PID/launch。两份 Stage A 都是未签、NO_GO，且 runner 在建 root/进程前要求上述两份当前源码回归收据 PASS。回归尚未运行时可以审静态包，不能据此启动。

Stage A 只做卡片真实入口预检、假 API/daemon 脱离进程组启动、真实目标 dispatch/claim、原始五PID完整argv/lstart双读，停在 READY_FOR_APPROVAL。无角色CLI、供应商模型0。static root 只是待复制的文件夹具，不是实际场景 root。首次运行的真实 root、claim、五PID和source revision只能从新readiness填入。

ROLE-MATERIAL-COMMANDS 的每条只写文件。新角色材料自带 B1 未签批准、dry-run/real 命令、bind-launch、六个逐屏键的未签批准、读屏-02重读办法、后续阶段独立批准及命令。实际 launch label 从成功 B1 结果读取，不硬编码旧label。B1 plan 为 security-notice + 完整原文；s7 实际按键 purpose 是 onboarding-notice。两者不同职责，不能互相替换。

**A-16**：ideation B1/onboarding/manual/0POST → I1分步到许可屏、完整核对后一次Enter → stop pending/零反馈 → executor B1/onboarding（每键原收据queued且业务0）→ 先arm原I2 → E1初始release → turn_submitted/delivered → 原I2恰一次 → E1/E2/E3 → E4与I3的实际根 → I4 → E5/E6。只执行实际 gate/inbox 自动根，不新增确认根。I2时点仍如实归于主控#299解释，不称用户逐字批准该时点。原protocol逐字不变，I4根/6POST、E6/11，总17、七许可。

**09C**：ideation与executor依次完成B1/onboarding/manual/0POST，再从两个实际B1 bind-launch和新Stage A生成owner（只读核对，不停止）。确认两者初始放行后才C-I1；C-E1是实际stop唤醒的一根/一个held POST，无ack。C-I2真实提前stop必须被拒且目标零增量；C-I3从真实早拒绝反馈产生，尽早备好权限原屏与逐项签字模板，>120000ms且观察elapsed≥120100ms才允许一个条件Enter，开始截止130秒、整场≤150秒。C-I4只确认真实成功反馈，C-E1中性结束。总I4根/7POST、E1/1，八POST、三许可、模型0。C-I3屏幕/命令/stop/目标/native/window/代次任一不符，零键INCOMPLETE；未知写入不得重复。被批准的持续停止要求须显式写在原C-I1批准里，demand模式只把实际stop ID与该已签要求关联，不发送业务动作。

Tracer bullet 沿实际输入→工具请求→Stop/relay→收据，不新增operator业务入口；Deep modules 复用两套既有 driver/原件回收器，不以包装返回READY替代动作；Ubiquitous language 区分queued请求、pending/queued/delivered投递和control action。

## 原件与回收

两场都从第一POST/第一hook开始留全量文件。HttpExchange在验证前记录实际POST与所有成功/409/未完成响应，hookTrace保留原stdin/started/finished等；使用严格分页读屏，并保留完整原屏、签字件、action/intent/written。

prepare-rev2-owner.py 只在真实Stage A/B1后绑定原PID/argv/lstart/claim/两份manifest，不编attempt/null，不启动或发信号；数据生成器的参数是实际目录。随后用t078_raw_retention执行只读dry-run、停机前采集/脱敏/一致只读库行导出、外置逐成员字节读回、独立方签原件读回，再正常daemon_stop/panes.shutdown和两API各一次SIGTERM。停机后不读SQLite；任何新/变hook/POST/finished阻止删root。slot单列，不删。

外置目录分别 `/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078/09b-a16-raw-01/scene.tar.gz` 与 `09c-raw-01/scene.tar.gz`；实际capture输出含每原件archive指针。主控从原件独立重数17/8 POST、10/5根、7/3许可及真实因果，不以collector summary抵消F1。C时钟证据的created_at不重写，目标只一次Esc且存活，不能用cleanup的停机动作充当业务中断。

三窗格移T091、真登录移T092；系统IME本轮未验证INCOMPLETE。这里不启动任何真实登录或模型。
