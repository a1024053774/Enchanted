# T-093 正常登录 profile：交付结果

2026-10-17；task T-093，attempt a1，worker s16-t093，ready_rev 1。
受管 session 67f986cc-92e4-4089-9c22-802a1143b645，原生 session 01a14ae2-a3df-7731-a7b0-1b679b3bce95，launch launch-45148b6732394eccab3b21224b238513。
工具 codex-cli 0.163.0，模型配置 gpt-6.1-sol / xhigh；配置不证明实际供应商 tier。

**整票 INCOMPLETE：实现及下列无模型运行检查 PASS，最终冻结候选的独立审查、门禁验收与集成尚未完成。**
不修改 ticket 验收框，不把 Git 提交当作 Gate submit 或 integration 收据。

更新：独立审查 01 对第一次冻结候选 1d4c58b4a 给出 **NO_GO（验收文件缺口）**，报告原文保留。
下文首次交付的 PASS 均是当时运行证据，不提升为新候选的独立审查通过。当前仅修正验收输入与审查驱动的失败保存，产品源码未改；新外部复验与新独立审查仍待完成，见末节。

最新状态（主控 #79）：用户裁定 A 改了 HOME 条件。清单差异已不作通过条件，但所有父／辅助进程的 OS 禁写尚未完成，父子 profile 兼容性必须先实测。当前仍 INCOMPLETE；当前工作快照不是 A 已落地的验收候选，最新入口为 REVIEW-REQUEST-T093-03.md。下面的旧版本状态与“产品未改”说明仅对应各自历史阶段。

再更新（主控 #82）：父进程拒写成立，嵌套 C 已以 exit 71 实测失败。当前改为单层重设计，转发层的上游网络权限边界待明确授权，整票 INCOMPLETE。最新请求为 REVIEW-REQUEST-T093-04.md；不再重复嵌套探针。

当前状态（主控 #83）：F 网络边界已明确，授权阻点已解决。新增平级 profile 边界探针，等待主控在沙箱外实测新组合；产品源码尚未改造，整票 INCOMPLETE。最新入口为 REVIEW-REQUEST-T093-05.md，精确命令脚本为 PROBE-PARALLEL-01.sh。本轮本地只检查语法／纯构造／Mach 符号可用性，没有执行新 OS 探针、读 auth、查询 Security 服务、启动供应商 CLI 或模型。

## 变更与版本

起点 main 为 61786370428c3ec5f894ea60acccf2695d54c2dc。
正常登录仍经过 controller_start、既有 UserPromptSubmit／PermissionRequest／Stop 及同一转交路径。
新增隔离 HOME 的 auth-only 副本、固定版本与生成状态、本地先记后转的转发器、只读事实命令。
转发记录不保存认证头或正文；终端公开字节对凭据变体脱敏，OSC/DCS 负载不公开。
未修改 acceptance、gates、地图或全局配置。

| 版本 | 本轮证据边界 |
| --- | --- |
| 2b6af7ff4260a6a6cc09f63285b75ec8b1b80bbf | probe-10 代码；主控 #72 回传 PASS，供应商 CLI 2.1.302 只连本地假服务 |
| ff625c3718696cf31a7e9fd0d68e84bd2b0442b7 | 首个产品候选，独立工具审查 FAIL：OSC/DCS 负载可泄漏凭据，保留失败结论 |
| fbc84483ed1efd14783131e2fc2a8e55eb5c3774 | 修复控制负载泄漏及夹具多行 paste；新测试拒绝旧候选 |
| 3b2172beba0427fb6eba69024536e0a7812bf7cf | product-chain-03 沙箱外 PASS，完整 daemon/PTY/hook/Stop 和实际 HOME 清单 |

3b2172beb 之后产品源码及全链脚本、C/Python 假 CLI 未改变；只补转发测试的可选原件导出、证据和交付文档。
最终审查对象为包含本结果与审查请求的冻结提交，完整 SHA 由 `T-093 FROZEN <sha>` 交接；差异核对见 freeze-checks-01.json。

## Acceptance 对应证据

| 条件 | 证据与观察 | 状态与边界 |
| --- | --- | --- |
| 红态：main 无正常登录入口，旧入口拒绝非假 API | [profile-red-01.json](profile-red-01.json)：source_equals_main=true；正常登录认证／sandbox／版本合同三项失败，HTTPS 真实地址被旧假 API 入口拒绝；同一构造合同 [profile-green-01.json](profile-green-01.json) 4 项通过 | PASS（有效合同红态）；原红态摘要 INCOMPLETE 和 rc 1 保留，不改写成绿态 |
| 绿态：假上游走完整链、原件对账、隔离根删除、真实 HOME 无差异 | [product-chain-03.json](product-chain-03.json)：controller_start、真实 PTY、实际进程身份、原生 hook／inbox／Stop，唯一哨兵转交一次，反馈完成；received=forwarded=ledger_requests=model_requests=独立上游=2，outcomes=2；隔离根及夹具删除；[实际 HOME 摘要](product-chain-03.host-home.json) 5554→5554，差异 0 | PASS，主控 #73 沙箱外 rc 0。daemon 用合成源 HOME，另核对主控实际 HOME；未启动供应商 CLI，真实模型／真实上游 0 |
| 反例：启动参数混入真实 HOME 路径被标出 | [forwarder-green-03.json](forwarder-green-03.json) 的 counterexamples.home_references：指定 HOME 前缀插入 argv，报告 launch.argv[1]、1 次；禁用引用检查的变异被拒 | PASS，合成路径反例；不把路径引用等同实际读写 |
| 反例：凭据进入证据被扫描命中 | 同报告的 credential_injections：原值／JSON／URL／base64 去重后的各变体均命中（本次 3 个唯一变体，各 1）；临时泄漏文件随后删除；保留证据 4 文件扫描命中 0 | PASS，只用随机合成值；未把反例凭据原值留进证据 |
| 反例：漏记一条被对账抓住 | product-chain-03 真实转发日志删序号 2 后对账失败；另有可复数的 [missing-row 原件](forwarder-original-01/missing-row/requests.jsonl) 与 [事实命令读回](forwarder-recount-01.json)：入口及独立上游 2，原件请求 1，counts_match=false | PASS；模拟丢记录，保留原始完整版本及损坏副本，不覆盖真实通过记录 |
| 凭据不进证据或 Git | product-chain-03 结束时扫描 state 的 10 个文件，命中 0；probe-10 真实凭据只在内存／隔离根，扫描 0、隔离根已删除；新保留转发原件扫描 0，当前 Git index 对本次合成值／变体扫描 0；新增路径无 auth 副本，只有脚本与小型文本证据 | PASS（所列来源与扫描范围）；没有重读真实 auth 做全 Git 历史扫描，不将合成值检查冒称真实凭据全历史检查 |
| 地图 0 problems | freeze-checks-01.json 保存最终 status 输出；未修改地图 | PASS，0 problems、0 stale living docs |

product-chain-03 在运行时读原始 requests.jsonl 并经事实命令重数；该临时夹具已整体删除，因此其原件没有保留。
为便于独立复数，另运行同一生产转发器，保存 [forwarder-original-01/requests.jsonl](forwarder-original-01/requests.jsonl)：两条请求、两条结果，400 后 200，两个独立上游收据，原值／认证头／正文均不入记录。
它是**另一轮转发测试**，不是 product-chain-03 的原件；[forwarder-recount-01.json](forwarder-recount-01.json) 用同一个只读事实入口分别重数完整与漏记副本。
这些四个小文件由事实命令作为输入读取，按 T-088 留仓库；没有将 sqlite、二进制或整套夹具入库。

## probe-10 三条必须保留的边界

1. 供应商 CLI 的通过依赖隔离配置中新建的 `hasCompletedOnboarding` 和唯一当前 cwd 的项目信任状态。这两个是 **2.1.302 内部状态**；正式模式固定该版本，升级须重新核对，不能静默复用。没有从真实 .claude.json 复制状态，也没有自动业务按键。
2. onboarding 预检会直连 `api.anthropic.com/api/hello` 与 `platform.claude.com/v1/oauth/hello`，两个 hello 候选不经过 BASE_URL。正式模式必须准备完成状态，CLI／子进程只允许本地转发端口与精确 daemon Unix socket；官方地址直连被阻断。事实报告单列可见预检迹象；`preflight_observed=false` 仅表示没识别到相应终端输出，不能证明零网络尝试，不能把转发计数外推为全部网络尝试。正例预检字符串与隐藏预检的变异均有检查。
3. probe-10 收到 **2 个** POST /v1/messages（10594／10574 字节），都携带复制的 bearer、假上游都回 400。按主控结论，说明 400 后发生重试；每次 HTTP 接收独立计数，失败与重试都不能合并。转发器自己不重试、不跟随重定向。

以上来源为主控 #72 与 [probe-10.json](probe-10.json)，真实上游 0，凭据扫描 0，实际 HOME 5554→5554、无差异，隔离根删除。
产品全链使用编译的确定性假 CLI，不能取代供应商登录／路由事实；probe-10 也不能替代本次产品 hook／Stop 的实跑。

## 检查、失败保留与复现

- [counterfactuals-04.json](counterfactuals-04.json)：未改对照及 7 种错误候选均按预期区分，含修复前 OSC/DCS 泄漏候选。
- [private-files-green-01.json](private-files-green-01.json)：合成文件 5 项，auth-only、metadata、符号链接与过期凭据。
- [paste-fixture-01.json](paste-fixture-01.json)：实际 C 夹具修复前把多行 paste 拆成两次，修复后一次完整提交。
- [fixture-version-regression-01.json](fixture-version-regression-01.json)：既有版本核对 8 项通过，原缺陷与删除核对的变异均被拒。
- [PRODUCT-REVIEW-01.md](PRODUCT-REVIEW-01.md) 保留旧候选 FAIL；控制负载修复的新反例通过，不补称旧审查通过。首次 counterfactuals-01 的测试解析问题及先前探针失败保留，不覆盖。

只读重数（可在当前沙箱运行，不读 auth、不启动 CLI）：

```sh
node workbench/src/claudeLoginCheck.ts evidence/2026-10-16-batch16/T-093/forwarder-original-01
node workbench/src/claudeLoginCheck.ts evidence/2026-10-16-batch16/T-093/forwarder-original-01/missing-row
```

复现局部检查须选全新输出与原件目录：

```sh
node workbench/tests/test_t093_forwarder.ts /private/tmp/新的摘要.json /private/tmp/新的原件目录
python3 workbench/tests/test_t093_counterfactuals.py /private/tmp/新的反事实.json
```

第一次冻结前，完整链已由主控 #73 执行，rc 0；当时没有新增必须在沙箱外运行的检查。本次审查修正后的外部复验另见末节。
若独立 reviewer 需要复验，必须由主控另选新输出，后台服务脱离调用者进程组：

```sh
python3 workbench/tests/run_t093_login_chain.py --output evidence/2026-10-16-batch16/T-093/product-chain-04.json
```

真实 HOME 清单范围是 .claude、.claude.json、.claude.json.backup、Library/Keychains；只读元数据，不比较 atime，不读正文、不跟随链接、不用校验值，其余 HOME 路径显式排除。
其他会话可能并发写入，所有差异都报告、不推断因果、不自动忽略；本次完整链实际差异为 0。
事实命令只报告事实，不批准或拒绝模型回合；凭据扫描保留结束时的范围和时间，不冒称新扫描。
本票没有运行真实模型回合，合入后仍等用户另说开工；没有可靠性、吞吐或成本收益主张。

冻结后由执行主控安排新的只读 reviewer 与唯一门禁；本结果不代替最终审查、submit 或 integration。

## 独立审查 01 后的验收修正

主控 #77 转交 [independent-review-01.md](independent-review-01.md)，要求修正两处验收证据。该报告未改字，旧 NO_GO 原样保留；没有据此声称产品行为存在缺陷。
代码／驱动修正候选为 c34d71a975b59a0db8c1e97bb40c0f7a94e629d1；相对第一次冻结，workbench/src、完整链脚本及假 CLI 都没有变化。

| 问题 | 红态与修正 | 当前证据和边界 |
| --- | --- | --- |
| 生产凭据变体列表为空后，候选检查跳过全部注入，仅由清理 ENOENT 退出 | [counterfactuals-05-red.json](counterfactuals-05-red.json) 复现：expected_business_assertion 未观察到、fixture_missing_error=true。现在输入由测试自己的原值、JSON、URL、base64、无填充 base64、base64url 构造；检查列表非空、文件确实创建且内容吻合、正命中及每项均执行；公开字节的禁止值也来自测试输入，不用被测枚举器／扫描器作答案 | [forwarder-green-04.json](forwarder-green-04.json) 对照通过；[counterfactuals-07.json](counterfactuals-07.json) 12 项通过。清空生产枚举器命中 `credential injection must be detected`；空场景、跳过循环、取消写入分别命中非空／执行／文件存在的指定 AssertionError，均无 ENOENT |
| 首条请求不记账的原始失败被审查驱动清理断言盖住 | 原审查外置 omit-first-request.stderr 只留下 `private HOME cleanup must finish`，没有结果 JSON；原业务断言保持 INCOMPLETE。新建 EVIDENCE-RECHECK-02.sh，旧审查脚本 01／02 不动。生成驱动保留首个 failure；清理等待明确不观察已记录的 boundaryFailure；清理异常独立写 cleanup_failures，移除清理断言覆盖主失败的路径 | [evidence-recheck-local-02.json](evidence-recheck-local-02.json)：实际生成驱动在 setup 前强制业务与清理双失败，旧式未捕获清理异常会遮盖主失败并被拒；修正版同时保留 primary_business_probe 与 secondary_cleanup_probe。此为 L1 驱动回归，未启动 PTY/auth/ps；真实首条漏记的完整链尚未复跑，INCOMPLETE |

本轮没有修改 reviewer 的 independent-review-01.md 或 REVIEW-OUTSIDE-01／02.sh。新脚本由 worker 派生，修正不代替新的独立审查。
新的反事实还要求具体业务断言，不再仅因存在 AssertionError 或退出非零就记作“清空变体”已被拒绝。首次红态和旧摘要都保留。

已完成的本地命令（输出路径均为首次创建）：

```sh
node workbench/tests/test_t093_forwarder.ts evidence/2026-10-16-batch16/T-093/forwarder-green-04.json
python3 workbench/tests/test_t093_counterfactuals.py evidence/2026-10-16-batch16/T-093/counterfactuals-07.json
bash evidence/2026-10-16-batch16/T-093/EVIDENCE-RECHECK-02.sh /Users/luckye/Documents/Code/a2a-wt-t093 c34d71a975b59a0db8c1e97bb40c0f7a94e629d1 --check-only
```

--check-only 的两个失败优先级进程、三种生成代码语法检查均通过；它不运行真实 PTY、auth helper、ps 或模型，不冒称外部完整链证据。
完整沙箱外命令由主控对**新冻结提交**执行；第二个参数换成最后交接的完整 SHA，省略 --check-only：

```sh
bash evidence/2026-10-16-batch16/T-093/EVIDENCE-RECHECK-02.sh /Users/luckye/Documents/Code/a2a-wt-t093 FULL_FROZEN_SHA
```

脚本自动创建新的 /private/tmp/t093-evidence-02-* 输出，核对 HEAD 与给定 SHA，一次性导出该版本 workbench，不改仓库或全局配置；后台进程脱离调用者进程组。
它先验证失败优先级，再跑未改对照、独立反例对照，最后跑首条漏记、HOME 漏报、空凭据枚举器、计数恒一致四种生产单处变异；空枚举器另跑候选自己的完成检查。
读取 SUMMARY.json 时，首条漏记必须以 independent_upstream_assertion 为主失败；cleanup_failures 与外层 cleanup.json 分开检查。不得用 ENOENT、超时或另一清理错误替代业务拒绝。
真实 HOME 仍只比较四个既定范围的元数据，所有差异保留；凭据只用合成输入，隔离根和夹具按本轮登记收尾，真实 CLI／真实 auth／真实上游／真实模型均为 0。
尚未执行这条完整命令；当前整票 INCOMPLETE，等待该复验结果和新冻结候选的独立审查。新的审查入口见 REVIEW-REQUEST-T093-02.md。

## 用户裁定 A 后：清单仅报告、父层保护事实待定

来源是用户主控 #79、main c06a73179 的 T-093“裁定”节及 20261018T004018Z-ideation-answer-001：验收改为 OS 强制禁写真实 HOME 加一个拒写反例；清单差异照实报告，不作通过条件。worker 不改受限的项目地图或旧审查原文。

已完成的确定部分：生产 facts 的 inventory 标注 pass_condition=false 与裁定来源；完整链检查继续要求差异数据存在，但不要求空列表；外层返回码保留 child 结果，有差异不再改为失败，child 失败也不放行。复验摘要仍保存原始 home_unchanged 信息，但不以它决定结果。扫描、计数、preflight、清理和身份等其他断言没有放宽。

[inventory-policy-red-01.json](inventory-policy-red-01.json) 在旧逻辑上复现“child=0、有差异仍退出 2”；[inventory-policy-green-01.json](inventory-policy-green-01.json) 的四组 child 成功／失败和有／无差异组合均符合新裁定，前后差异元数据完整保留，旧零差异门槛被拒。边界是 L1 分类，元数据和 child 结果由测试提供，不是 OS 拒写证据。

尚未完成的是所有应用进程的 OS guard。逐进程现状与目标 profile、实际 HOME 与合成认证源 HOME 的区别、输出／FD 边界，以及决定性 SDK 兼容性未知均列在 [HOME-GUARD-A-PLAN.md](HOME-GUARD-A-PLAN.md)。当前不能把只限制 CLI 的旧 C profile 说成父进程和全部 helper 已被保护。

先由主控在沙箱外运行小探针（不要覆盖已存在输出）：

```sh
python3 -I -S -B workbench/tests/probe_t093_parent_sandbox.py --output /private/tmp/t093-parent-profile-01.json --source-revision FULL_FROZEN_SHA
```

它在任何应用工作前同 PID exec H，所有实际 helper 继承 H，记录真实 HOME 唯一新文件拒写及文件未出现，并验证更严格子 profile 在 H 后代中是否真能生效。
删规则变异只在合成 HOME 中做，实际 HOME 规则保留；要求真实独占创建、立即删除及指定业务断言失败，创建／删除记录入证据。这个选择避免主动移除真实 HOME 的保护；它不证明实际 HOME 去掉规则后会写入成功。
清单 helper 也在 H 中，仅记录四范围元数据差异，差异不决定通过；采集失败仍保持 INCOMPLETE。

本地 [parent-probe-safety-02.json](parent-probe-safety-02.json) 仅证明合成文件的独占创建／删除、既有文件保护和未禁写情况下的业务拒绝，实际 HOME 尝试 0，OS profile 执行 0。探针语法已检查，未在 worker 沙箱里运行实际沙箱／ps／CLI，也未读 auth、请求升级或跑模型。

若 sandbox-exec 不能在已有 H 的子进程里施加现有 C/R，必须保持 INCOMPLETE 回主控处理，不能移除 CLI 的网络或 Security 限制来冒充成功。
因此之前 EVIDENCE-RECHECK-02 的完整模式现在直接停止，防止无父层保护时对 A 给出 PASS；旧审查 01／02 脚本和全部旧报告保持原文。新小探针的输出回来后，才能完成全进程保护实现和真实链复验。

## 单层重设计：父层拒写已成立，转发权限待裁定

主控 #82 回传 probe rc 2／INCOMPLETE；原件 [parent-profile-01.json](parent-profile-01.json) 已读回留存。
父 PID 60365 在 H 下独占创建真实 HOME 新文件被 errno 1 拒绝，created=false、absent_after=true；两个 inventory helper 继承 H。
子进程 60700 请求第二层 C 失败，exit 71、Operation not permitted、无实际 child 结果；C 不可列为已生效。清单 5555→5555、无差异、pass_condition=false；临时根删除、清理无错误，auth／CLI／模型／网络均 0。

用户已授权凭据复制单独移到业务 profile 之前／之外，且只精确读一次。后续设计不使用嵌套 profile，也不在 C 内重读原始凭据。
但若包括转发器的所有进程都共用一个只允许本地端口 P 的 profile，现有 http/https.request 无法连接真实上游，另端口 U 的假上游也被禁止。
把 F 移为独立受保护树并给予上游网络，是新的额外边界；不能从凭据准备例外自动推导其授权。

[SINGLE-PROFILE-DESIGN-01.md](SINGLE-PROFILE-DESIGN-01.md) 列明最小建议：R 精确凭据准备，C 单层业务树，另一个平级 F 负责先记后转／上游网络；所有阶段仍禁写 HOME，F/C 禁 Security，CLI 不增加直连上游能力。
本设计尚待明确批准，产品未按它修改；[请求 04](REVIEW-REQUEST-T093-04.md) 将该决定交主控／构思主控。
本轮没有新的必须沙箱外运行的命令，不以进一步 probe 代替权限裁定；原审查报告不改。
