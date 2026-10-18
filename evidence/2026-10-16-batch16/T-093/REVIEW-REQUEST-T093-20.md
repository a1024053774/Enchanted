# T-093 第三轮 P1 修正：恢复白名单

**INCOMPLETE：局部红绿通过，新候选 T-096 原生七场与后续独立审查／门禁待完成。** task T-093 / attempt a1，worker s16-t093，session 67f986cc-92e4-4089-9c22-802a1143b645；基线 788d75f4a75a861a7beb23f3f0ac97a6ecc70938。最终候选绑定本轮末行 `T-093 FROZEN <完整 SHA>`。不 push、不 rebase、不改 gates／acceptance／地图或全局配置；不跑真实模型。

## 原问题与裁定

主控 #129 转交 [independent-review-03.md](independent-review-03.md)，结论 NO_GO。报告与 REVIEW-OUTSIDE-04.sh 按原字保留。P1：单看 authentication，正常登录缺该字段就进入普通恢复；真实 claudeLaunch 生成记录的给定边界探针观察到版本 1／PTY 1／pane_restored。第三轮对网络两层、运行身份、libproc、原件／凭据及限制披露的其他结论按其原范围保留。

本次依主控裁定改为白名单、默认拒绝：只恢复能正面认定的 T-096 假 API 主控，合法旧记录可无 authentication；正常登录及无法识别记录均在任何 CLI 前保持未恢复，不重建 R/F/D/C、不扩大 T-096。

## 机械识别与不变部分

白名单来自实际 fd5c93e6e／当前 claudeLaunch 记录，而不是以“不是 normal”作准入：controller／Claude Code／既有 preset、zsh，P1 role_card_revision，公开假 token、规范 loopback http origin／合法显式端口、规范 /private/tmp HOME／config 同时匹配。认证字段只能缺省或为 isolated fake API only；未知认证、NODE_OPTIONS、API_KEY／OAuth token 不进入此合同。判定只读内存字段和纯路径／URL，不读 auth、文件或钥匙串。

任何已知正常登录标记优先拒绝：authentication、T-093/normal-login/ role revision、login audit/preflight、T-093 hook 授权、profile process log、a2a-claude-login 私有 HOME/config、已知 trace loader。返回 normal_login_restore_requires_protected_start 和原中文重启指引。其余不满足白名单者返回 restore_record_unrecognized；旧窗格／位置与历史记录保留。允许的假 API 才继续原 argv／task／版本／session／shell／规范执行路径／实际前台 leader 检查。worker attempt reclaim 规则不变。

没有增加恢复 fallback、默认 argv、固定 leader、版本或 session 绕过。仅 panes.ts 与恢复测试改变；controller_start、hook／Stop、转发器、OS profile、事实脚本、processSnapshot 不改。

## 红绿与反例

- restore-whitelist-red-20.json／red-command：精确 git-show 788d75f4a 与 reviewer 候选源码逐字相同；同探针实际生成输入只删除 auth，观察版本 1／PTY 1／pane_restored，rc 2。scratch 和输入路径迁移到新根，不改旧现场。
- reviewer-replay-green-20.json：同 reviewer 案例／oracle，正常及缺 auth 正常均版本=PTY=0、明确错误；fake／legacy-fake 各正常恢复，历史不变。恢复输入来自实际 claudeLaunch 的原合成记录，未手造其形状。
- restore-contract-red-20-02.json：扩展合同在 788d75f4a 上命中 Normal-login restore must stop before version, identity and PTY boundaries；文件为 INCOMPLETE／rc 1，保留原字作为业务红态。
- restore-contract-green-20-03.json：10 个正常登录／部分标记、12 个未知、2 个无 auth 的旧假 API、1 个显式假 API、1 个 worker 有逐项调用数／错误／历史观察；另保留缺 argv／错误版本／缺 session、失败兄弟隔离、保存位置／空集、完整实际 shell argv、规范身份三模式与 worker attempt 不变。两个旧缺 executable_path／auth 正例未删除，补齐真实 P1 合同元数据。
- 复原单 auth guard、分别删 P1 revision／公开假 token／loopback URL 证据、截实际 argv、删已有身份一致性、固定 leader、历史 worker 坏实现均被对应业务断言拒绝。没有用集合为空或环境崩溃冒充检出。
- T-091 IPC 19 项、T-096 daemon 7 项局部回归通过；均无真实 CLI／OS 查询，不代替新七场。旧 r18b 原生 PASS 只绑定旧恢复入口。

可重放给定边界探针（输出须全新，不执行真实 CLI）：

```sh
python3 -B evidence/2026-10-16-batch16/T-093/REPLAY-RESTORE-PROBE-20.py --revision 788d75f4a75a861a7beb23f3f0ac97a6ecc70938 --output /private/tmp/新的白名单红态.json
python3 -B evidence/2026-10-16-batch16/T-093/REPLAY-RESTORE-PROBE-20.py --output /private/tmp/新的白名单绿态.json
node --experimental-vm-modules workbench/tests/test_t096_restore.mjs /private/tmp/新的恢复合同.json
```

第一项预期 rc 2、FAIL；后两项 rc 0、PASS。REVIEWER-RESTORE-PROBE-20.mjs 和 generated-normal-record-review03-20.json 是 reviewer 原文／合成输入的原字副本；helper 只把 scratch／模块依赖 URL 和输入目录前缀迁移到新根。真实 auth 读取、模型、CLI／PTY 实际执行和 OS profile 操作均为 0，所有调用来自给定边界。

## 主控沙箱外：新候选七场

下面使用已修正 T096-REGRESSION-16.sh，output 始终是 `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-096/<label>`，原件写本次全新 run/archive 摘要，不覆盖 r18b。源码 HEAD 必须等于完整候选、src/tests 清洁、外置盘挂载且输出新；不回退内置盘。CLI 路径取已核对的 2.1.302，仍由执行主控逐屏批准六键及 startup-ready；模型／fake POST 预算 0。

```sh
repo=/Users/luckye/Documents/Code/a2a-wt-t093
candidate=替换为本轮完整冻结SHA
cli=/Users/luckye/.local/share/claude/versions/2.1.302
approval=主控本轮逐屏初始化批准记录位置
resume="$repo/evidence/2026-10-16-batch16/T-093/T096-REGRESSION-16.sh"
bash "$resume" tracer "$repo" "$candidate" "$cli" "$approval" t093-r20-tracer-01
```

先核对 tracer rc 0／PASS、同原 session／历史 nonce、完整事件与内核 argv、规范身份、原 launch 不变、关闭持久化、model_turns=fake_posts=0、cleanup_complete=true。任一失败保留现场即停，不继续后场、不自动补按键；按主控原裁定交回处理。

tracer 通过后逐场运行，出现失败同样停：

```sh
bash "$resume" three "$repo" "$candidate" "$cli" "$approval" t093-r20-three-01
bash "$resume" missing-argv "$repo" "$candidate" "$cli" "$approval" t093-r20-no-argv-01
bash "$resume" version-mismatch "$repo" "$candidate" "$cli" "$approval" t093-r20-version-01
bash "$resume" missing-session "$repo" "$candidate" "$cli" "$approval" t093-r20-no-session-01
bash "$resume" isolation "$repo" "$candidate" "$cli" "$approval" t093-r20-isolation-01
bash "$resume" empty-reopen "$repo" "$candidate" "$cli" "$approval" t093-r20-empty-reopen-01
```

three 须两主控恢复、worker 未恢复／receiver 未重启／无成功事件且 attempt 不变；三个单故障仍为 restore_argv_missing／restore_version_mismatch／restore_session_missing、保留未恢复／只读；isolation 中 executor 仍正常恢复；empty-reopen 第三窗口 panes／keys=[]、saved=true，不重新授权 worker 或改 task。全部 rc 0／PASS、cleanup=true、模型与 fake POST 0。原生旧记录缺字段正例仍由 L1 合同覆盖，不冒称这七场新生成原生记录就是它。

其余两层网络／HOME 用户裁定 A／probe-10 的三边界／libproc 全 pane 影响与 T-091/T-078 范围仍见请求 19 和第三轮原文；本次不把其余 PASS 扩大成真实上游或模型验证。新七场回传后，由执行主控安排后续独立审查与唯一门禁；此冻结不代替 submit／验收／集成。
