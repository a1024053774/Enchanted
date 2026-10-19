# T-093 独立审查请求 01

2026-10-17；task T-093，attempt a1，ready_rev 1，worker s16-t093。
受管 session 67f986cc-92e4-4089-9c22-802a1143b645；原生 session 01a14ae2-a3df-7731-a7b0-1b679b3bce95；launch launch-45148b6732394eccab3b21224b238513。
codex-cli 0.163.0，gpt-6.1-sol / xhigh；配置不作实际供应商 tier 的证明。

请执行主控新开干净、只读的 reviewer 会话，按项目角色及 behavioral-acceptance-review 技能审查本次冻结候选。
**整票 INCOMPLETE：实现及所列运行检查通过，最终独立审查与唯一门禁验收／集成未完成。**
本请求不代替 submit、acceptance、integration 或 ticket 关闭。worker 冻结后不再修改，后续由主控处理。

## 冻结对象

交付候选为 **3887a6140f293fc333ce5de4966c67eb9f3fe6fb**。
最终审查对象是包含本请求及 freeze-checks-02.json 的冻结提交，完整 SHA 由 worker 最后一行 `T-093 FROZEN <sha>` 交接、主控转发；请先核对两者之间只有这两份文本证据，再绑定最终 SHA 给出结论。

代码起点 main：61786370428c3ec5f894ea60acccf2695d54c2dc。
完整链通过版本：3b2172beba0427fb6eba69024536e0a7812bf7cf。
3b2172beb→3887a6140 的产品 src、完整链脚本及 C/Python 假 CLI 均未改变。
唯一测试变化是 test_t093_forwarder.ts 补可选元数据原件导出、反例细项与合成值 Git index 扫描；生产路径与全链通过证据不依赖这个导出分支。
变更范围核对见 [freeze-checks-01.json](freeze-checks-01.json)、freeze-checks-02.json。

允许范围为 workbench/src（gates 除外）、workbench/tests、workbench/README.md 与本票 evidence；未修改 acceptance、gates、地图或任何全局配置。
规范依据为 [T-092 决定](../../../.project-map/tickets/T-092-normal-login-profile.md)、[T-093 ticket](../../../.project-map/tickets/T-093-normal-login-profile-build.md) 及 AGENTS.md。
用户已明确本票不跑真实模型回合；真实模型必须在合入后另说开工。本请求也不授权 reviewer 运行模型或读取真实认证。

## Acceptance 与可读证据

| 条件 | 证据及当前观察 |
| --- | --- |
| main 红态 | profile-red-01.json：实际构造源码等同 main；正常登录合同失败，旧入口拒绝非 loopback API。profile-green-01.json 同合同 4 项通过 |
| 假上游完整链、计数／清理／真实 HOME | product-chain-03.json 与 product-chain-03.host-home.json：主控 #73 沙箱外 rc 0；实际 daemon／PTY／进程身份／hook／inbox／Stop，唯一哨兵转交一次、反馈完成；独立上游=入口=转发=原件请求=2，结果 2；隔离根／夹具删除，state 扫描 0；实际 HOME 5554→5554、差异 0 |
| HOME 路径反例 | forwarder-green-03.json：argv 混入指定 HOME 前缀，报告字段与 1 次出现；禁用检查的变异被拒 |
| 凭据证据反例 | 同报告：随机合成原值及编码变体均被扫描命中；临时泄漏文件删除；保留证据 4 文件扫描 0，当前 Git index 对本次合成值／变体命中 0 |
| 漏记反例 | product-chain-03 的实际日志删一条后对账失败；forwarder-original-01/missing-row 保留独立补充运行的损坏副本，事实命令读回入口 2／原件 1／counts_match=false |
| 无凭据入证据或 Git | probe-10 的真实凭据副本只在私有内存／隔离根且已清理；完整链合成值 state 扫描 0；原件只含方法、路径、长度、bearer 匹配布尔值与结果，不含头或正文。结构检查与扫描范围见 RESULTS，不冒称对真实 auth 做了新的全 Git 历史扫描 |
| 地图 | 两份 freeze-checks 保存 0 problems／0 stale；未改 ticket 验收框 |

完整细节、失败历史、复现命令与版本边界见 [RESULTS.md](RESULTS.md)。
product-chain-03 在运行中重数原件，随后销毁了夹具；该轮原件没有保留。
forwarder-original-01 是另一次同生产转发器的独立运行，已留完整和漏记两个小型输入，不能冒称它就是 chain-03 原件。
可在当前沙箱只读复数，不启动 CLI、不读 auth：

```sh
node workbench/src/claudeLoginCheck.ts evidence/2026-10-16-batch16/T-093/forwarder-original-01
node workbench/src/claudeLoginCheck.ts evidence/2026-10-16-batch16/T-093/forwarder-original-01/missing-row
```

## 必须核对的边界与审查重点

- probe-10 使用新建的 hasCompletedOnboarding 与唯一当前项目的信任状态，都是 2.1.302 内部字段；正式模式固定版本，升级须重新核对。没有复制真实设置、历史或其他 auth 对象。
- onboarding 的两个官方 hello 候选绕过 BASE_URL。正式模式预先生成状态并限制 CLI／子进程只能连接本地转发端口与精确 Unix socket；事实报告识别可见预检。preflight_observed=false 不证明零网络尝试，转发计数不等于全部网络尝试。
- probe-10 的两个 Messages 请求都被假上游回 400，按主控结论说明重试；失败与每次重试各算一条，转发器自身不重试、不跟随重定向。
- auth 来源为明确的文件或精确 Keychain 服务／单一 keychain 文件，无枚举或自动 fallback。重点检查私有副本、错误输出、终端原始字节、跨分片脱敏与结束清理，不能只检查屏显文字。
- 产品 hook 需要派生／执行子进程并连接既有 daemon。请核对继承 sandbox 的子进程仍不能读写受保护源 HOME、也不能连其他端口；不要把必要的工作区／state／源码路径例外描述为整个真实 HOME 无引用。
- 仍是同一 controller_start 与原生 hook／Stop 转交，保留身份、prompt 关联、去重及反馈；本票未另起门禁或策略引擎。
- 逐条落盘及 fsync 必须先于上游；每条错误／响应都有结果，不记录认证头与正文；计数对账必须拒绝漏行的错误结论。事实命令只报告事实，不自动放行或拒绝模型调用。
- 真实 HOME 清单只读四个既定范围的元数据；所有差异报告且不归因、不自动忽略，没有 root/fs_usage 归属采集。本次外层实际差异为 0。

## 旧审查与反事实

[PRODUCT-REVIEW-01.md](PRODUCT-REVIEW-01.md) 对旧候选 ff625c371 为 FAIL：OSC/DCS 负载可泄漏凭据。
该缺陷已修复；当前测试在所有分片位置检查实际公开字节，旧候选会被相同测试拒绝。
counterfactuals-04.json 的对照和 7 种错误候选均按预期区分；不把自测当作本次新候选的独立审查 PASS。
首次 counterfactuals-01 的测试解析问题、旧探针失败与旧审查结论均保留；未覆盖或未知之处请明确写 INCOMPLETE。

## 运行与交接限制

本轮没有新增必须在沙箱外运行的检查。若 reviewer 需要完整复验，请先交执行主控，使用 RESULTS 中脚本和全新输出标签；不申请升级、不自行运行 ps、供应商 CLI 或真实 auth，也不改测试与产品。
后台服务必须脱离调用者进程组。不得读用户应用、全局设置、钥匙串其他条目或其他会话，不得发送外部消息、push 或 rebase。

请将结论绑定最终冻结 SHA，区分 PASS、INCOMPLETE、BLOCKED、NO_GO，并明确代码缺陷、证据不足与环境限制。
审查通过后由执行主控走唯一门禁；此文件及 Git 九项尾注均不是业务 submit／集成收据。
