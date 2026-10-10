# T-073-1：红态与环境策略阻塞

状态：**BLOCKED**。T-073 的实现尚未开始；任务卡、启动入口、Git 钩子和打分脚本均未交付，ticket 保持 open，待主控决定并关闭。

依据：T-073 `ready_rev: 1`、本批任务卡；开工时 a2a `main` 为 `5d9f03c669c1ded777524adc76a3f3834ae785cb`。执行会话为 Herdr `s12-t073` / pane `wF:p21`，原生会话 `01a12758-be0b-7e63-aa49-1c6beeb3ed6d`。本卡没有给出门禁 task/attempt/fence 身份，本文记录卡片执行与诊断，不声称已完成门禁 submit、验收或集成。

## 已取得的证据

1. **红态 PASS**：旧入口 `herdr agent start --kind codex` 启动真实交互 Codex，在隔离夹具提交 `63b5b67d9fe1e66e888814e7a5d2e1f9777ac6e2`。`red02/git-message.txt` 只有 `T073 baseline`，没有 `A2A-*`。完整实际提交号也保存在 `red02/commit.txt`；现场在 `red02/fixture.tar.gz`，原夹具保留于 `/private/tmp/a2a-t073-xt7u56z4`。
2. **环境策略前提 NO_GO**：启动 argv 没有 `shell_environment_policy` 覆盖；隔离配置只有该夹具真实路径的信任项，规则只有 git add/commit 两条 allow。pane shell 的无害 `T073_PROBE_KEY=harmless-sentinel` 出现在真实 Codex `exec_command` 的子进程环境中，见 `red02/env-probe.json`。这与卡片及 ticket 关于该版本“默认滤掉名称含 KEY”的前提相反。没有为取得红态而暗中启用过滤。
3. **现场保留与清理 PASS**：`red01` 是启动路径问题，未发生模型 turn，信任确认界面未获批准；取消后关闭本探针 pane，并删除该次隔离 home。`red02` 确认 agent 为 done 且提交已存在后才关闭自己的 pane，原生记录复制到本机 `red02/sessions/`（Git 忽略），删除整个隔离 home。两次夹具与命令证据保留，不覆盖失败。
4. **项目状态 PASS**：开工和阻塞收尾运行 `project_map.py status`，均为 0 problems、0 stale living docs；原始收尾输出见 `status-blocked.txt`。

CLI：Codex `0.162.1`、Herdr 客户端及 server `0.9.3`，没有升级或重启 server。真实调用请求 `gpt-6.1-sol`、xhigh、`service_tier="fast"`、`check_for_update_on_startup=false`；仅证明启动请求，未证明供应商实际服务 tier。

实际用量：`red01` 0 个模型 turn，`red02` 1 个 turn。原生事件汇总见 `red02/usage.json`：累计 input 104,163（cached input 94,464）、output 470（含 reasoning 132）、total 104,633。这是 rollout 的累计用量，不是单次输入长度，也没有据此换算费用。

## 决定入口与最小选项

已发送 blocking issue `20261010T194745Z-worker:s12-t073-issue-001`，正文在 `issue-default-environment.md`。任务卡明确要求遇到 spec 与实际行为不符先停下，交主控写 needs-decision，因此未继续实现。

建议修订证据条件：启动入口仍显式设置每会话环境策略、窄放行 `GIT_CONFIG_KEY_0`；反事实使用“显式开启过滤时变量缺失；窄放行后保留”，不再声称该版本默认过滤。另一选择是保留原卡并维持 BLOCKED。未擅自修改卡片、ticket 验收或 dated spec。

旁证：[官方配置参考](https://learn.chatgpt.com/docs/config-file/config-reference)（2026-10-10 查询）说明 `ignore_default_excludes` 默认 `true`，默认跳过名称含 KEY/SECRET/TOKEN 的自动过滤。结论的主要依据仍为本机实际探针。

## 失败方式清单

| Ticket 的失败方式 | 本次处理与剩余状态 |
| --- | --- |
| Codex 默认过滤 `GIT_CONFIG_KEY_0` | 无害 KEY 变量默认保留，原前提被反例推翻；需主控修订证据条件。没有设置 `GIT_CONFIG_KEY_0` 的红绿实测尚未运行。 |
| Git 元数据沙箱与钩子读写 | 仅复制 git add/commit 两条规则；旧入口真实提交成功。新入口与钩子读写未测。 |
| 无原有钩子或原钩子失败 | 未实现、未测；不得写为通过。 |
| 手动 unset 会话变量 | 未实现、未测；后续须说明拒绝或由门禁检出缺尾注的边界。 |
| amend、rebase、merge | 未实现、未测。 |
| 打分并发追加与损坏文件 | 未实现、未测。 |

独立审查：未运行。没有实现候选；不把诊断报告当作完成候选消耗交付前的一次 fresh-context 审查。

## 重放与产物

所有实际 argv、stdout、stderr、exit code 在各标签的 `commands.jsonl`。先使用全新标签；不可覆盖 `red01`、`red02`。以下流程会调用真实模型一次，必须仍处在批准的任务范围内：

```sh
python3 -B evidence/2026-10-10-batch12/T-073/real-probe.py prepare NEW_LABEL
python3 -B evidence/2026-10-10-batch12/T-073/real-probe.py start-red NEW_LABEL
cp evidence/2026-10-10-batch12/T-073/red02/prompt.txt evidence/2026-10-10-batch12/T-073/NEW_LABEL/prompt.txt
python3 -B evidence/2026-10-10-batch12/T-073/real-probe.py prompt NEW_LABEL
python3 -B evidence/2026-10-10-batch12/T-073/real-probe.py inspect NEW_LABEL
```

以新标签 `state.json` 中实际夹具路径执行 `git -C FIXTURE log -1 --format=%B`、`git -C FIXTURE rev-parse HEAD`，读取 `FIXTURE/env-probe.json`，取得消息、版本与环境输出；再将其记录与夹具归档保存。agent done/idle 且提交已存在后执行：

```sh
python3 -B evidence/2026-10-10-batch12/T-073/real-probe.py finish NEW_LABEL
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
```

本次只修改本卡证据及本 ticket Resolution；`scripts/dispatch` 保持原状。探针的派发也经现有 dispatch，追加到了主控的 `dispatch.jsonl`；该主控日志不计入候选。开工前已有 `evidence/2026-10-09-batch11/controller-poll.log` 改动，保留不提交。T-074 证据与本批主控日志不属于本 worker 的交付。
