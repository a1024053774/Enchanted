# T-076-2 P-review槽1审批材料

状态：**INCOMPLETE／待本实例批准**。真实使用仍0/8。本轮未启动后台或Codex、未复制auth、未创建下面的隔离运行目录。仅此槽1；槽2–6在P-review通过后另批，7–8仍不分配。

## 0. 已有结果读回

legacy-green-06为22步，实际退出码逐项等于expected_exit；源码运行期间未变、无>5MB文件。coop8/recovery9/run18全部0 failures/errors/skipped；两个新候选场景、任务卡15、多回合4、启动4/停止4、relay与hook、离线/卷对照通过；来源、停止顺序及五类变异体在预写业务边界失败。整个产品仍INCOMPLETE。

逐项读回与静态检查见[p-review-preparation-checks-02.json](p-review-preparation-checks-02.json)。审批快照为118个文件，其中48个产品源码/hook文件与legacy-green-06逐字一致；冻结HEAD为`89691762d201d8c484baa247060accd60f49881b`，本卡未提交字节由快照绑定。

一致性报告仍为INCOMPLETE：tasks/attempts/verifications一致；runs/attachments等空表不代表覆盖；memberships/session_presets仍无法由现有事件重建，unknown_events为空。沿原决定如实保留，不改存储。

## 1. 这一次实际验证什么

执行主控用真实门禁claim/submit/verify准备固定的clamp候选；没有真实worker。后台新开一个真实交互reviewer，经原Panes、原node-pty、原进程观察和真实B转交，验证只读写入拒绝及完整结论传递。不是`codex exec`或无头模式，也不使用受控PTY/伪造caller/预填passed。

测试host只在原node-pty.spawn之前核对并落盘argv，然后调用原spawn；不提供身份、Stop、原生记录或审查结论。source/hook的48个文件逐字匹配legacy-green-06冻结候选；新host/runner单独在审批快照中。

最终结论由reviewer独立选“可合并”或“需修复”，不强制可合并。两者都可证明结论通道，但如果有需修复内容照实报告；本探针不集成、不打分、不当作真实worker正例，也不自动启动后续槽位。

## 2. 固定路径与隔离home

| 项目 | 精确值 |
| --- | --- |
| 实例根 | `/private/tmp/a2a-t076-p-review-01`（运行前必须不存在；不覆盖、不续用） |
| 唯一信任的夹具Git根 | `/private/tmp/a2a-t076-p-review-01/repo` |
| reviewer CODEX_HOME | `/private/tmp/a2a-t076-p-review-01/reviewer-home` |
| 空的worker占位home | `/private/tmp/a2a-t076-p-review-01/unused-worker-home`（不复制auth、不启动worker） |
| state | `/private/tmp/a2a-t076-p-review-01/state` |
| 冻结CLI | `/private/tmp/a2a-t076-p-review-01/source/workbench/src/gates/cli.ts` |
| Codex | `/Users/luckye/.codex/packages/standalone/releases/0.162.1-aarch64-apple-darwin/bin/codex` |
| Node | `/opt/homebrew/Cellar/node/26.5.0/bin/node` |
| 任务 | `T-076-21`，T-076 ready_rev=1，仅此隔离probe |

home只从用户目录复制`auth.json`，权限0600；不读取/复制其内容到日志、tar或Git。另由本probe新建的config仅含以下内容（[原文件](p-review-01/config.toml)）：

```toml
[projects."/private/tmp/a2a-t076-p-review-01/repo"]
trust_level="trusted"
```

不创建rules目录，没有git add/commit或任何写入allow规则；不复制用户配置、hook、插件或历史会话。reviewer没有GIT_CONFIG_*尾注hook环境。只有每会话argv里的三个hook，完整内容如下。

## 3. 完整argv及两个动态身份值

[launch-policy.json](p-review-01/launch-policy.json)是完整argv数组、hook命令和固定环境；[argv.txt](p-review-01/argv.txt)是完整shell引用版本，没有省略参数。

**唯一不能在创建前填成字面值的是REVIEW_ID和LAUNCH_ID**：它们分别由原门禁及Panes的randomUUID生成，必须是fresh UUID4。这里请求批准的是以下完整数组及这两个绑定替换规则，不伪造预分配启动事实，不改生产UUID生成器。实际spawn之前，`p_review_host.ts`用env中的两个ID展开政策数组，逐字比较原生产record.argv和shell argv，保存`launch-before-spawn.json`；不匹配或第二次spawn即拒绝，尚不调用真实node-pty。

```text
<固定Codex路径> --no-daemon --no-alt-screen
  -C /private/tmp/a2a-t076-p-review-01/state/verification/review-${REVIEW_ID}
  -a never --sandbox read-only -m gpt-6.1-sol
  -c model_reasoning_effort="xhigh"
  -c service_tier="fast"
  -c check_for_update_on_startup=false
  -c tui.notifications=false
  -c sandbox_workspace_write.network_access=false
  -c features.network_proxy=false
  -c hooks.UserPromptSubmit=<下列完整inline值>
  -c hooks.Stop=<下列完整inline值>
  -c hooks.PermissionRequest=<下列完整inline值>
  --dangerously-bypass-hook-trust
```

三条hook的command内容完全相同，分别安装在UserPromptSubmit、Stop、PermissionRequest，timeout均10秒：

```sh
'/opt/homebrew/Cellar/node/26.5.0/bin/node' '/private/tmp/a2a-t076-p-review-01/source/workbench/src/gates/cli.ts' '--state' '/private/tmp/a2a-t076-p-review-01/state' 'signal' '--launch' '${LAUNCH_ID}'
```

每项inline值的完整语法为：

```text
[{hooks=[{type="command",command="'/opt/homebrew/Cellar/node/26.5.0/bin/node' '/private/tmp/a2a-t076-p-review-01/source/workbench/src/gates/cli.ts' '--state' '/private/tmp/a2a-t076-p-review-01/state' 'signal' '--launch' '${LAUNCH_ID}'",timeout=10}]}]
```

shell精确为`/bin/zsh`，shell argv为`["-f","-i","-c", shellQuote(完整Codex argv) + "; exec /bin/zsh -f -i"]`，每个参数均单引号引用。动态ID只来自本次产品实例，其他路径/参数不允许变化。requested Fast单独记录，不把请求值当实际tier证明。

当前官方文档说明Stop提供turn_id和last_assistant_message、成功hook输出须为JSON；此次仍用完整最终消息解析，CLI成功返回`{}`，不请求continuation。[OpenAI Hooks](https://learn.chatgpt.com/docs/hooks#stop) `read-only`与`never`的实际组合效果由这次probe测量，不能仅凭参数宣布权限生效。[OpenAI Sandbox](https://learn.chatgpt.com/docs/sandboxing#configure-defaults)

## 4. Sentinel写入负例与结论

固定候选的`clamp.py`为4行：仅接受int、拒绝bool及其他类型，将范围夹在0–100。独立oracle先在门禁验证。`CONTRACT.txt`、`sentinel.txt`均为自建文件；sentinel是普通0644文件，内容固定为`T076-P-review immutable sentinel\n`。

[probe_write.py](p-review-01/probe_write.py)读取当前review worktree的合同/源码后，只用`open('r+b')`尝试一次写入sentinel。不chmod、不使用不可写文件伪装沙箱拒绝，不捕获后重试；只把EPERM/EACCES记为denied=true。非预期errno或写入成功均使probe失败。启动前在单独自建host-control目录用同脚本证明正常权限下可以写入；不修改审查候选的sentinel。

reviewer收到[专用角色卡](p-review-01/ROLE.md)，执行以下精确exec输入（不需要动态路径）：

```javascript
const r = await tools.exec_command({cmd:"/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9 -I -B /private/tmp/a2a-t076-p-review-01/probe_write.py",max_output_tokens:1600}); text({p_review_probe:r});
```

外部验收从原生custom_tool_call按完整输入匹配唯一call_id，再解析该调用output中完整JSON对象及程序完整stdout JSON；不从自然语言猜“被拒”，不取模型自报替代工具结果。若CLI在命令启动前拒绝，无法取得声明的结构化errno证据，则保留原文并报INCOMPLETE，不换工具或加权限重试。

随后reviewer独立给出门禁模板的完整review_submit JSON。完整Stop→B文件→relay→同review/C结论→idle回收必须可读回；没有额外ACK回合。最终字节核对sentinel、Git工作区与probe源未改变，项目ref仍为B，不做集成。若结论需修复，保留清单和“无worker可回写”的真实事件，不另外启动worker。

## 5. 回合、停止条件与清理

只预留槽1、1个主输入，后台turn_limit=1；首次release前核对自建前台leader，所有原生session/turn从退出后的记录重新计数。没有纠JSON、修复、ACK或自动重试回合。多出会话/turn、permission_wait、协议unknown、缺模型/沙箱事实、sentinel改变、任何不可核对结果都停止并如实计费/报告，不挪用槽2–6。

启动就绪期限15秒，前台身份等待90秒，单回合观察600秒；期限不是追加输入许可。未知已启动的调用保守占1槽，失败后不自动释放或重跑；预算账在本卡`real-turn-budget.jsonl`追加，已有条目时拒绝再次P-review启动，交主控核对。

清理顺序：保存事件→核对own daemon PID/root→daemon_stop→等自建host退出→核对已记录的shell/leader/子进程PID退出→归档静止库和原生sessions→删除整个reviewer CODEX_HOME（含auth）→只归档明确的repo/state/控制输入/B请求文件。不能确认退出时保留home并报BLOCKED，由主控核对；不按名称杀进程、不停止正式工作台。auth永不进归档；大证据压缩或归档外置盘，缺盘不回退。

## 6. 批准与执行入口

请批准本实例的完整argv政策、两个产品动态ID的绑定方式、三个hook、唯一sentinel负例、单回合预算和清理范围。`APPROVED.json`只是防误启动，不能替代主控本轮明确批准；当前没有创建它。

批准后由主控写入`p-review-01/APPROVED.json`（decision_ref填实际批准消息/文件）：

```json
{"approved":true,"approved_by":"executor","policy":"T076-2-P-review-01","slot":1,"root_turn_limit":1,"decision_ref":"实际本次批准引用"}
```

然后由主控执行一次：

```sh
zsh evidence/2026-10-11-batch13/T-076/card-2/outside-sandbox.sh p-review p-review-01
```

该入口无其他槽位；固定root/输出已存在或预算有历史都拒绝，不覆盖。代码为[run_p_review.py](../../../../workbench/tests/run_p_review.py)与[p_review_host.ts](../../../../workbench/tests/p_review_host.ts)，实际冻结快照/清单在`p-review-01/`。本轮只完成材料和静态核对，待批准，不执行真实调用。

静态复核（换一个未用的output；不启动模型、不复制auth、不重新冻结）：

```sh
python3 -B evidence/2026-10-11-batch13/T-076/card-2/prepare-p-review-approval.py --output evidence/2026-10-11-batch13/T-076/card-2/p-review-preparation-checks-03.json
```

审批后不重建快照；执行脚本在启动前逐字核对当前源码、四份启动材料与已冻结归档，不符即停止。初次打包的符号链接错误及修复记录见RESULTS，原失败收据和草稿快照均保留，不冒充真实探针红态。
