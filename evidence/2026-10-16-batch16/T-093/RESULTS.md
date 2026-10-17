# T-093 正常登录 profile：交付结果

2026-10-17；task T-093，attempt a1，worker s16-t093，ready_rev 1。
受管 session 67f986cc-92e4-4089-9c22-802a1143b645，原生 session 01a14ae2-a3df-7731-a7b0-1b679b3bce95，launch launch-45148b6732394eccab3b21224b238513。
工具 codex-cli 0.163.0，模型配置 gpt-6.1-sol / xhigh；配置不证明实际供应商 tier。

**整票 INCOMPLETE：实现及下列无模型运行检查 PASS，最终冻结候选的独立审查、门禁验收与集成尚未完成。**
不修改 ticket 验收框，不把 Git 提交当作 Gate submit 或 integration 收据。

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

完整链已由主控 #73 执行，rc 0；本轮没有新增必须在沙箱外运行的检查。
若独立 reviewer 需要复验，必须由主控另选新输出，后台服务脱离调用者进程组：

```sh
python3 workbench/tests/run_t093_login_chain.py --output evidence/2026-10-16-batch16/T-093/product-chain-04.json
```

真实 HOME 清单范围是 .claude、.claude.json、.claude.json.backup、Library/Keychains；只读元数据，不比较 atime，不读正文、不跟随链接、不用校验值，其余 HOME 路径显式排除。
其他会话可能并发写入，所有差异都报告、不推断因果、不自动忽略；本次完整链实际差异为 0。
事实命令只报告事实，不批准或拒绝模型回合；凭据扫描保留结束时的范围和时间，不冒称新扫描。
本票没有运行真实模型回合，合入后仍等用户另说开工；没有可靠性、吞吐或成本收益主张。

冻结后由执行主控安排新的只读 reviewer 与唯一门禁；本结果不代替最终审查、submit 或 integration。
