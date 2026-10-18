# T-093 R 阶段诊断与保留夹具处理交接 08

**INCOMPLETE：外部 V 已通过；完整链仍未取得绿态，本次驱动修正等待沙箱外复验。**
task T-093 / attempt a1 / ready_rev 1，worker s16-t093；受管 session 67f986cc-92e4-4089-9c22-802a1143b645，native session 01a14ae2-a3df-7731-a7b0-1b679b3bce95，launch launch-45148b6732394eccab3b21224b238513。
以最后 FROZEN 完整 SHA 运行，不代替受管 submit、独立验收或集成。

## 原因的证据边界

主控 #94：候选 2d4eba04b42ae7dd83f0f190ff99a08aabb9a0b4 的实际外部 V 入口 rc 0，
model_requests=2、counts_match=true、fixture_nonce 非空，原件为 [external-facts-05.json](external-facts-05.json)。
本次没有改变产品源码，因此保留这项入口结论，不把它提升为完整登录链通过。

none 在 R 返回 rc 2，旧结果 [product-chain-05-setup-red.json](product-chain-05-setup-red.json) 只有通用错误。
最新夹具是 /private/tmp/t093-chain-_7290n4q：只有初始目录、角色卡、合成认证源和哨兵；
没有端口文件、源码变异副本、session 或 audit，失败范围是三个只读 Git 检查。
创建哨兵到失败结果落盘相隔 15.236 秒，与当时 communicate(timeout=15) 一致。
相同完整索引搜索在 worker 中用独立无认证哨兵耗时 19.325 秒，正常返回 1、stderr 为空；没有施加 G。
只读现场与测量摘要是 [setup-05-inspection.json](setup-05-inspection.json)。

这些证据支持 Git 超时判断；原异常及 stderr 已被旧驱动丢弃，无法恢复究竟是哪条 Git 命令超时。
不把推断写成已捕获的原始 TimeoutExpired，也不把当前 R 失败归因到 C/F 或 Node。

## 修正

- 完整索引扫描单独使用 90 秒期限，覆盖已观察到的 19.33 秒；其余 Git 检查仍为 15 秒。仍只扫一次、范围完整，没有重试、跳过文件或忽略返回码。
- 每个 R 阶段保存 setup_stage；结果保留原始异常类型、脱敏消息、errno／超时及栈位置；最近一次 Git 记录 PID、G、时限、用时、返回码和脱敏 stdout／stderr。正文在脱敏后才截断，诊断写盘前再次扫描。
- Git 超时由其 Popen 所有者终止本次独立进程组、回收并确认退出；回收失败单列，原始超时及已捕获的部分 stderr 不被覆盖。
- R 失败会删除本次生成的 source-home/.claude，保留其余非凭据现场；若已经生成私有登录根，结果记录该路径，仍由原 D 生命周期负责，不虚构删除成功。
- 产品 C/F/D/V、HOME 读写屏障、网络、fork、Security、hook／Stop、计数、扫描和原六场业务断言均未改变。

新字段在结果 JSON 中；终端仅打印阶段与异常类型，凭据和未脱敏 stderr 不进终端／证据／Git。
setup-diagnostics-red-04 对旧冻结驱动的五项预定检查失败；setup-diagnostics-green-04 通过原异常、回收、脱敏、实际 main 阶段和有界扫描五项检查。
进程和信号均为模拟，没有据此宣称 G 的 OS 运行已通过。

## 遗留夹具：整根删除，凭据不归档

七个已观察目录及文件数／字节数见 [retained-fixtures-05.json](retained-fixtures-05.json)。
最新 R 目录共 3 个文件／296 字节，含合成认证源；此前六个 Node 入口失败目录也仍保留合成认证源。
不把这些根原样放进 evidence、Git 或外置归档。失败结果、原日志的诊断摘要和目录清单已保留，选择删除整个运行夹具。

cleanup_t093_retained_fixture.py 每次只处理明确的一个根：
检查 canonical 路径、UID、已知目录／文件结构，不读取认证正文；启动过服务的夹具必须有确认私有 HOME 已删除、无清理错误的 D 收据，所有记录 PID／组信号 0 均须为 ESRCH。
未知文件、未确认清理、PID／组仍存在或身份已复用时拒绝删除，不能强行忽略。
变异源码的 node_modules 只允许指向本 worktree 依赖的既有链接，删除时只 unlink，不沿链接删除目标。
整个删除进程单次施加 X：禁写真实 HOME、禁网络／Security／fork；没有后台监督进程。

以下每条分别执行，输出必须是新路径。任何 INCOMPLETE 均保留对应根和收据，停止该根处理：

```sh
python3 -I -S -B workbench/tests/cleanup_t093_retained_fixture.py --root /private/tmp/t093-chain-_7290n4q --output /private/tmp/t093-cleanup-05-01.json
python3 -I -S -B workbench/tests/cleanup_t093_retained_fixture.py --root /private/tmp/t093-chain-l2qtw5kt --output /private/tmp/t093-cleanup-05-02.json
python3 -I -S -B workbench/tests/cleanup_t093_retained_fixture.py --root /private/tmp/t093-chain-4ix7bnvu --output /private/tmp/t093-cleanup-05-03.json
python3 -I -S -B workbench/tests/cleanup_t093_retained_fixture.py --root /private/tmp/t093-chain-jlyq2vja --output /private/tmp/t093-cleanup-05-04.json
python3 -I -S -B workbench/tests/cleanup_t093_retained_fixture.py --root /private/tmp/t093-chain-kyew9xey --output /private/tmp/t093-cleanup-05-05.json
python3 -I -S -B workbench/tests/cleanup_t093_retained_fixture.py --root /private/tmp/t093-chain-wx413hum --output /private/tmp/t093-cleanup-05-06.json
python3 -I -S -B workbench/tests/cleanup_t093_retained_fixture.py --root /private/tmp/t093-chain-_4gt5f2t --output /private/tmp/t093-cleanup-05-07.json
```

期望 rc 0、status=PASS、root_removed=true；收据保留删除前文件数／字节数及凭据文件曾存在的布尔值。
worker 只读检查过七个目录结构，进程探测由 mock 替代；没有删除它们，也没有证明实际 PID 目前仍未复用。
retained-cleanup-local-02 的五项合成检查覆盖初始／已清理目录整根删除、未确认／活动进程拒绝、依赖链接目标保留；不冒充 X 的 OS 证据。

## 完整链沙箱外复验

外部 V 已取得事实、产品源码未变，本轮不重复该命令。
先跑 none，允许本次完整索引扫描等待最多 90 秒；只有 rc 0 且 JSON PASS 后才继续五场。
若 R 再失败，直接回传新 JSON 的 setup_stage、error_summary 与 last_git，保留原件，不重跑覆盖它。

```sh
t093_repo=/Users/luckye/Documents/Code/a2a-wt-t093
t093_candidate=FULL_FROZEN_SHA
bash evidence/2026-10-16-batch16/T-093/EVIDENCE-RECHECK-03.sh "$t093_repo" "$t093_candidate" /private/tmp/t093-chain-06-green.json none
```

none 通过后分别执行，期望 rc 2、预定主失败、cleanup_failures=[]：

```sh
bash evidence/2026-10-16-batch16/T-093/EVIDENCE-RECHECK-03.sh "$t093_repo" "$t093_candidate" /private/tmp/t093-chain-06-home-mutant.json home-references-empty
bash evidence/2026-10-16-batch16/T-093/EVIDENCE-RECHECK-03.sh "$t093_repo" "$t093_candidate" /private/tmp/t093-chain-06-scan-mutant.json scanner-zero
bash evidence/2026-10-16-batch16/T-093/EVIDENCE-RECHECK-03.sh "$t093_repo" "$t093_candidate" /private/tmp/t093-chain-06-count-mutant.json counts-always-match
bash evidence/2026-10-16-batch16/T-093/EVIDENCE-RECHECK-03.sh "$t093_repo" "$t093_candidate" /private/tmp/t093-chain-06-first-mutant.json drop-first-record
bash evidence/2026-10-16-batch16/T-093/EVIDENCE-RECHECK-03.sh "$t093_repo" "$t093_candidate" /private/tmp/t093-chain-06-empty-mutant.json empty-credential-cases
```

五个主失败依次为 home_path_injection_must_be_reported、credential_injection_must_be_detected、missing_raw_request_must_be_detected、forwarder_record_count_must_match_upstream、credential_injection_cases_must_not_be_empty。
最后独立核对：

```sh
python3 -I -S -B workbench/tests/check_t093_chain_results.py --candidate "$t093_candidate" \
  --output /private/tmp/t093-chain-06-verdict.json \
  /private/tmp/t093-chain-06-green.json /private/tmp/t093-chain-06-home-mutant.json \
  /private/tmp/t093-chain-06-scan-mutant.json /private/tmp/t093-chain-06-count-mutant.json \
  /private/tmp/t093-chain-06-first-mutant.json /private/tmp/t093-chain-06-empty-mutant.json
```

每个产品进程的 profile 仍见请求 07，R 的 Git 子进程均为原 G；新增清理 helper 为独立 X，不进入产品链。
真实 HOME 清单继续照实报告、不作通过条件；采集失败仍失败。probe-10 的内部状态版本限制、onboarding 直连预检和重试计数边界不变。
真实供应商 CLI、真实认证读取、真实上游和模型回合均为 0；整票仍 INCOMPLETE，待本候选外验和独立验收。
