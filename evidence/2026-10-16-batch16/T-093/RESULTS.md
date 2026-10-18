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

当前状态（主控 #83）：F 网络边界已明确，授权阻点已解决。新增平级 profile 边界探针，等待主控在沙箱外实测新组合；产品隔离／转发生命周期尚未改造，整票 INCOMPLETE。最新入口为 REVIEW-REQUEST-T093-05.md，精确命令脚本为 PROBE-PARALLEL-01.sh。初次探针只读审查指出两处 P1，原文保留，已通过权限码数据反例和跨 exec 计时／删计时变异修正。另有上游 URL 配置解析的单行产品修正，纯解析红绿见 upstream-config-red-01.json／upstream-config-green-01.json。本轮未执行新 OS 沙箱探针、读 auth、查询 Security 服务、启动供应商 CLI 或模型。

最新状态（主控 #84）：[parallel-profile-01.json](parallel-profile-01.json) 中各 OS 边界均成立，只有 U 后清单收尾失败，原件仍为 INCOMPLETE。现已去掉该 Node→Python 回 exec，在同一 Python 进程采后清单后再确认关闭；旧 profile() 规则未改。产品已接入独立 R 准备、F 转发、D 清单／清理与单层 C；完整新链和五项变异待沙箱外运行，整票仍 INCOMPLETE。当前交接为 REVIEW-REQUEST-T093-06.md／EVIDENCE-RECHECK-03.sh。以上“尚未改造”文字属于此前快照。

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

## 产品平级 profile 候选 06：实现完成，外验待运行

主控 #84 的旧外验确认：C/F/U/S/M/CLI 子进程禁写真实 HOME、F 越界出站／监听被拒、C 直连假上游被拒、F/U fork 与 Security 被拒、本地配置正例及合成删规则变异均成立。U_closed 已保存，但后清单未得，因此保留原 rc 2、primary_failure=null 及两项 cleanup_failures；不提升为 PASS。主控事后 ps 无残留的转述与 JSON 的观察范围分开。

U 现在用同一个 Python 进程完成前清单、假服务与后清单，后清单成功后才确认 closed；没有改变旧探针 profile() 的 AST。局部测试先重建提前确认的变异，再证明 U_closed_must_include_post_inventory 能拒绝它。JSON ready/closed/stop 在内容完整后原子发布。

产品入口 claudeLoginSession.py 在链外精确读一次原始 auth，只复制 OAuth，生成唯一隔离 HOME 与最小版本绑定状态；启动平级 F/D 后同 PID exec C 中的原 daemon。C 及 hook/Stop 的控制路径保持原样；版本、status、PTY、事实子进程均继承 C。F 的唯一地址／端口由 URL＋显式固定 IPv4 配置，禁 DNS／fallback／其他出站／Security／fork；D 无网络／Security／fork，只收四范围目录/stat，原始清单留在私有根。HOME 禁写覆盖整个 OS 账号 HOME，不用 HOME 环境变量替代，也没有 repo/state/roles 的 HOME 写入例外。

并发 start 的准备会话采用一次性独占消费，落后者不能取得或清理胜者资源。D 区分正常结束、主动取消和根进程失联，对本次登记的 PID/组核对后清理，未确认就保留 INCOMPLETE。C 管理 tmp 与 CLI 私有根分开，结束后的事实命令不应重建已删除的隔离根。当前事实 schema 为 2，原件位置是 forwarder/journal/requests.jsonl。

凭据元数据字段的额外缺口有独立局部红绿：journal-red-01.json 中方法／数值暴露 2 个合成值，journal-green-01.json 为 0 且 JSON 可解析。修正在 F 的写盘边界，不落认证头或请求体。该检查没有监听或请求上游。

局部通过证据：cleanup-local-05.json（U 关闭、提前确认变异、一次合成读取、路径边界、D 正常／取消清理及身份丢失时不发信号；D 的信号为模拟）、once-local-03.json（并发只消费一次、不清理胜者）、facts-local-03.json（四种清单差异／漏记组合不自动授予模型许可）、launch-local-05.json（原 hook/Stop 与单层启动构造）、url-local-03.json（配置解析）、private-files-local-02.json（OAuth 范围／链接／有效期）、oracles-local-02.json（Mach 明确拒绝及跨 exec 截止）。这些不替代新产品 OS 绿态。

最终局部快照补为 cleanup-local-07.json、once-local-05.json、facts-local-05.json、private-files-local-03.json：原始 auth 前的短 D 基线、一次性消费与输入前事实均已接入；新增显式 --preflight 事实模式。局部测试模拟基线子进程／服务计数，未执行新的 OS profile。实际全链必须由主控复验；不据此升级状态。

inventory-race-red-01／green-01 另复现并修正目录在 stat 后、枚举前消失的收尾风险；明确记录 missing／vanished_before_enumeration，保留已见元数据。PermissionError 仍传播，未放宽观测失败。它不证明原 U 一定是这个原因。

完整外验脚本已经准备，命令及逐进程 profile 表在 REVIEW-REQUEST-T093-06.md。绿态使用随机 prompt／inbox 哨兵、真实 PTY/daemon/native hook/Stop、编译假 CLI、独立受保护假上游。逐条对账 F 原件与独立 U 收据；覆盖原三个反例、八个真实 HOME 拒写路径、合成缺失规则的实际创建／立即删除、F 越界连接及 C 绕过 F。五项变异分别破坏路径报告、扫描、计数、首条记账与注入列表，要求各自业务断言失败；清理另列。所有反例只用本地假上游。

probe-10 三条边界仍保留：两个内部状态只对 2.1.302 有事实支持，换版本须重核；onboarding 的两个 hello 直连官方域名，不经过 BASE_URL，必须避免触发并报告终端／私有 debug 的可见信号；400 后的每次重试都算新请求。沉默的被拒网络尝试未测量，不能用转发原件冒称全网络审计。

本候选没有运行真实供应商 CLI、读取真实登录、连接真实接口或产生模型回合。完整新产品 OS 运行、真实域名 DNS/TLS 和独立验收均未取得；不使用旧 PASS、局部模拟或进程标签冒称这些结论。全部原审查与失败保持原文，Git／提交仅冻结候选，不代替受管交付门禁。

## 候选 06 的独立复核与修正

冻结 1e556ce716220b6c1ff3200a0a5407166d8938c6 的新只读复核返回 FAIL，原文保存在
[PRODUCT-PARALLEL-REVIEW-01.md](PRODUCT-PARALLEL-REVIEW-01.md)，没有改写旧审查报告。
复核发现两个可达问题：正式普通 Python 命令可能在挂 profile 前写真实 HOME 的字节码缓存；
D 的意外失败路径只发 TERM，没有确认 C 组退出就可能删除私有根、给出成功清理收据。

入口现在先禁止字节码写入，正式命令统一使用并核对 `-I -S -B`。不支持普通 Python 启动；
解释器的 site／环境启动早于脚本检查，不能把脚本检查当作任意解释器启动的 OS 防护。
D 在意外失败时将 C 根组加入现有的身份核对、KILL、退出确认；明确取消仍保留负责报告的 C 进程。
若 C 组退出未确认，保留原始 PermissionError、单列清理错误并保留私有根，不写成功删除收据。
没有扩大 profile 权限或真实 HOME 写入例外。

同一 [test_t093_review_regressions.py](../../../workbench/tests/test_t093_review_regressions.py)
在旧冻结源码上得到四项预定业务失败，在修正源码上通过：冷缓存禁止写入、缺失启动标志拒绝、
C 忽略 TERM 时仍确认退出、C 仍存活时拒绝成功清理。对照为 review-regressions-red-02.json 与
review-regressions-green-03.json；整个检查缓存写入被拦截、进程信号被模拟，没有真实 auth、网络或 OS profile。
旧源码从 Git 原文读入 /private/tmp，不回退或修改工作树。复现命令：

```sh
python3 -I -S -B workbench/tests/test_t093_review_regressions.py /private/tmp/t093-review-regressions-new.json
```

review-regressions-green-01／02 保留为失败诊断：最初测试在关闭字节码标志后才读取测试源码，
把测试自身加载 _bootlocale 的缓存尝试也纳入了被测入口。最终测试在拦截前准备代码对象，再运行入口；
red-02 用同一最终测试重新拒绝旧实现，未靠删除失败或仅绿态掩盖该问题。debug-01 也原样保留。

相关局部复验 cleanup-local-08、once-local-06、facts-local-06、private-files-local-04、launch-local-07 均通过。
这些仅证明局部逻辑；本候选完整 OS 绿态、五项变异和修正后的 U 收尾仍未在沙箱外执行。
外验命令、每个进程的 profile 及预期业务失败见 REVIEW-REQUEST-T093-06.md；当前整票仍为 INCOMPLETE。

最终局部汇总为 freeze-checks-10.json：43 个脚本／源码语法检查、UTF-8、diff、修改范围和旧 profile AST 核对通过，地图 0 problems／0 stale。
freeze-checks-09.json 保留文档范围检查的错误基线诊断；10 改用上次冻结版本比较，本次没有改动 README 正常登录节以外的内容。

## 主控 #92：原探针通过、产品 Node 路径红态

[parallel-profile-02.json](parallel-profile-02.json) 是候选 47286b7bda7d6497a1c62a067308b18ea3fc1f7a 的外部 PASS：
U 同进程收后清单及关闭已确认，cleanup_failures=[]，collection_complete=true，临时根已删除。
这份原件与旧失败 parallel-profile-01.json 同时保留，不覆盖或把旧失败改称通过。

同一候选六个产品场景均在 prepared_services 后退出 1，未生成结果 JSON。
六份日志中 Node 26.5.0 都在 realpathSync → lstat /Users/luckye 时遇到 EPERM，未进入主模块；
五项变异的预定业务断言均未到达，核对器 FileNotFoundError 也不是业务拒绝。
只读日志摘要为 product-chain-04-startup-red.json；主控事后核对无残留进程和 HOME 新文件，worker 未执行外部 ps。

本次选择用户授权的 (a)，新增 home_read_barrier：保留原 file-read* 屏障和既有源码／可执行文件内容例外，
只用 literal 给这些允许路径的祖先目录增加 file-read-metadata，含真实 HOME；不对整个 HOME 子树开放元数据。
C、F 和外部事实 V 共用，D 规则不动。HOME 的所有写入仍被禁止；网络、fork、Security 等边界均未放宽。

新反例在完整链实际 C／F 下观察 HOME／源码祖先元数据与入口 realpath 正例，同时要求源码根公开 AGENTS.md
的正文读取被拒、读取字节为 0，其祖先目录也不能枚举。只用既有公开文件，不读 auth／用户配置，不写真实 HOME。
独立结果核对器新增相同外部条件，保留原六场状态、计数、扫描、清理和身份断言。

漏检原因：本地检查没有施加 OS profile；原 PROBE-PARALLEL 的 C 和模拟 CLI 是 Python，
F 的 Node 没有产品 F 的 HOME 内容屏障，因此没有发生受限 Node 的源码祖先路径解析。
原探针 PASS 的证明范围是它实际检查的边界和收尾，不能证明产品 Node 可启动；新检查放入实际产品链。

metadata-local-red-01 用旧冻结源码命中缺少祖先元数据规则；metadata-local-green-01 的三项局部检查通过。
其中还验证记录器在合成 HOME 无屏障时会读取一个公开哨兵字节、报告读取成功，并被业务断言拒绝，未把“被拒”写死。
这些仅证明构造／记录器与外部 V 共用规则；worker 没有运行 OS profile，实际元数据放行及正文拒绝仍待外验。
局部复验 cleanup-local-09、review-regressions-green-04、once-local-07、facts-local-07 通过。

新完整命令见 REVIEW-REQUEST-T093-07.md；使用新的 chain-05 路径，先 none，成功才继续五项变异与独立核对。
整票 INCOMPLETE；没有真实供应商 CLI／真实 auth／真实上游／模型回合，没有新的独立验收通过结论。

元数据候选 0a52043f86e5384efae943cbafe859ccb535ec14 的只读审查原文为 METADATA-REVIEW-01.md：
INCOMPLETE，未发现本次边界内的新违约；纯内存对照拒绝正文可读、读取一字节却声称拒绝、ENOENT、目录可枚举和入口未解析五种坏记录。
审查不替代 OS 执行。产品源码随后未变；另补 run_t093_facts_entry.py 供主控验证实际外部 V 入口，
同 PID 准备无认证小输入后进入真正 --stage facts，不嵌套 profile、不留无保护监督进程。
该脚本只做语法检查，未在 worker 中执行；命令、预期计数与保留输入的范围已补在交接请求 07。

## 主控 #94：V 入口通过、R Git 阶段失败

候选 2d4eba04b42ae7dd83f0f190ff99a08aabb9a0b4 的外部 V 已实际通过，原件 external-facts-05.json：
rc 0、两次请求重数一致、fixture_nonce 非空。本轮产品源码未变，保留该入口事实，不提升为完整链通过。
完整 none 原件 product-chain-05-setup-red.json 仍为 INCOMPLETE；其后五场按停止条件未跑。

只读检查定位最新根 /private/tmp/t093-chain-_7290n4q，没有端口／session／audit，只到初始角色与合成认证源，
故失败范围是三个 Git 检查。创建哨兵到结果落盘为 15.236 秒，符合原来的 15 秒超时；相同全索引操作用无认证独立哨兵本地耗时 19.325 秒、正常返回 1。
setup-05-inspection.json 保留目录元数据及测量；未读取认证正文。原异常／stderr 已丢弃，不能恢复哪一条原命令确切超时，超时结论保留为有证据支持的推断。

现在只有完整索引扫描使用 90 秒、有界且只执行一次；原扫描范围、返回码要求和其他断言不变。
R 结果新增 setup_stage、原异常类型／脱敏消息／errno 或 timeout／栈位置，以及最近 Git 的原输出摘要、用时、返回码和回收状态。
诊断先脱敏再截断、写盘前再扫，保留原主失败，清理异常单列。超时持有者终止并回收本次独立 Git 组；部分 stderr 即使回收失败也保留。
R 失败删除新生成的 source-home/.claude，保留其他现场及真实的未完成状态。

setup-diagnostics-red-04 用旧驱动拒绝五项要求；setup-diagnostics-green-04 对当前驱动通过，
覆盖超时回收、90 秒单次扫描、raw／JSON／URL／base64 脱敏、主失败不被清理盖住、实际 main 到 Git 阶段的上下文。
进程及信号为模拟，不代替实际 G 和完整链复验。局部修正过程中 red-02 的回收错误覆盖问题和旧摘要均原样保留。

七个历史根仍有合成认证源，见 retained-fixtures-05.json；不原样归档凭据，选择在保留结果／清单后整根删除。
新 cleanup_t093_retained_fixture.py 只接受已知任务结构、当前 UID、确认已清理的私有 HOME 和已消失的记录 PID／组；未知或活动现场拒绝。
它不读认证正文，只删除依赖链接本身，不沿链接删除实际依赖；初版单次 X 禁 HOME 写入、网络／Security／fork，审查修正后的停机核对与当前 X 权限见下段。
retained-structure-local-01 的初版不识别变异源码副本，结果保留；02 只读识别全部七根，但进程探测为模拟，未实际删除。
retained-cleanup-local-02 的五个合成场景通过；实际清理收据仍待主控执行，不声称已删。

新沙箱外命令、七根逐项清理及 chain-06 复验见 REVIEW-REQUEST-T093-08.md。所有旧结果和审查原文不改。
地图与局部检查见新的 freeze 摘要；没有真实模型／供应商 CLI／真实认证／真实上游回合，整票 INCOMPLETE。

驱动冻结 28276275d96e97d3ac861600530831a5f2d84f91 的只读审查为 FAIL，原文 SETUP-REVIEW-01.md：
R/G 异常与脱敏反例未发现新增问题，但初始目录也可能仍由 R/G 使用，不能仅凭形态删除。
修正后清理入口只接受 retained-cleanup-scope-05.json 中本 worktree 的七根；每个根都必须取得当前 R/G 停机核对，列表缺失、不完整、匹配到进程时拒绝。
以一条 /bin/ps 子进程做已授权的只读核对，只有任务 PID／组／状态进入收据，完整参数不落盘；X 为此允许 fork，子进程继承禁 HOME 写入／网络／Security，产品 F/U/D 的 fork 禁令不动。
收据把核对范围绑定具体根与 worktree，原有已启动服务的 PID／组和 D 清理收据仍逐项要求。
cleanup-quiescence-red-01 在旧冻结源码复现活动初始根被删除；green-01 的同一断言拒绝删除，并核对合成的相对 R、G、空匹配／不完整进程列表。
retained-cleanup-local-03 继续通过五个合成清理场景；这些进程核对为模拟，当前仍没有实际删除七根或取得完整链 OS 绿态，也没有新的独立验收通过结论。

## 主控 #97：清理 PermissionError

请求 08 的七根清理实际都返回 PermissionError／INCOMPLETE，原结果缺少路径和 errno；完整链 -06 没有继续运行。
cleanup-05-inspection.json 保留七份原结果和只读元数据：495 项均无 0000、异主、flags 或特殊文件，七根 0700、UID 501 与 worker 相同，ls -ldeO 未见 ACL。
认证正文未读，保留根未改动。/bin/ps 为 root-owned 4755，/usr/bin/pgrep 为无 setuid/setgid 的 0755。
初始目录也失败，指向共同的受保护 ps 启动；原次错误位置尚未恢复，不能仅凭模式推断当作实捕异常。

默认清理观察器改为非特权 pgrep，限定当前 UID，只收 PID；不复制二进制、不 chmod，也不放宽 X 或产品 profile。
对照 Python 仅睡眠并携带 R/G 标记，不运行实际 R/G；查询须看到它，终止回收并确认组消失后再查真实 R/G。
看不到对照、非预期退出码、输出不合法或回收未确认均拒绝删除；对照 exec 前即设 20 秒硬期限。

失败会记录具体 operation／path／errno，或无文件目标时的 PID；包含可取得的 mode／uid／flags／类型。
遍历错误显式上报，rmtree 回调记录完整路径与原始 os_filename，根缺失核对的权限错误不冒称删除成功，次要错误不覆盖主错误。
新增 --inspect-only 不删除；同一 X 下会单独记录旧 ps 的执行错误，然后用新观察器核对。
只处理既有七个固定根，permission_changes=[]；无需也没有实施 chmod。

局部 cleanup-errors-red-03 在旧冻结版本上六项失败，green-03 通过六项诊断；FIFO 用合成文件验证不打开。
cleanup-observer-red-01 拒绝旧观察器，cleanup-quiescence-green-05 用模拟结果核对 R/G 正对照及失败／不可见对照拒绝；retained-cleanup-local-06 通过含只检查不删除的六个合成场景。
这些不证明新观察器在 X 下已运行。本次仍没有读取真实认证、启动供应商 CLI／真实上游／模型，也没有删除现有七根。
先执行 REVIEW-REQUEST-T093-09.md 的一根只检查命令，成功后才逐根清理、继续请求 08 的 chain-06。整票 INCOMPLETE。

清理实现冻结 d355efac68c74ca8af7fe9bd8fea5a98f1968e9c 的只读审查为 INCOMPLETE，原文 CLEANUP-OBSERVER-REVIEW-01.md：
13 个纯内存反例未发现本次范围内的已证实违约，但没有新 X／观察器／实际删除证据。
它指出原错误单元测试主要直接调用 helper；随后补 cleanup-cli-red-01／green-01，实际调用 main 和独占 JSON writer，只模拟失败操作／bootstrap。
旧实现的最终失败收据缺少 operation/path/errno，被同一业务断言拒绝；当前文件错误与观察器错误两个最终 JSON 均具备准确字段。
这仍是 L1 模拟，不能声称已复现真实受保护 exec 或实际文件权限；清理实现自审查后未变。地图与最终局部状态见 freeze-checks-16.json。

## 主控 #98／#100：先保留主失败，再交清理拥有者

**本候选 INCOMPLETE。** 主控已确认旧七根全部删除成功，inspect-only 的旧 ps 在 X 下直接捕获 PermissionError、errno 1、/bin/ps、4755；新观察器实际通过。
原件摘要与七份清理结果保存在 chain-06-cleanup-red.json。随后候选 bc87c71fc 的 none 在 prepared_services 后遭 ENOTEMPTY，未写 JSON；后五场未跑。
新根 /private/tmp/t093-chain-e189ndt0 只剩 source-home（含合成认证）。worker 仅列元数据，不读认证正文、不删除它。

根因是测试 C 保留了对合成认证源的拒读拒写，却试图删除其父根；删除异常又覆盖了已捕获的业务失败。
主控 #100 同意这条判断并要求独立清理拥有者。原业务错误已丢失，不能从收尾错误推断它是什么。
新流程先持久化原错误的类型／消息／code／errno／path／stack，后续清理错误另列；结果采用独占首次发布、拥有者核对后的原子更新和 fsync，检查点摘要另存 events。
R 的 Git 终止／生成认证目录删除之前也先保存原异常，修正同一类先清理后留证据的问题。

独立长期 D 先执行原 metadata_service，再等待 C 的清理许可；许可必须能读回同一候选／夹具的 cleanup_pending 检查点。
测试 D 只增加本次合成 source-home 的 file-write-unlink，可枚举目录，普通文件正文仍拒读；用 open 反例记录被拒及 0 字节。
C/F 与真实 HOME、网络、Security、fork 边界均不变。原始基线 helper 仍用未扩展 D，结果另列 D_baseline 的完整规则。
D 删合成源并提交带所见检查点序号的收据后退出。C 再确认 U 关闭、daemon 关闭、F/D/U/S/M/G 组与登记子进程退出，最后同步删剩余根。
无法确认写入者就不删根；ENOTEMPTY 等删除错误记录为次要清理失败，不能取代原主失败。报告 PID 最后由外部 V 确认退出。
正式产品不删除用户认证源；首轮 de956c2de 只修改测试／清理／核对与文档，产品 src 未改变。随后审查指出产品准备函数内部同样先清理后报告，修正见下段。

局部红绿为 chain-publication-red-02／green-04：同一检查在 bc87 的真实旧清理尾部命中 primary_JSON_must_exist_before_any_cleanup，当前发布器通过主失败、ENOTEMPTY、存活写入者、次要收尾错误与已有证据不覆盖五项检查。
setup-publication-red-01／green-02 对 R 命中 R_primary_JSON_must_exist_before_source_cleanup，修复后同时核对先落盘再终止 Git。
chain-cleanup-oracle-green-01 用独立给定的收据拒绝活动写入者、主失败丢失、源未删、正文可读、先删源、无历史与报告仍在运行七种反例。
cleanup-quiescence-green-07 增加 C 的活动／正对照；retained-cleanup-local-07 拒绝 source-only 多余项并验证固定结构删除。
这些均为本地合成文件与模拟进程，只证明局部逻辑，不证明 OS 权限或完整链已通过。

主控 #100 明确 Codex 会话本身是一层 sandbox，不能在其中嵌套本次 profile；此前本地可用性检查 exit 71，后续升级被拒，本轮不再尝试。
按其要求交付沙箱外 REHEARSE-CHAIN-01.sh：先让同一原 R/G/C 链在两次 hook／Stop 后主动抛 rehearsal_primary_probe，核对主失败和完整清理，再跑绿态。
两场及独立核对全部符合预期后才运行正式六场；新命令、实际进程 profile 表和停止条件见 REVIEW-REQUEST-T093-10.md。
唯一新残留用 CLEANUP-CHAIN-06.sh 清理，精确范围在 retained-cleanup-scope-06.json；不读认证正文、不 chmod，R/G/C 未停或形态不符均拒绝。
所有旧审查报告保持原文，旧 PASS 不替本候选的 OS 演练／六场复验背书。真实供应商 CLI、真实 auth、真实上游与模型本轮均未运行。

首轮冻结 de956c2de 的只读审查为 FAIL，原文 CLEANUP-PUBLICATION-REVIEW-01.md 保留不改。
它在准备函数内部复现“清理先于原异常落盘”，并证明 V 只信任退出布尔值，活动组／子进程也能通过。
产品 prepare 现要求调用方提供失败发布者，在内部清理前发布，清理异常另报，最后仍抛原异常；真实入口只保存类型／errno，主失败与清理用不可覆盖的独立 JSON，测试入口保存完整脱敏摘要。
C/F/D/G/V 的既有 OS 权限规则未变，测试 D 的合成源 unlink 例外仍按上文单列。不是对准备错误的忽略或成功降级。
V 现把组／子进程身份与原登记记录绑定，并独立用信号 0 核对每个 PID／组；只有 ESRCH 可判已退出，权限错误或仍存活都拒绝。
prepare-failure-red-03 在旧产品源码上拒绝原异常落盘顺序及覆盖；green-03 覆盖实际 prepare＋测试发布器和真实 R main 的类型收据／次要清理错误。
chain-cleanup-oracle-red-03 拒绝旧核对器，green-04 的 12 项检查包括谎报退出、身份错配及漏子进程。
两项均是无 auth／无 OS 执行的合成检查；新沙箱外演练、固定残留删除与正式六场仍待主控，整票保持 INCOMPLETE。

修正实现冻结 965560422036ae4382036a9e68758abe0fd74baf 的一次限定复核为 INCOMPLETE，原文 CLEANUP-PUBLICATION-REVIEW-02.md。
审查者独立执行 prepare 3 项与 oracle 12 项合成检查均通过，认定前两项 P1 的 L1 缺口已关闭；实际 OS 边界仍未测。
原始小报告另存 prepare-review-green-01.json、oracle-review-green-01.json。实现自该冻结后未改；后续只补文本证据。
按请求 10 先清理 e189ndt0，再做同 profile 的两场演练，通过独立核对后才做正式六场；旧候选通过不沿用。


## 主控 #103：pane_release 的 not-ok 回复被断言丢弃

**INCOMPLETE。** 候选 4533ebeb7 的固定残留清理 rc 0／PASS，e189ndt0 已删除；原件 cleanup-07.json。
同候选 primary 演练 rc 2，主失败 chain_operation_failed，失败位置为 turns 的 pane_release 布尔断言，并未到 rehearsal_primary_probe。
边界全部通过，请求 0；主失败先落盘，source HOME／隔离 HOME／夹具删除及写入者退出已确认，cleanup_failures=[]。
原结果摘要与检查点为 rehearsal-01-primary-summary.json、rehearsal-01-primary.events.jsonl。绿态、正式六场均未跑。

旧断言丢弃了 daemon.error／details，event store 又随夹具删除，不能恢复实际拒绝码。
当前 worktree 的 release 检查初始 unknown／无 active、failed，再执行 processInfo 的前台身份核对；没有 T-096 的屏幕就绪条件。
其中 /bin/ps 与之前 X 下被拒的 setuid 程序相同，是待验证嫌疑，不能写成已确认的本轮原因。
没有据此改产品、全局配置或 OS profile，也没有自动重试、放行状态或绕过身份核对。

测试调用现在把 command／实际 error／details 写入 error_summary.daemon_response，message 也保留实际返回码；pane_release 保存前后 status 和返回值。
同样处理 controller_start、pane_dispatch 与 daemon_stop 的 not-ok，清理错误仍为次要；全部内容经既有凭据脱敏与独立扫描后落盘。
daemon-rejection-red-01／green-01 对实际 release 代码块的三种合成回复复现并修复错误丢失，green 验证 details 的合成凭据被脱敏；chain-publication-green-05 的五项主失败／清理检查通过。
这些仅证明 L1 回复留证，不证明本轮真实 daemon 拒绝原因。当前只修复诊断，业务拒绝根因待下一次真实回复，不宣称整链已修好。
请求 11 给出 rehearsal-02-primary 命令；若错误仍为 pane_release_rejected，回传结构化 error／details 和前后状态，停止绿态及正式六场。

诊断实现冻结 d594057a9672e2b7441ca17c4e8632296927f1b4 的只读审查对 L1 留证范围给出 PASS，原文 DAEMON-ERROR-REVIEW-01.md。
审查者独立重跑新旧 release 代码块，并以新 nonce 拒绝码、不同状态、含合成凭据的详情核对清理前发布；原件以 daemon-rejection-review-* 和 publication-review-green-01 保存。
PASS 不覆盖真实 daemon 拒绝原因或 OS 链路。产品／权限／release 条件未改，整票 INCOMPLETE；请求 11 仍需主控先运行新的 primary。

## 主控 #105：方案 b 替换 setuid ps

**INCOMPLETE：修复已实现，OS primary 待执行。** 主控在 6f6e2820b 实际取得 pane_release_rejected，daemon.error=orchestration_failed、details=Error: spawn EPERM；before／after 无 active、queue、writing 或 draft。
旧 release 的第 688 行调用 processInfo，第 398 行唯一 spawn 是 /bin/ps -axo pid=,ppid=,pgid=,tpgid=,comm=；本机 stat 确认 04755，原始回复摘要为 rehearsal-02-primary-summary.json。
结合此前受保护 ps 的实捕拒绝，已定位该 setuid 查询启动；不再把它写成队列或屏幕问题。

选择主控准许的 b：Panes.processInfo 统一改由 /usr/bin/python3 -I -S -B processSnapshot.py 查询 macOS libproc。
helper 在原 C 中继承全部禁令，只遍历本 PTY 后代，不读参数／环境／认证、不全机枚举、不启动子进程。
SDK sys/proc_info.h 的 136 字节 ABI、关键偏移和退出标记均通过静态编译对照；函数语义核对本机 libproc.h 与 Apple 官方开源 libproc.c。
查询保留原 PID／PGID／TTY 前台组／可执行路径条件，复核出生时间／身份变化；权限拒绝／短数据／截断／坏树都拒绝，僵尸和已知退出不作活 leader。
这是多次只读内核查询，不宣称原子快照或后续存活保证；原有 hook／Stop 身份重查继续执行。
没有分离 daemon、增加 CLI 权限或 fallback；所有 OS profile、auth 复制、网络、Security、fork 与门禁源文件保持不变。

REALITY GATE: INCOMPLETE。observed 为真实 spawn EPERM、唯一 ps 调用和 04755；measured 为 SDK ABI 编译通过；inferred 为去掉 setuid exec 可消除已定位的启动障碍。
material unknown 是同一 C 下实际 libproc 查询是否可读以及整链是否成功，不能用模拟结果替代。
最小 Tracer bullet 保留在真实 release／原生 hook／Stop 生产路径，新 primary 同时作为查询权限与两次转交探针；执行主控按请求 12 在沙箱外跑，错误或清理不符即停。

process-observer-red-02 在旧产品上由同一当前测试拒绝 setuid ps；green-04 的 11 场（含随机 PID）通过。
process-snapshot-green-03 的 23 项合成缓冲／树及 ABI 编译通过；ignored-denial 变异命中明确业务断言，见 process-snapshot-mutant-01。
受影响旧 pane 测试首轮失败不是新查询导致：旧产品＋旧测试也重现 writes.then 缺字段，原件 conflict-panes-parent-01；补齐当前 fixture 字段、保留原断言后 conflict-panes-green-02 四项通过。
新观察留证导致旧提取测试包含 TS 注解，parser-red-03 的 Unexpected token 保留；修正提取范围后 daemon-rejection-green-04 三项与 chain-publication-green-06 五项通过。
这些均无真实 libproc／ps／pgrep 查询、OS profile、认证、网络或模型执行。

完整链现在导出实际 release 的 foreground_process_query，独立 V 要求其 observer 方法、PTY root 与内核前台身份匹配假 CLI。
primary-03 的命令和停止条件见 REVIEW-REQUEST-T093-12.md；只有主动失败及完整清理均符合预期，才跑 green／V 和正式六场。

首轮查询实现冻结 3fca92984443d0954f1fda8fbe0ba68230c66dcc 的只读审查为 FAIL，原文 PROCESS-OBSERVER-REVIEW-01.md。
审查者对 native/observer/rejection/publication 的 42 项 L1 检查通过，但指出合法假 API alias 会因 argv[0] 与内核可执行路径不同而误拒。
实际 Claude 启动边界现于原版本校验后、PTY 启动前保存规范 executable_path，Codex 使用原来已规范化的路径；保留实际 argv，不在查询时重新解析 alias。
process-alias-red-02 在首轮冻结上命中 valid_alias_must_keep_foreground_identity；green-02 的真实 start/release＋模拟执行／PTY／内核返回通过 alias 与不同目标反例。
process-alias-mutant-01 将目标改为每次 query 再解析 alias，启动后 alias 改指的其他程序因而被误认；同一反例拒绝了这种错误修法。
version-boundary-green-01 的原版本／并发断言与 conflict-panes-green-03 的原四项业务断言继续通过。新增版本夹具只提供 realpath 的 IO 边界，未削弱版本比较。
首次 alias 夹具用了不符合旧假 API 合同的根前缀，被 isolated_controller_root_required 拒绝、无 JSON；修正为该入口既有 t078-2 前缀后，使用同一最终夹具重新取得红绿，未改产品边界。
以上仍不证明真实 C 的 libproc 权限或完整链成功；新 primary 命令不变，等待主控执行。
