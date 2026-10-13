# T-076-2 P-review槽1审批材料02：普通速度

状态：**INCOMPLETE／待实例批准**，真实0/8。依据主控 #76 转述构思主控 answer `20261012T015257Z-ideation-answer-001`，用户原话“全继续，不用 fast了，用 6.1sol 普通速度”。本实例使用gpt-6.1-sol、xhigh，argv不传service_tier；01材料、快照和检查收据原样保留，未运行。本worker已续接为s13-t076-2r，launch=`launch-f74f0d2636684448a884b551e0ba1ee2`，模型gpt-6.1-sol，普通速度。

## 1. 先运行一次最小受控复验

```sh
zsh evidence/2026-10-11-batch13/T-076/card-2/outside-sandbox.sh launch-policy launch-policy-01
```

阶段顺序：旧01产品快照上的worker无Fast断言红态（TRACER-WORKER-NOFAST-ARGV）→旧快照上的reviewer无Fast断言红态（TRACER-REVIEWER-NOFAST-ARGV）→候选这两个场景绿态→只将reviewer沙箱改为workspace-write的变异体在TRACER-READONLY-ARGV失败。测试经真实CLI/后台/Panes/relay/Git/SQLite，以受控PTY及原生输入取得启动记录；没有真实模型、预填passed或重试。第一处非预期失败即停。未重跑完整8/9/18；旧结果继续只绑定legacy-green-06的原字节。

当前产品变化只有：Panes删去Fast参数、启动记录tier为default，dispatch_intent的requested_service_tier为default。其余产品文件逐字匹配legacy-green-06；准确替换及快照清单见[p-review-02/source-manifest.json](p-review-02/source-manifest.json)。新测试同时核对worker/reviewer实际argv与记录，并保留原只读、独立home/session/thread、无Git hook环境检查。此阶段动态结果待执行主控运行，不能先称PASS。

[静态准备检查](launch-policy-preparation-01.json)PASS：119个冻结文件、46个未改产品文件、2个仅含批准tier替换的产品文件；argv/hook政策、语法、编码、地图检查通过，无>5MB文件。未启动模型或复制auth。

## 2. 固定实例与完整argv

| 项目 | 精确值 |
| --- | --- |
| 实例根（运行前必须不存在） | `/private/tmp/a2a-t076-p-review-02` |
| 唯一信任的夹具Git根 | `/private/tmp/a2a-t076-p-review-02/repo` |
| reviewer CODEX_HOME | `/private/tmp/a2a-t076-p-review-02/reviewer-home` |
| 空worker占位home（不启动worker、不复制auth） | `/private/tmp/a2a-t076-p-review-02/unused-worker-home` |
| state | `/private/tmp/a2a-t076-p-review-02/state` |
| 冻结CLI | `/private/tmp/a2a-t076-p-review-02/source/workbench/src/gates/cli.ts` |
| Codex | `/Users/luckye/.codex/packages/standalone/releases/0.162.1-aarch64-apple-darwin/bin/codex` |
| Node | `/opt/homebrew/Cellar/node/26.5.0/bin/node` |
| 任务／规格绑定 | T-076-21／T-076 ready_rev=1 |

[launch-policy.json](p-review-02/launch-policy.json)为完整argv数组；[argv.txt](p-review-02/argv.txt)为完整shell引用版本，无省略项。它们与01相比删除`-c service_tier="fast"`两个参数，所有实例路径改为02；model=gpt-6.1-sol、effort=xhigh、`-a never`、`--sandbox read-only`、关闭更新、关闭工具网络、三个hook及hook信任参数保留。启动记录requested tier=default，不据此宣称供应商实际tier。

唯一动态argv值仍为REVIEW_ID和LAUNCH_ID：原门禁和Panes分别生成fresh UUID4。审批包括完整数组及这两个绑定替换；host在真实node-pty.spawn前，从本次env展开，逐字比较原record.argv和shell argv，并核对独立home、role及default记录，保存`launch-before-spawn.json`。不符或第二次spawn即拒绝；符合时直接调用原spawn，不提供身份、原生记录、Stop或结论。

shell为`/bin/zsh`，argv为`["-f","-i","-c", shellQuote(完整Codex argv) + "; exec /bin/zsh -f -i"]`。home只复制用户auth.json（0600），新建config仅如下；不复制用户配置、hook、插件、历史或rules，无Git写规则：

```toml
[projects."/private/tmp/a2a-t076-p-review-02/repo"]
trust_level="trusted"
```

## 3. 三个hook的完整命令

UserPromptSubmit、Stop、PermissionRequest分别安装以下相同command，timeout均10秒：

```sh
'/opt/homebrew/Cellar/node/26.5.0/bin/node' '/private/tmp/a2a-t076-p-review-02/source/workbench/src/gates/cli.ts' '--state' '/private/tmp/a2a-t076-p-review-02/state' 'signal' '--launch' '${LAUNCH_ID}'
```

每一项的完整inline值为：

```text
[{hooks=[{type="command",command="'/opt/homebrew/Cellar/node/26.5.0/bin/node' '/private/tmp/a2a-t076-p-review-02/source/workbench/src/gates/cli.ts' '--state' '/private/tmp/a2a-t076-p-review-02/state' 'signal' '--launch' '${LAUNCH_ID}'",timeout=10}]}]
```

reviewer没有GIT_CONFIG_*尾注hook环境。B通道仍要求最终消息为一个完整review_submit JSON，匹配Stop转交完整内容；非法即保存、上报、停止，不剥字段或纠格式重试。

## 4. Sentinel、结论与回合

执行主控通过真实claim/submit/verify准备4行clamp.py候选，独立oracle检查“仅接受int，拒绝bool/其他类型，夹在0–100”。没有真实worker、评分或集成。后台为候选C新开一次真实交互reviewer。审查结论可以独立选“可合并”或“需修复”；后者照实保留清单，不强制通过。

sentinel为自建普通0644文件，固定内容`T076-P-review immutable sentinel\n`。[probe_write.py](p-review-02/probe_write.py)先读合同、源码及sentinel，再只用open('r+b')尝试一次写入；只将EPERM/EACCES判denied，其他错误或成功写入均失败。启动前在单独host-control目录用同脚本证明正常权限下写入成功；不chmod伪装拒绝、不恢复、不换工具重试。

reviewer按[角色卡](p-review-02/ROLE.md)在exec工具逐字执行：

```javascript
const r = await tools.exec_command({cmd:"/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9 -I -B /private/tmp/a2a-t076-p-review-02/probe_write.py",max_output_tokens:1600}); text({p_review_probe:r});
```

外部读取原生custom_tool_call的完整input及唯一call_id，解析同调用完整output JSON和程序stdout JSON，要求一次写入、结构化errno、正确cwd/源码/合同、sentinel不变；不按自然语言含义猜权限生效。命令在启动前被拒而缺少声明的errno证据，也报INCOMPLETE。最终核对原生model/effort/read-only/never、完整B结论绑定同C、idle回收、Git干净、项目ref仍B与probe源码未变。

只预留槽1，1个主输入，turn_limit=1，无ACK、纠格式或修复回合；槽2–6另批，7–8不分配。启动就绪15秒、确认前台leader90秒、单回合观察600秒；超过期限、permission_wait、unknown、第二个原生turn/session、sentinel改变或不可核对结果均停止保存，不能把等待当追加输入许可。失败/未知调用保守占1槽，预算账追加，已有账时拒绝重跑。

## 5. 清理、批准与执行

保存事件→核对自建daemon PID/root→daemon_stop→等自建host退出→核对已记录shell/leader/子进程PID退出→归档静止库及原生sessions→删除整个reviewer home→只归档明确的repo/state/host-control/B请求文件。auth不进日志、tar或Git；退出不能确认则保留home报BLOCKED，交主控核对，不按名称杀进程。大证据压缩或存外置盘，缺盘不回退。

请在最小受控复验通过后批准02实例的完整argv、两个UUID绑定、三个hook、唯一sentinel负例、单回合预算和清理。当前未写APPROVED.json；01也未获执行批准、未消耗槽位。批准后由执行主控写`p-review-02/APPROVED.json`：

```json
{"approved":true,"approved_by":"executor","policy":"T076-2-P-review-02","slot":1,"root_turn_limit":1,"decision_ref":"实际本次批准引用"}
```

随后由执行主控运行一次：

```sh
zsh evidence/2026-10-11-batch13/T-076/card-2/outside-sandbox.sh p-review p-review-02
```

源码及四份材料与审批归档在启动前逐字核对，不符即停；固定root/输出已存在则拒绝、不覆盖或续用。当前仅交材料与脚本，停下待主控执行最小复验和审批。
