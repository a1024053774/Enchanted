# T-093 可配置测试端口与 U 启动失败收尾

**INCOMPLETE：局部红绿通过；本候选的 OS 编译、完整无模型链和 T-096 原生七场待主控沙箱外运行。** task T-093 / attempt a1，worker s16-t093，session 67f986cc-92e4-4089-9c22-802a1143b645；基线 7bba61000d8ae5b643135b58111768a403a5d04c。最终候选绑定末行 `T-093 FROZEN <完整 SHA>`，不 push、不 rebase；冻结不代替 submit／验收／集成。

## 外部事实与修正范围

主控 #126 已在基线上取得生产 F 的 443 profile 编译 PASS。primary／green 均在 U 启动阶段以 fake_upstream_listener_unavailable、errno 13 失败，cleanup_failures=[upstream_shutdown_unconfirmed]；两个夹具已删除，无残留。小摘要为 [os-r17-failure-summary-18.json](os-r17-failure-summary-18.json)。主控另确认用户的 IPNExtension/Tailscale 占用 IPv4／IPv6 *:443，worker 没有对它查询、停用或修改，也没有申请升级。

生产入口 claudeLoginSession.py 的 main 显式调用 `prepare(..., upstream_port=443)`，不新增生产端口 CLI 选项；原非 443 提前拒绝、一次精确 auth 读取及所有其他权限不变。测试入口 run_t093_login_chain.py 通过 `--upstream-port`（默认 18443，范围 1024～65535）调用同一个 prepare，随后同一个 **claudeLoginSession.policies(session)** 从 session.upstream_port 生成 `remote tcp4 "*:<port>"`。没有第二套 F profile 或在生成后的 F 中替换规则。局部检查逐字比较：把测试 F 的端口恢复为 443 后与生产 F 相等，C／D 原字节相等。编译脚本也直接调用同一函数，分别编译生产 443 和测试端口，各跑 loopback／文档地址两场，只编译、不连接。

事实中的 network_boundary 报告实际端口；链路另记录 port_configuration：generator=claudeLoginSession.policies、production_upstream_port=443、test_upstream_port=所选端口。V 从自己的端口参数核对，不能把测试的非 443 报成生产 443。**OS 层不再按主机限制**；F 应用层固定配置主机、不跟随重定向、不受入站 Host 改目标的行为没有修改。测试仍保留活跃的另一个本地端口，F 必须被 OS 拒绝访问；C 直接访问 U 必须被拒绝；非配置主机由实际 handler＋给定 transport 的反例拒绝，不联网。

U 原先在 try 抛绑定错误后，虽然 finally 执行 close，但位于 finally 之后的 closed.json 不会写出。现把关闭收据放在 finally：记录 startup_completed、listeners_bound、closed_listeners、all_closed、close_errors。每个已构造的监听器都尝试关闭；关闭错误单列，不盖掉原始绑定异常。即使零监听也须收据，C 核对 PID／pgrp、计数与 all_closed，再在原 5 秒窗口等待 ESRCH。永久 EPERM、活进程、缺收据、错误收据仍失败；最终每条 writer 的屏障和主失败先落盘规则未变。V 还要求完整运行的 U 成功启动两监听、关闭两监听且拥有者匹配。

## 局部证据与边界

- port-generator-red-18.json 拒绝旧生成器硬写 443；port-generator-green-18.json 的 10 项包括多个端口／地址、C／D 不变、默认非 443 提前拒绝、测试端口匹配／不匹配和生产入口明确 443。没有调用 OS 编译或 auth。
- upstream-startup-red-18-02.json 拒绝旧 U 的零监听／部分监听无收据及关闭错误掩盖原异常；upstream-startup-green-18.json 四场通过。upstream-skip-close-mutant-18.json 删除真实 close 调用后被 receipt_must_count_actual_listener_closes 拒绝。
- upstream-shutdown-red-18.json 在 7bba61000 的旧 C 回调上抓到未核对 all_closed；green-18 十场验证零／部分监听收据、关闭失败、缺收据、瞬时／永久 EPERM 与活进程。writer-exit-green-18.json 七项仍拒绝每条 writer 的未知退出。
- wrapper-port-red-18.json 拒绝未传端口的旧脚本；wrapper-port-green-18.json 用实际系统 Bash 的 exec 哨兵核对默认 18443／显式 51943，共十四分支，无真正委派。counts-selection-green-18-02.json 十三项核对 V，保留未知权限／活 writer／错误主失败／候选／场次／缺六场，并新增错误端口、U 未关闭和错误拥有者。
- session-once-green-18.json 和 session-test-port-green-18.json 验证事实分别报告 443／18443；prepare-failure-green-18.json 三项、session-cleanup-green-18.json 五项、upstream-prompt-green-18.json 精确 JSON 十三项、host-lock-green-18-02.json 五项通过。应用主机锁代码未修改。
- 首次 upstream-startup-red-18.json 的 AST 取样漏掉旧 try 之后的正常关闭语句，已保留，不用它证明旧正常路径缺收据；最终 red-18-02 覆盖完整尾段。首次 host-lock-green-18.json 误漏 `--experimental-vm-modules`，五项为 vm.SourceTextModule 环境错误，不作业务红态；补该参数后的 -02 为实际局部绿态，C 原调用本来就带该参数。

正常登录不自动恢复的 #125 限制、假 API／legacy 正例和此前独立局部 PASS 仍保留，panes.ts／恢复测试本轮未改。probe-10 的三个边界不变：2.1.302 内部 onboarding／唯一 cwd trust 状态升级须重核；官方 hello 候选不经 BASE_URL，必须避免且报告可见迹象，不能把沉默被拒当零尝试；失败与重试逐次计数。用户裁定 A 的真实 HOME OS 禁写及各反例、清单仅报告、凭据／正文不进证据规则不变。R 之外的 C/F/D/U/S/M/G/V 仍各按既有单层／平级 profile 身份运行；除测试上游端口替换，其他权限不变。

## 主控沙箱外命令

只设置测试端口；不是生产配置。不覆盖旧结果；整轮保持同一个值，冲突即停，不自动换端口或动用户服务。若需改值，另起全新输出名。先填本轮末行完整 SHA：

```sh
repo=/Users/luckye/Documents/Code/a2a-wt-t093
candidate=替换为本轮完整冻结SHA
export T093_TEST_UPSTREAM_PORT=18443
osrun="$repo/evidence/2026-10-16-batch16/T-093/T093-OS-16.sh"
bash "$osrun" compile "$repo" "$candidate" /private/tmp/t093-r18-compile-01.json
```

要求 rc 0／PASS，四项均 compiled=true、same_generator_only_port_changed=true；生产 OS_remote_ports=[443]，测试为所选端口。它只是编译证明，不是 443 实际出站证明。失败即停。

```sh
bash "$osrun" primary "$repo" "$candidate" /private/tmp/t093-r18-primary-01.json
```

只接受 rc 2 且 primary_failure=rehearsal_primary_probe：两条精确 U 收据、先记后转、非配置端口 OS 拒连、应用主机拒绝、C 绕行拒绝成立，cleanup_failures=[]、fixture_removed=true、U 的两监听均关闭且最终 writer 逐项确认。任何其他失败都停；不要像上一轮那样 primary 失败后继续 green。

```sh
bash "$osrun" green "$repo" "$candidate" /private/tmp/t093-r18-green-01.json
bash "$osrun" verify-rehearsal "$repo" "$candidate" /private/tmp/t093-r18-rehearsal-check-01.json /private/tmp/t093-r18-primary-01.json /private/tmp/t093-r18-green-01.json
```

两项均 rc 0／PASS 后再逐场运行，任一主失败不符或清理不完整即停：

```sh
bash "$osrun" none "$repo" "$candidate" /private/tmp/t093-chain-11-none.json
bash "$osrun" home-references-empty "$repo" "$candidate" /private/tmp/t093-chain-11-home.json
bash "$osrun" scanner-zero "$repo" "$candidate" /private/tmp/t093-chain-11-scanner.json
bash "$osrun" counts-always-match "$repo" "$candidate" /private/tmp/t093-chain-11-counts.json
bash "$osrun" drop-first-record "$repo" "$candidate" /private/tmp/t093-chain-11-drop.json
bash "$osrun" empty-credential-cases "$repo" "$candidate" /private/tmp/t093-chain-11-empty.json
bash "$osrun" verify-six "$repo" "$candidate" /private/tmp/t093-chain-11-check.json /private/tmp/t093-chain-11-none.json /private/tmp/t093-chain-11-home.json /private/tmp/t093-chain-11-scanner.json /private/tmp/t093-chain-11-counts.json /private/tmp/t093-chain-11-drop.json /private/tmp/t093-chain-11-empty.json
```

none 预期 rc 0／PASS；五变异 rc 2、主失败依次为 home_path_injection_must_be_reported、credential_injection_must_be_detected、missing_raw_request_must_be_detected、forwarder_record_count_must_match_upstream、credential_injection_cases_must_not_be_empty；每场 cleanup=[]、fixture_removed=true，V rc 0／PASS。保留 JSON 与 events 原件；均只用假 CLI／合成 auth／本地 U，真实模型／真实上游／真实 auth 读取 0。

T-096 七场使用最终候选和全新标签，仍逐屏批准初始化；先 tracer，通过再继续，失败交主控重开 T-096。原外置盘／模型与 fake_posts=0／完整 argv／worker attempt／empty-reopen 断言全部沿用，不因换测试端口放宽：

```sh
resume="$repo/evidence/2026-10-16-batch16/T-093/T096-REGRESSION-16.sh"
cli=/已核对的Claude_Code_2.1.302可执行文件绝对路径
approval=主控本次运行授权位置
bash "$resume" tracer "$repo" "$candidate" "$cli" "$approval" t093-r18-tracer-01
bash "$resume" three "$repo" "$candidate" "$cli" "$approval" t093-r18-three-01
bash "$resume" missing-argv "$repo" "$candidate" "$cli" "$approval" t093-r18-no-argv-01
bash "$resume" version-mismatch "$repo" "$candidate" "$cli" "$approval" t093-r18-version-01
bash "$resume" missing-session "$repo" "$candidate" "$cli" "$approval" t093-r18-no-session-01
bash "$resume" isolation "$repo" "$candidate" "$cli" "$approval" t093-r18-isolation-01
bash "$resume" empty-reopen "$repo" "$candidate" "$cli" "$approval" t093-r18-empty-reopen-01
```

逐屏步骤仍见 [T-096 RUN-RESTART](../T-096/RUN-RESTART.md)。外置盘未挂载则报错，不回退；这组真实假 API 恢复不用上面的测试端口参数，也不运行模型。Panes.processInfo/libproc 影响及 T-091/T-078 回归说明仍见请求 13／16，不能用局部 mock PASS 替代本次原生七场。
