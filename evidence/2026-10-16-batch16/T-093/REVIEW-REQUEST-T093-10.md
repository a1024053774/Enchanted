# T-093 主失败保留与清理拥有者交接 10

**INCOMPLETE：局部反例通过；同 OS profile 的完整演练及正式六场等待主控沙箱外执行。**
候选绑定 worker 最后一行 `T-093 FROZEN <完整 SHA>`。task T-093 / attempt a1，worker s16-t093；受管 session 67f986cc-92e4-4089-9c22-802a1143b645，native session 01a14ae2-a3df-7731-a7b0-1b679b3bce95，launch launch-45148b6732394eccab3b21224b238513。
不代替 submit、独立验收或集成；不授权真实 CLI、认证读取、真实上游或模型回合。

修正实现冻结为 965560422036ae4382036a9e68758abe0fd74baf；限定只读复核为 INCOMPLETE，原文 [CLEANUP-PUBLICATION-REVIEW-02.md](CLEANUP-PUBLICATION-REVIEW-02.md)。前两项 P1 的 L1 缺口已关闭，3 项准备失败与 12 项独立核对反例通过；OS 演练尚未执行。最终冻结提交相对此实现只增加本轮审查原件、文本摘要与核对结果，运行命令仍绑定最后 FROZEN 的完整 SHA。

主控 #98 已确认旧七根全部清理成功；新 none 却在 `rmSync` 遇到 ENOTEMPTY，未保存原业务异常。
[chain-06-cleanup-red.json](chain-06-cleanup-red.json) 保留主控结果及残留元数据，不读取认证正文。
主控 #100 同意：C 拒读拒写合成认证源，因而不能删除包含它的父根。认证源必须由独立清理拥有者收尾。
原业务异常已经丢失，不能从 ENOTEMPTY 推断。新演练先保存原异常，若出现新的业务失败就停下回传。

## 修改与权限

C/F/G 的既有权限规则、业务断言和用户裁定 A 均未改。只读审查发现准备函数内部也有同类问题，产品 prepare 现在要求调用方在清理前发布原异常；原异常随后原样抛出，内部清理错误单列。真实 R 入口只保存异常类型／errno，不公开原始错误文字；主失败和清理各用一个不可覆盖的 JSON。测试 R 保存完整脱敏摘要。
C 的结果在任何测试收尾动作前 fsync，以独占路径首次发布；后续只原子更新自己创建的文件。
保存原错误类型、message、code、errno、path、stack；先脱敏再公开。每个检查点另写 `.events.jsonl` 文本摘要。
清理异常逐条写入 cleanup_failures／cleanup_errors，不能覆盖 primary_failure。
R 在终止自己持有的 Git、准备函数内部私有根清理或生成认证目录删除前也先保存原异常。

| 实际进程 | 实际 profile |
| --- | --- |
| R 入口与短脱离准备 | 业务沙箱前的固定准备，仅生成／精确读取一次合成 auth；无长期监督进程，最后 exec 为 C。不开真实 auth |
| 三次只读 Git 子进程 | G，独立组；禁实际 HOME 写入、网络、Security；超时仍持有并回收原组 |
| 原 auth 读取前的基线 helper | 原产品 D，结果中标为 D_baseline；完整规则另存 profiles.D_baseline |
| 长期独立 D | 测试派生 D；保留实际 HOME 禁写、无网络／Security／fork，仅增加本次 source-home 的 file-write-unlink。可枚举该合成目录，普通文件正文仍拒读；启动时直接验证凭据文件 open 被拒、0 字节 |
| F／其 Python→Node exec | 原产品 F；只写记录目录、一个监听端口、仅配置假上游，禁止 fork／Security／其他网络 |
| 假上游 U | U，独立组；只写 U 目录、两个反例所需本地监听、无出站／fork／Security |
| 合成禁写对照 S／删合成禁写规则的 M | 原测试 S／M，独立组；实际 HOME 禁写始终存在，M 只在合成 HOME 独占新建后立即删除 |
| C 根报告进程／daemon、clang、编译子进程、PTY、shell、假 CLI、hook／inbox、事实子进程 | 同一个外层 C，后代继承；不嵌套 sandbox，不开放认证源、不新增网络或 HOME 写入 |
| 外部结果核对器 | 独立 V，禁实际 HOME 写入、网络、Security |
| 旧残留清理入口、pgrep、只睡眠的正对照 | 独立 X／继承 X，禁实际 HOME 写入、网络、Security；仅 PID 输出。正对照自身不运行 CLI／Git |

D 先执行原产品 metadata_service，取得原私有 HOME 删除收据，再等待 C 的清理许可。
许可绑定输出／候选，D 读回同一候选、同一夹具的 cleanup_pending 检查点后，才 unlink 合成 source-home。
它不读认证正文，删除收据包含 PID／组、源路径和所见检查点序号。
C 等 U 端点关闭、daemon 关闭、D 删除／退出、F/U/S/M/G 组及登记子进程均消失后，才同步删除剩余根；无法确认则保留根。
C 此后仅做同步根删除和外部结果发布并退出，V 还将退出记录与原登记身份逐项绑定，独立用信号 0 核对全部登记 PID／组和报告 PID 均已消失。删除失败也有此前已落盘的原错误。

这是测试中生成的认证源收尾权限；正式产品不会删除用户认证源。D 的这项新增权限限本次 /private/tmp 合成源，不覆盖真实 HOME。
旧七根和新残留均不原样归档，因为含合成凭据；保留文本收据后整根删除。

首轮冻结 de956c2de 的只读审查为 FAIL，原文 [CLEANUP-PUBLICATION-REVIEW-01.md](CLEANUP-PUBLICATION-REVIEW-01.md)：准备函数内部清理先于主失败、V 只信任退出布尔值。两项已补局部红绿与修正：prepare-failure-red-03／green-03，chain-cleanup-oracle-red-03／green-04。新 V 不接受“组／子进程仍存活但收据写 exited=true”的记录，也拒绝身份错配或漏登记子进程。它们仍不替代下列 OS 演练。

## 先清理唯一新残留

```sh
bash evidence/2026-10-16-batch16/T-093/CLEANUP-CHAIN-06.sh \
  /Users/luckye/Documents/Code/a2a-wt-t093 /private/tmp/t093-cleanup-07.json
```

只接受 `/private/tmp/t093-chain-e189ndt0` 的精确 source-only 形态：source-home、.claude、private-sentinel、.credentials.json。
不读这两份普通文件正文、不 chmod。原七根范围仍保留为历史显式列表，不会自动接纳新根。
R/G/C 的查询均须看见正对照，再确认对照组已退出、实际匹配为空；否则拒绝删除。
期望 rc 0、PASS、root_removed=true、permission_changes=[]。失败保留根及 path／errno，不继续演练。

## 再演练原 R/G/C 链

以下 `$candidate` 取最后 FROZEN 完整 SHA，`$repo` 为本 worktree。输出均须不存在。
没有无保护的长期 shell 监督器；每条脚本 exec 进真正的受保护链。worker 本身已在 Codex OS 沙箱内，不能施加相同嵌套 profile；按主控 #100 不重试、不请求升级。

```sh
repo=/Users/luckye/Documents/Code/a2a-wt-t093
candidate=替换为本次完整冻结SHA
bash "$repo/evidence/2026-10-16-batch16/T-093/REHEARSE-CHAIN-01.sh" "$repo" "$candidate" /private/tmp/t093-rehearsal-01-primary.json primary
```

这场故意在所有边界检查、两个真实原生 hook／Stop 周期及六种凭据注入检查完成后、正常 finalization 前抛出 `rehearsal_primary_probe`。
期望 rc 2、INCOMPLETE、primary_failure 恰为该值、cleanup_failures=[]、fixture_removed=true、upstream_requests=2；这次主动失败不是绿态。
若错误不同、清理不完整或 JSON／events 缺失，停止，回传新原件；不要继续绿态或正式链。

```sh
bash "$repo/evidence/2026-10-16-batch16/T-093/REHEARSE-CHAIN-01.sh" "$repo" "$candidate" /private/tmp/t093-rehearsal-01-green.json green
python3 -I -S -B workbench/tests/check_t093_chain_results.py --rehearsal --candidate "$candidate" \
  --output /private/tmp/t093-rehearsal-01-check.json \
  /private/tmp/t093-rehearsal-01-primary.json /private/tmp/t093-rehearsal-01-green.json
```

绿态和独立核对都须 rc 0、PASS。独立核对器重新读检查点历史、原件、上游收据、D 收据，核对退出组／子进程及报告 PID；不导入产品 helper。
它拒绝漏原件、错误计数、凭据扫描失效、源未删除、正文可读、先删源再留主失败或仍有报告进程。

## 演练两场及独立核对通过后，再跑正式六场

```sh
bash "$repo/evidence/2026-10-16-batch16/T-093/EVIDENCE-RECHECK-03.sh" "$repo" "$candidate" /private/tmp/t093-chain-07-green.json none
```

先要求 rc 0、PASS、primary_failure=null、cleanup_failures=[]、fixture_removed=true；否则停。
通过后逐场执行，均期望 rc 2、INCOMPLETE，但主失败必须恰好为下表业务断言，清理仍全部成功。

| mutation | primary_failure |
| --- | --- |
| home-references-empty | home_path_injection_must_be_reported |
| scanner-zero | credential_injection_must_be_detected |
| counts-always-match | missing_raw_request_must_be_detected |
| drop-first-record | forwarder_record_count_must_match_upstream |
| empty-credential-cases | credential_injection_cases_must_not_be_empty |

```sh
bash "$repo/evidence/2026-10-16-batch16/T-093/EVIDENCE-RECHECK-03.sh" "$repo" "$candidate" /private/tmp/t093-chain-07-home.json home-references-empty
bash "$repo/evidence/2026-10-16-batch16/T-093/EVIDENCE-RECHECK-03.sh" "$repo" "$candidate" /private/tmp/t093-chain-07-scanner.json scanner-zero
bash "$repo/evidence/2026-10-16-batch16/T-093/EVIDENCE-RECHECK-03.sh" "$repo" "$candidate" /private/tmp/t093-chain-07-counts.json counts-always-match
bash "$repo/evidence/2026-10-16-batch16/T-093/EVIDENCE-RECHECK-03.sh" "$repo" "$candidate" /private/tmp/t093-chain-07-drop.json drop-first-record
bash "$repo/evidence/2026-10-16-batch16/T-093/EVIDENCE-RECHECK-03.sh" "$repo" "$candidate" /private/tmp/t093-chain-07-empty.json empty-credential-cases
python3 -I -S -B workbench/tests/check_t093_chain_results.py --candidate "$candidate" --output /private/tmp/t093-chain-07-check.json \
  /private/tmp/t093-chain-07-green.json /private/tmp/t093-chain-07-home.json /private/tmp/t093-chain-07-scanner.json \
  /private/tmp/t093-chain-07-counts.json /private/tmp/t093-chain-07-drop.json /private/tmp/t093-chain-07-empty.json
```

正式独立核对须 rc 0、PASS、六场 pass=true；每场保留 JSON 和同名 `.events.jsonl`。本轮没有运行这些外部命令。
当前六条 Acceptance 的历史索引见 RESULTS；main 红态／原始 probe 边界仍保留，完整链证据不能从旧候选沿用为本候选通过。
