# T-076-2 真实正例槽2–6审批材料02：显式default

状态：**INCOMPLETE／待本实例批准**。依据主控 #82 和用户answer `20261013T142903Z-ideation-answer-001`，所有Codex会话（含隔离被测worker/reviewer）显式传`-c service_tier="default"`。探针和换执行器证据见[2026-10-13 tier probe](../../../2026-10-13-tier-probe/README.md)。原01材料过期且原样保留；本02重新冻结，模型固定gpt-6.1-sol、xhigh、普通速度。

恢复时重新核对预算仍1/8，读回见[p-review-readback-01.json](p-review-readback-01.json)；没有新的reservation/observation，原01和新02实例根均不存在。周额度用尽即停止保存，不换账号、模型或重试。此轮未复制auth、未写APPROVED.json、未预留新回合。执行worker已续接为s13-t076-2s，launch=`launch-632ff9488406442585d7e3ec1aa6fa35`，同原生会话，日志读回default。

先由主控运行受影响最小检查：

```sh
zsh evidence/2026-10-11-batch13/T-076/card-2/outside-sandbox.sh launch-policy launch-policy-default-01
```

旧01快照分别必须命中TRACER-WORKER-DEFAULT-ARGV、TRACER-REVIEWER-DEFAULT-ARGV（缺显式覆盖）；候选两个场景必须通过；只将default值改priority的变异体必须命中worker默认档断言；原只读变异体仍须命中TRACER-READONLY-ARGV。没有真实模型，非预期错误即停，不重跑8/9/18。此最小阶段尚未执行，不能标动态PASS。

## 1. 真实路径与五回合流程

由实际CLI/后台/Panes/node-pty/Git/SQLite执行，没有受控PTY、伪造原生记录或预填结论。host只在原spawn前逐字核对审批argv及环境，再调用原spawn；每个角色只能启动一次。完整runner为[run_t076_quality_real.py](../../../../workbench/tests/run_t076_quality_real.py)，host为[quality_real_host.ts](../../../../workbench/tests/quality_real_host.ts)。产品源码相比旧01快照仅Panes增加显式default两个argv参数；其他47个源码/hook逐字一致，完整差异由新manifest绑定。

| 槽 | 用途与独立证据 |
| --- | --- |
| 2 | worker首回合按预写角色卡交故意漏bool排除的C1，真实Git提交及B submit；外部oracle预期只在bool-true失败 |
| 3 | 自动ACK1，只确认，不调用工具；等原生task_complete和匹配Stop idle后主控verify，明确oracle_failed，登记自动质量回写 |
| 4 | worker收到⟦门禁 #n⟧的quality-repair，修好、测试、真实提交C2并显式重交，同attempt、原生会话与leader |
| 5 | 自动ACK2，只确认，不调用工具；交付turn仍绑定槽4，等完整结束后主控再次verify，重跑机械串 |
| 6 | C2的新只读reviewer独立审查，完整结论经Stop→B→relay绑定C2；可合并才进入主控评分待办，需修复即保存并停 |

没有自动run提前触发verify；外部runner在两个ACK边界后分别调用唯一verify入口。夹具含独立B与主控推进host.txt得到G，worker只能改src/clamp.py；集成后要求M父提交精确为G、C2。独立oracle用合同的11组字面边界/非法类型预期，不从模型或实现生成答案；项目规则为注册时冻结的syntax-only AST检查。C1人为保留缺口是PLAN §9已批准的失败触发，不代表首次交付合规。

Panes现有turn_limit按该daemon全部窗格累计，故配置和两个启动记录都为5；不向reviewers配置塞入未声明的turn_limit覆盖。外部断言要求worker恰为4回合、reviewer恰为1；没有宣称产品按窗格单独限4或1。超出当前worker等待边界即停，最终按原生记录重新计数。没有其他输入、ACK、纠格式或修复授权；槽7/8仍未分配。

## 2. 完整argv、home及动态值

| 项目 | 精确值 |
| --- | --- |
| 实例根（运行前必须不存在） | `/private/tmp/a2a-t076-real-delivery-02` |
| 唯一信任的Git夹具根 | `/private/tmp/a2a-t076-real-delivery-02/repo` |
| worker CODEX_HOME | `/private/tmp/a2a-t076-real-delivery-02/worker-home` |
| reviewer CODEX_HOME | `/private/tmp/a2a-t076-real-delivery-02/reviewer-home` |
| state | `/private/tmp/a2a-t076-real-delivery-02/state` |
| 固定CLI | `/private/tmp/a2a-t076-real-delivery-02/source/workbench/src/gates/cli.ts` |
| Codex | `/Users/luckye/.codex/packages/standalone/releases/0.162.1-aarch64-apple-darwin/bin/codex` |
| Node | `/opt/homebrew/Cellar/node/26.5.0/bin/node` |
| 任务／规格 | T-076-22／T-076 ready_rev=1 |

[launch-policy.json](real-delivery-02/launch-policy.json)包含两个完整argv数组；[worker-argv.txt](real-delivery-02/worker-argv.txt)、[reviewer-argv.txt](real-delivery-02/reviewer-argv.txt)是无省略的shell引用版本。共用`--no-daemon --no-alt-screen -a never -m gpt-6.1-sol`、xhigh、**`-c service_tier="default"`**、关闭更新/通知/工具网络、三个hook和`--dangerously-bypass-hook-trust`。worker的-C为`.../state/worktrees/${ATTEMPT_ID}`、sandbox=workspace-write；reviewer的-C为`.../state/verification/review-${REVIEW_ID}`、sandbox=read-only。显式覆盖也用于隔离home；记录requested tier=default，不当作供应商实际tier证明。

唯一动态argv值是原产品生成的ATTEMPT_ID、REVIEW_ID、各自LAUNCH_ID，均fresh UUID4。审批涵盖完整数组及这三个绑定规则，不预造ID；真实spawn前从本次env展开，核对原record.argv、shell argv、角色、沙箱、home、tier及Git环境，保存两个launch-*-before-spawn.json。任何不符或同角色第二次spawn均拒绝。

shell精确/bin/zsh，argv为`["-f","-i","-c", shellQuote(完整Codex argv) + "; exec /bin/zsh -f -i"]`。两个home各只复制auth.json（0600），分别新建仅一个repo trust条目的config；不复制用户配置、hook、插件或历史。worker另新建且仅有[worker.rules](real-delivery-02/worker.rules)中的两条git add/git commit规则；reviewer无rules、无Git写授权，不复用P-review02的home或会话。

## 3. 三个会话hook与Git尾注hook

两角色分别在UserPromptSubmit、Stop、PermissionRequest安装同一command，timeout=10；LAUNCH_ID替换为该角色本次launch：

```sh
'/opt/homebrew/Cellar/node/26.5.0/bin/node' '/private/tmp/a2a-t076-real-delivery-02/source/workbench/src/gates/cli.ts' '--state' '/private/tmp/a2a-t076-real-delivery-02/state' 'signal' '--launch' '${LAUNCH_ID}'
```

完整inline值（两个argv数组中三个事件分别展开，无省略）：

```text
[{hooks=[{type="command",command="'/opt/homebrew/Cellar/node/26.5.0/bin/node' '/private/tmp/a2a-t076-real-delivery-02/source/workbench/src/gates/cli.ts' '--state' '/private/tmp/a2a-t076-real-delivery-02/state' 'signal' '--launch' '${LAUNCH_ID}'",timeout=10}]}]
```

worker额外会话环境精确为：

```text
GIT_CONFIG_COUNT=1
GIT_CONFIG_KEY_0=core.hooksPath
GIT_CONFIG_VALUE_0=/private/tmp/a2a-t076-real-delivery-02/source/workbench/hooks/
```

Git在两次独立commit -m时调用完整hook路径`/private/tmp/a2a-t076-real-delivery-02/source/workbench/hooks/prepare-commit-msg <本次Git生成的提交消息文件路径> message`。消息路径是Git本次生成的参数，不可在创建前伪造；hook正文为冻结的hook.py，shebang=`/usr/bin/env python3`，按启动记录PATH解析。其他Git hook别名同样是冻结的hook.py。当前只读检查global core.hooksPath为空；启动脚本还在自建repo中检查有效core.hooksPath必须未设置，否则在复制凭据前停止，避免forward未批准hook。夹具Git init忽略全局/系统配置，只含默认sample hook；不写Git配置或用户全局目录。reviewer无GIT_CONFIG_*。

尾注从该worker的最新原生root turn读取实际model/effort；9项Task/Attempt/Session/Role/Tool/Model/Effort/Native-Session/Launch都在C1/C2消息中逐字读回，要求与本次worker身份一致，Model=gpt-6.1-sol、Effort=xhigh。不能用requested环境代替原生事实。[WORKER.md](real-delivery-02/WORKER.md)和[REVIEWER.md](real-delivery-02/REVIEWER.md)均完整冻结；worker沿原B文件CLI，reviewer最终完整JSON沿Stop自动转交。

## 4. 评分由主控在看到结果后填写

审查可合并并idle回收后，先做一次零模型的缺分反例：integrate不带score-file，必须score_required且Git仍G。然后保存`outside-real-delivery-02/ready-for-score.json`，打印`boundary=awaiting_executor_score`，等待最多300秒。主控读该文件及review/gate证据后，才向同目录写`executor-score.json`，包含result=通过、boundary_discipline、boundary_reason、engineering_taste、engineering_reason、notes，数字与理由由主控判断；runner不创建或预填评分。

写分须一次完整落盘（可临时文件后rename），不能部分写入。runner确认候选仍C2，通过唯一integrate --score-file推进Git，读取仅一条score_recorded，核对delivery_rounds=2、completion拒绝=1、其他六类=0、human_interventions=0及worker来源；最后reclaim原worker。未提供评分、非法分或候选变化即保存并停，不集成或猜分。主控执行时保持runner运行，收到上述boundary后填写，不另起模型回合。

## 5. 停止、预算与清理

启动就绪15秒、前台身份每次90秒、每个worker边界和reviewer期限600秒，评分期限300秒。原生结构化error、pane失败、permission_wait、协议unknown、错误候选/身份、超额turn、ACK调用工具、审查需修复或不可核对结果都停止，不追加输入、换账号、模型或权限。主控确认周额度耗尽时立即停止该runner；finally保存现场并只停止本实例的后台。

启动前预算账须只有P-review槽1的reservation/observation（readback审计不计新回合）。本实例预留5，计划累计6/8；实际数由退出后原生记录分角色重新核对。失败/未知预留不自动释放、复用或重跑，交主控审计；槽7/8不得自动调用。

清理：保存事件→核对自建daemon PID/root→daemon_stop→等待自建host退出→核对已记录shell/leader/子进程PID退出→归档静止库及两份原生sessions→删除两个完整CODEX_HOME→只归档明确的repo/state/B请求目录。退出未确认则保留home报BLOCKED，交主控核对；不按名称杀进程，不停正式工作台。auth不进日志/tar/Git；>5MB输出压缩，压缩后仍超大则报告归档要求，不直接提交。所有退出、事件、候选、评分及失败原样保留。

## 6. 批准与执行入口

请在最小检查通过后批准完整两份argv（含显式default）、三个动态身份绑定、每会话三个hook、worker两条Git规则与冻结尾注hook、五回合、评分待办及上述清理。当前没有APPROVED.json。批准后由主控写入`real-delivery-02/APPROVED.json`：

```json
{"approved":true,"approved_by":"executor","policy":"T076-2-real-delivery-02","slots":[2,3,4,5,6],"root_turn_limit":5,"decision_ref":"实际本次批准引用"}
```

由主控执行一次：

```sh
zsh evidence/2026-10-11-batch13/T-076/card-2/outside-sandbox.sh real-delivery real-delivery-02
```

固定根/输出已存在、审批字节改变、已有额外budget reservation都拒绝；没有兜底重试。材料与源码快照在real-delivery-02/，静态准备命令见RESULTS；本轮只交审批材料与可运行脚本，未执行新真实回合。

[本02静态收据](real-delivery-02-preparation-01/run.json)PASS：121个冻结文件，47个产品源码/hook逐字匹配旧01，Panes仅增加批准的default参数；未变oracle沿用字节一致的原控制证据，未重跑。原01检查只证明原01字节，不能替本02启动行为背书。静态检查不能替代最小阶段或本实例端到端结果。
