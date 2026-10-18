# T-093 Node 路径元数据修正交接 07

**INCOMPLETE：有外部红态与局部回归通过，修正后的 OS 完整链尚未运行。**
task T-093 / attempt a1 / ready_rev 1；worker s16-t093；受管 session 67f986cc-92e4-4089-9c22-802a1143b645，native session 01a14ae2-a3df-7731-a7b0-1b679b3bce95，launch launch-45148b6732394eccab3b21224b238513。
以最后 FROZEN 完整 SHA 为候选；冻结不代替 submit、独立验收或集成回执。

## 原因与修正边界

主控 #92 的候选 47286b7bda7d6497a1c62a067308b18ea3fc1f7a：
[parallel-profile-02.json](parallel-profile-02.json) 的原探针 rc 0／PASS、清理错误为空；
六个产品场景均 rc 1，在 prepared_services 之后、Node 主模块开始执行之前，因为
realpathSync 内的 lstat /Users/luckye 返回 EPERM 退出。没有结果 JSON，五个变异的业务断言都未执行。
六份日志只读核对摘要保存在 [product-chain-04-startup-red.json](product-chain-04-startup-red.json)；不覆盖旧输出。

采用本次授权的方案 (a)。HOME 的 file-read* 屏障同时拒绝了 Node 所需的祖先路径元数据；
现在仅对已允许的源码、依赖、Node／CLI 可执行文件的祖先目录增加 file-read-metadata，
每项都是精确 literal，包含真实 HOME，不使用 HOME 的 subpath 元数据通配。
目录列表和其他文件正文仍由原屏障拒绝；既有源码／可执行文件内容例外不变，HOME 写入禁令不变。
C、F 与外部事实入口 V 使用同一个生成函数，D 的清单规则没有改变，仍无嵌套 profile。

新增 C／F 反例用 worktree 根现有、公开且不是符号链接的 AGENTS.md；不查询 auth 或用户配置。
分别要求：HOME／源码祖先 lstat 成功、实际入口 realpath 成功；AGENTS.md 正文读取被 EPERM／EACCES 拒绝、读取字节为 0；其所在祖先目录也不能枚举。
正文意外可读时最多读一个公开文件字节，不保存该字节或目录列表，检查必须失败。
这条链明确要求源码根在真实 HOME 内，才能重现该环境边界；没有移动源码或扩大内容权限。

## 为什么之前没发现

局部构造／清理／扫描检查没有施加 macOS profile，不能证明 Node 在它里面可启动。
原 PROBE-PARALLEL 的 C 根及模拟 CLI 都是 Python，没有运行 Node 主模块路径解析；
其独立 F 允许 HOME 读取，未施加产品 F 的 HOME 内容读取屏障。
因此该探针能证明所列网络、fork、Security、拒写和收尾事实，不能证明产品 C/F 的 Node 启动。
这次把元数据正例与正文／枚举反例放进真正的产品链 C、F，并由独立结果核对器核对字段及拒绝码；
不再用原探针 PASS 代替产品启动证据。

局部 metadata-local-red-01 用旧冻结源码命中缺失元数据规则的业务失败；metadata-local-green-01 对修正源码通过。
同一检查还让记录器读取合成文件：缺少屏障时它确实报告读取成功、拒绝业务断言；没有把拒绝写死。
这是构造／记录器证据，未执行 OS profile，也未读取真实 HOME 文件正文。外部 V 的规则共用有局部捕获检查，实际 V 的 Node 启动尚无新 OS 证据。

## 每个进程的 profile

| 进程 | 本次实际启动设计 |
| --- | --- |
| R 初始准备 | -I -S -B；关闭额外 FD、拒绝 HOME 内输出 FD，精确原始 auth 读取一次仍在业务 profile 之外；无长期未保护监督进程 |
| Git 检查 | G，禁 HOME 写入、网络和 Security；只读 Git，无 optional locks |
| 短脱离 helper | 独立施加对应 F／D／U／S／M，执行 true 后退出，PID／组及退出码分别记录 |
| F Python→Node，同 PID | 独立 F；只写自己的记录目录、单监听 P、单配置上游，禁其他出站／Security／fork；新增精确祖先元数据，内容屏障保留 |
| D 基线与长期清理进程 | 原 D，禁 HOME 写入／网络／Security／fork；原 auth 前采基线，结束收后清单，确认登记组退出后删除私有根 |
| C daemon 根、PTY／zsh／编译假 CLI、Python peer、原生 hook／inbox、ps、clang、事实 Node | R 同 PID exec 单次 C，后代继承；仍只连 F 及本次 control.sock；新增精确祖先元数据，HOME 内容与写入屏障保留 |
| 测试 U | 独立 U，原产品 F 约束派生，无出站、只监听两个明确假端口，禁止 Security／fork |
| 测试 S／M | 独立使用 C；只在 M 删除合成 HOME 禁写规则，真实 HOME 禁写始终保留；创建／立即删除仍需实证 |
| 外部事实入口 | 独立 V，禁 HOME 写入／网络／Security，内容屏障加精确祖先元数据；链内事实子进程继承 C，不嵌套 V |
| 最后结果核对器 | 独立 V，禁 HOME 写入／网络／Security，不导入产品计数或扫描函数 |

新候选的实际 PID／组尚待外验填写，不能把表中设计当作已经运行的 PID 证据。

## 主控沙箱外命令

复用原 EVIDENCE-RECHECK-03.sh，没有新增长期监督脚本。日志必须放 HOME 外，输出均选新路径。
先只跑 none；若仍未得到 rc 0 与 PASS JSON，保留日志并回传，停止后续五场。

```sh
t093_repo=/Users/luckye/Documents/Code/a2a-wt-t093
t093_candidate=FULL_FROZEN_SHA
bash evidence/2026-10-16-batch16/T-093/EVIDENCE-RECHECK-03.sh "$t093_repo" "$t093_candidate" /private/tmp/t093-chain-05-green.json none
```

none 通过后，分别执行以下五条，预期均 rc 2，有 JSON、预定主失败且 cleanup_failures=[]：

```sh
bash evidence/2026-10-16-batch16/T-093/EVIDENCE-RECHECK-03.sh "$t093_repo" "$t093_candidate" /private/tmp/t093-chain-05-home-mutant.json home-references-empty
bash evidence/2026-10-16-batch16/T-093/EVIDENCE-RECHECK-03.sh "$t093_repo" "$t093_candidate" /private/tmp/t093-chain-05-scan-mutant.json scanner-zero
bash evidence/2026-10-16-batch16/T-093/EVIDENCE-RECHECK-03.sh "$t093_repo" "$t093_candidate" /private/tmp/t093-chain-05-count-mutant.json counts-always-match
bash evidence/2026-10-16-batch16/T-093/EVIDENCE-RECHECK-03.sh "$t093_repo" "$t093_candidate" /private/tmp/t093-chain-05-first-mutant.json drop-first-record
bash evidence/2026-10-16-batch16/T-093/EVIDENCE-RECHECK-03.sh "$t093_repo" "$t093_candidate" /private/tmp/t093-chain-05-empty-mutant.json empty-credential-cases
```

| 场景 | 必须出现的主失败 |
| --- | --- |
| none | null；PASS，两次请求及 400／200 收据一致，新增正文读取反例通过 |
| home-references-empty | home_path_injection_must_be_reported |
| scanner-zero | credential_injection_must_be_detected |
| counts-always-match | missing_raw_request_must_be_detected |
| drop-first-record | forwarder_record_count_must_match_upstream |
| empty-credential-cases | credential_injection_cases_must_not_be_empty |

最后独立重数、核对新增读取反例、原三个反例、八个 HOME 拒写路径及独立缺失规则变异和两项拒连：

```sh
python3 -I -S -B workbench/tests/check_t093_chain_results.py --candidate "$t093_candidate" \
  --output /private/tmp/t093-chain-05-verdict.json \
  /private/tmp/t093-chain-05-green.json /private/tmp/t093-chain-05-home-mutant.json \
  /private/tmp/t093-chain-05-scan-mutant.json /private/tmp/t093-chain-05-count-mutant.json \
  /private/tmp/t093-chain-05-first-mutant.json /private/tmp/t093-chain-05-empty-mutant.json
```

本轮不重复未改规则的 PROBE-PARALLEL，不把它的旧 PASS 提升为当前完整链通过。
真实供应商 CLI、真实 auth、真实接口及模型回合全部不运行；只用合成 auth 和本地假上游。
前后清单仍照实报告、差异不决定通过；采集失败仍失败。probe-10 的版本内部状态、onboarding 直连预检和重试计数三条边界不变，见 RESULTS。
全部旧结果和审查原文保留，本候选仍待外验及新的独立验收。
