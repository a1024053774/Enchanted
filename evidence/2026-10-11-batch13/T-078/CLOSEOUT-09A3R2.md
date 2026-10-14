# 09A-3R2 实跑与清理收尾

2026-10-14，主控 #153／#155／#157。**两场景及两个根的 cleanup 局部 PASS；T-078 整票 INCOMPLETE。** 实际源为 `643d59bfadbf07466ee28d57f471b8ef3d10646f`，材料提交 `dc67ce58b3300503bf31873d7c3c69c8d56b941f`。固定 Claude 2.1.296／Haiku 5.5 low、隔离 HOME、loopback 假 API，真实模型 0。所有窗口操作是 executor 预批的 test-simulated-user，不是用户亲手操作。

[原件读回](closeout-readback-09a3r2/result.json) 23 项 PASS：直接读取两份外置 tar 的 API/hook/PTY 与 SQLite/WAL；数据库只在新临时副本中只读打开，未忽略 WAL、未修改原件。已目视 [clean 空框](p1-materials-09a3r2/continue-esc/electron/cleared-draft.png) 与 [block 拼接阻断](p1-materials-09a3r2-block/continue-esc/electron/blocked-concatenation.png)，与脚本快照和原字节一致。本读回由已知实现的 worker 完成，不是 fresh-context 独立 reviewer。

clean：Esc 的 action/准入/intent/written/退休成立，API1 peer 关闭，active=null 且第二条 held。同窗一次 Control+C 记 control action，输入代次从 1 到 2；13836 highwater 的 PTY 前缀与保存文件一致，编辑区 empty=true，截图只有空白提示符。声明引用 Esc 的中断 seq 88 和当前代次，随后唯一 user_queue_release。API2 末条 user 文本为登记前缀＋nonce2，不含 nonce1；两份 UPS prompt_id 不同，唯一 Stop 的 ID 等于第二 ID，三份实际 hook exit 0，pane_idle 一次、最终 idle。主控执行 cleanup PASS。

block：只保留恢复草稿，不发 Control+C；故意不真实声明引用 Esc seq 88／输入代次 1。实际 UPS2 同时含 nonce1 与 nonce2，原 stdout 是 JSON decision=block，exit 0；只有两个 UPS，无第二 turn_start／Stop，主 Messages 仅 1，无 API 错误。原继续阶段观察 2 秒无 API2，随后归档内也只有请求 1。不把该有界反例外推成一般可靠性。

## 两次清理故障与修复

第一故障保留在 [block cleanup](p1-materials-09a3r2-block/cleanup/result.json)。真实 ps 前几次仍有 48987，最后一次 PID/lstart 不变，comm 从完整路径变成 `(2.1.296)`；旧规则立刻 identity_changed，没有等下一次实际 absence。记录无 stat，不以括号名称证明退出。已先重放实际等待闭包取得两项红态，再修纯生命周期判定：同 PID/lstart 仍是“尚未确认退出”，继续原有有界观察；只有实际 absence 才 PASS，PID/lstart 变更仍 BLOCKED，不据此授予发信号权限。[lifetime 红态](cleanup-lifetime-red-09a3r2/results.json)／[绿态 5/5](cleanup-lifetime-green-09a3r2/results.json) 保留。

第二故障保留在 [cleanup-recovery-153](p1-materials-09a3r2-block/cleanup-recovery-153/result.json)，signals_sent=[]。脚本未固定 ps locale，中文 `三 10月/14 ...` 的四个日期 token 被按五个切列，吃掉 Python 路径，owns_api 实际收到 `-B script root`。主控给出的完整四段 command/owner 原本匹配。先用原文本和实际 probe 闭包 [红态](cleanup-probe-locale-red-154/results.json)，再把 ps 生产端固定 LC_ALL=C／LANG=C，消费端非规范日期直接拒绝，不加多语言 fallback。[同探针 5/5](cleanup-probe-locale-green-154/results.json)，lifetime 5／原 cleanup 6 回归均 PASS，详见 [locale 诊断](CLEANUP-PROBE-LOCALE-154.md)。一般 runner 的 probe 同样固定语言；不是放宽 PID/根/命令检查。

主控 #157 在沙箱外执行 [cleanup-recovery-154](p1-materials-09a3r2-block/cleanup-recovery-154/result.json) PASS：两次读 PID 48954 的相同 lstart 和完整 script/root 后，仅向它发送一次 SIGTERM；实际确认 API 退出以及原 CLI 48987、壳 48986、后台 48977 已退出。根逐成员直接归档外置盘、不跟随符号链接，逐文件字节读回后才删该根；不发送其它信号、不删除 slot。旧两份 BLOCKED 原样保留，不回写为 PASS。

## 归档与保留项

| 原件 | 外置文件 | 字节／成员 | 依据 |
| --- | --- | --- | --- |
| clean fixture | `/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078/p1-materials-09a3r2/cleanup/fixture.tar.gz` | 8,138,071／980 | [20323dd7 manifest](external-archive-20323dd797a64b74b90e9633065b15df.json)，byte_readback=PASS |
| block fixture | `/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078/p1-materials-09a3r2-block/cleanup-recovery-154/fixture.tar.gz` | 8,126,057／970 | recovery-154 的成员 inventory／byte_readback=PASS，worker 读回 API/hook/SQLite/PTY |

原 [3fc9ebfa manifest](external-archive-3fc9ebfa7b8b4183a45aa58f2bd16dff.json) 的 files=[]，没有归档 block 根，不将其作为完整归档证明。现在两个隔离根均不存在。两个专属 slot 仍在外置盘，未删；所有失败、批准、截图、小份原字节、源快照和新收尾清单随提交保存，超 5 MiB 原件留外置盘。

本轮没有新增 CLI／API／后台／窗口／模型启动，worker 没执行外部 ps／信号／删除或 Git 写入。source 修改仅 p1_processes 的清理事实判定、runner 的 ps locale 和测试／证据；业务 src/app/hooks/core/taskCards 不改。新候选独立 reviewer、09B/09C、实际 IME、真登录与整票验收仍 INCOMPLETE；09B/C [计划](PLAN-09BC-01.md) 待审，当前入口 NO_GO，不做材料、不启动、不关闭、不集成、不 push。
