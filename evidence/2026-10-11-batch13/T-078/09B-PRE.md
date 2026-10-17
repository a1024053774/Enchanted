# 09B 前置产品切片：角色隔离目录与 6 根预算

主控 #187 已审 09B 计划方向，预算 I=4/6、E=6/11、合计17、模型0；本轮只做产品前置，不实现双角色业务驱动、不启动 CLI/API/目标。

## 红态与绿态

[红态](09b-profile-red-02/results.json) 保存了修改前真实 `claudeLaunch` 构造：两个 preset 共享 `HOME`、`CLAUDE_CONFIG_DIR`、`TMPDIR`、`ZDOTDIR`、`A2A_REQUEST_DIR`、`A2A_HOOK_TRACE_DIR` 六个路径，第三根 `turn_limit=3` 被 `invalid_controller_turn_limit` 拒绝；launch NO_GO，未启动服务。

修改后 [绿态](09b-profile-green-01/results.json) 通过真实生产构造器：两个 preset 由同一 broker/state/repo 下的 `roles/<preset>/` 推导各自 home/config/tmp/shell/requests/hooks/user-data/debug，路径集合无交集；`turn_limit=3` 接受，`turn_limit=7` 拒绝。共用 state/repo 与角色目录边界保留，旧 root 级共享路径不再由生成器创建或作为 fallback。

`panes.ts` 的 Claude hook 信号现在接受 1～6 根；超出 manifest 的 7 根仍在 `claudeLaunch` 拒绝。P1 生成器和续跑脚本已同步角色目录、角色 config/settings、hook 读回与 user-data。已运行的单角色 slice1 relay22、permission3、entry6、empty-declaration17 回归均 PASS。

附加构造回归：profile08、auth、role prompt、两回合预算均 PASS；六回合上限通过，七回合拒绝。所有检查无 CLI/API/UI/model。

## 允许范围

本切片修改 `claudeLaunch.ts`、`panes.ts`、P1 生成／续跑脚本及相关 profile tests。没有改变 relay、core、daemon、caller 或 Stop 业务；没有共享目录兼容分支；根路径仍要求 `/private/tmp/t078-2-*`、state/repo 为该 root 的真实路径，角色目录也必须是真实目录。

## 后续交接

交 [前置提交脚本](commit-09b-pre.sh)。脚本只冻结本切片、红绿证据与回归结果，保护启动身份、HEAD、暂存区及 allowlist；不启动任何服务。提交后再实现共库双角色 fake API／阶段驱动／独立 oracle，所有请求绑定实际登记正文、实际 stop/request ID 与全局 dispatch.seq；先红后绿，另交可执行 launch 包审阅。

当前双角色材料仍是 plan-review，launch NO_GO；operator 不代发 send/stop/ack，09B/09C 实跑与独立 reviewer 仍 INCOMPLETE。
