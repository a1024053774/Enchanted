---
id: T-045
title: 工作台"用量与限额"显示失败
type: build
status: closed
blocked_by: []
claimed_by: s5-t045
supersedes:
---

## What to build

用户在正式工作台（`~/Library/Application Support/a2a-workbench`）的 Settings → Usage & limits 看到 Codex、Claude、Cursor 均为"Unavailable / Could not reach the … usage endpoint"，而聊天正常。主控核对：本机直接访问 `chatgpt.com/backend-api/wham/usage` 2 秒内返回（401，网络可达）；错误来自 `apps/server/src/providerUsage/providers/codex.ts` 的异常分支，但工作台 `server.log` 没有该警告的细节。查明根因并修复，使 Codex 与 Claude 用量正常显示。

## Acceptance

- [x] 根因有证据（日志、复现命令或源码路径），区分工作台启动环境、凭据读取、网络与上游缺陷。
- [x] 修复后工作台中 Codex、Claude 的用量显示正常（截图），或说明某个 provider 因条款或认证方式本就不提供用量。
- [x] 诊断与验证期间不兑换 refresh token、不改写用户 `~/.codex`、`~/.claude` 凭据；修改上游文件时列清单。

## Resolution

2026-10-09：诊断交付 **PASS**，最终用量显示 **INCOMPLETE**，ticket 保持 open。用户明确“不改变网络配置，如果是这个原因就算了，看看是否有其他原因”，本次据此保留现状，没有产品修复。

正式工作台 `workbench-launch.log` 中 Codex、Claude 的真实异常为出站安全层拒绝保留地址；三个 usage 域名解析到 `198.18.x.x`，命中共享策略的 `198.18.0.0/15` 阻止项。假凭据经真实 batch 入口复现三个不可达 snapshot，socket、刷新、写入、Keychain 调用均为 0；共享源码探针与本地 HTTP 正例通过，移除保留网段规则的临时 mutant 被拒绝；47/47 相关既有测试通过。没有发现第二个导致当前用量报错的已证实原因；DNS 拒绝后的实际认证、TLS、限流和响应格式仍未验证。

还记录了独立的启动器 `status` locale 误拒绝，同一 PID/启动时间的中文、英文 `ps` 文本不同；中文 locale 下完整身份匹配。它不解释用量失败，不在 T-045 扩修。

证据与未验证项见 [RESULTS.md](../../evidence/2026-10-09-batch5/T-045/RESULTS.md)。fork `a2a-t045` 固定于 `28e2f1b4ca6634d4faba9bd921a55a51640407e4`，没有新提交或上游文件改动。真实凭据路径未运行，正式工作台未重启，未取得最终界面通过证据；本交付不代替主控的验收与 integration。


### 2026-10-09 修复交付

执行 `brief-T-045-fix.md` 与主控决定 01 后，离线修复交付 **PASS**，正式工作台显示仍 **INCOMPLETE**，保持 `status: open` 与界面验收复选框未勾选。fork 分支 `a2a-t045` 的独立提交为 `4b64e4cdd43e1e8e4c1f7bfaa2c66776f3985fa8`：共享出站边界只为用量 helper 显式启用的三个固定 HTTPS origins 放行 IPv4 `198.18.0.0/15`，其余主机名/保留地址及普通出站策略不变。

新边界测试在父版本 3 个正例为红，候选 18/18 为绿；同一离线 batch 夹具在父版本被地址策略拒绝，候选三个 provider 均 ok，并保留输入 17/47 的用量值；删除 origin 限制的 mutant 被 5 个反例拒绝。47/47 既有相关用量测试、13/13 共享策略测试、修改文件格式/lint 和 shared/server 包 typecheck 均通过。真实网络、凭据刷新/写入、正式应用重启及 push 均未执行。

改动清单、原始红绿与异常现场、复现命令和未验证项见 [修复 RESULTS.md](../../evidence/2026-10-09-batch5/T-045/fix/RESULTS.md)。主控合并、重启及用户界面确认尚待完成；本提交不代替门禁 acceptance 或 integration。

**主控关闭（2026-10-09，Claude Code）：PASS。** 修复合入 fork `a2a`（`3f274dd`），工作台重启后启动日志不再出现用量端点报错；用户于 2026-10-09 在界面确认用量正常显示（"确认"）。
