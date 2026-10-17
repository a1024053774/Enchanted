# A-16 ideation B1 与首启材料（主控 #345）

**材料准备 PASS；B1 dry-run、真实启动、读屏和按键均未运行。** 本轮只调用已冻结的 `prepare-a14.py --mode role` 写文件；没有启动 executor、daemon/API/角色 CLI、Electron或模型，没有派发/release/输入。Stage A 是主控已运行的独立结果，不把它算作本轮启动。

本套绑定 `09b-a16-stage-a-01/readiness.json` 的实际 attempt、root `/private/tmp/t078-2-09b-run-z9ov_cco`、源码 `7a6edbff87df85077b3a05d38f3cfd5654cde9c1` 与 `09b-executable-materials-16-02`。复用 ideation API PID34330、端口64318；`input.api_url` 保持模板 `http://127.0.0.1:0`，由既有复用解析器按 ready/完整argv/lstart解析，绝不起第二只 API。

## 主控逐步执行

1. 核对并签 `stage-b-approval.json`。真实目标 binding 逐字取自本次 readiness；`approved_by`、`approval_ref` 目前均空。
2. 从 `B1-COMMANDS.txt` **单独复制第一条** dry-run。预期 READY_FOR_ROLE、spawned/p1_spawned/cli_spawned 均false。失败停，不能接着跑 real。
3. dry-run通过后，**单独复制第二条** real。只启动 ideation，到首屏前停止；不自动读屏/发键。P1 的“尚未发输入，待独立screen”是启动范围提示，不代表首启完成。
4. real PASS 后执行 `BIND-LAUNCH.txt`。它读取实际 B1 result 和 process-manifest，核对 launch/session，再将 `ONBOARD-COMMANDS.txt` 中的 `LAUNCH_LABEL`（以及阶段材料的 `LAUNCH_MANIFEST`）替换成真实路径。该步骤前不得执行带占位符的首启命令，不复制/伪造 manifest。
5. 按 `ONBOARD-COMMANDS.txt` **一次只选一条命令**：先读 s1 原屏，核对后才签对应 `onboarding/` 草稿、执行这一个键；发完停下读下一屏。绝不把整份命令文件作为脚本连续运行。

| 原屏 | 单键 | 预期选择/文字 | 单键 purpose |
|---|---|---|---|
| s1 主题 | ArrowUp | Auto (match terminal) | onboarding-theme |
| s3 主题 | ArrowDown | Dark mode | onboarding-theme |
| s5 主题 | Enter | Dark mode | onboarding-theme |
| s7 安全说明 | Enter | 与 B1 screen_text 原文逐字核对后 Continue | onboarding-notice |
| s9 信任 | ArrowDown | Yes, I trust this folder | workspace-trust |
| s11 信任 | Enter | 光标确在 Yes, I trust this folder | workspace-trust |

B1 的整体屏幕计划沿冻结格式保留 `security-notice` 和 `screen_text`；s7 单键入口使用 `onboarding-notice`。信任不使用 Digit1 或默认 Enter。六份单键草稿均留空签字，分别绑定自己的 launch/session/directory/screen_id/key/purpose/screen_file；动作如实记为批准的测试自动化。

每次初读不符，停下、用同屏 `-02` 读屏命令重读，不发键；若采用 `-02` 原件，签字草稿的 `screen_file` 与该键命令的 `--screen-file` 都改指这份原件。不得覆盖初读。s13 只读空提示符/manual，仍不发业务输入，不自动确认 readiness 或 release。

## 完整读屏与原件保留

所有 screen/key 后快照都经冻结的 `run_t078_p1.py → p1_output.read_complete_output`，从offset0分页到固定total并确认EOF，保存完整 `screen.bin`、`screen.json.capture` 的页/范围；total变化、缺页、零进度或无EOF均拒绝。没有复用旧64KiB单页路径。B1到首启应为0 Messages；若出现HTTP POST/409、意外业务输入、额外根或任何界面不符，停下保留原件，不重试、不默认批准。

原件沿 rev2：两角色 `http-exchanges/` 的逐POST request/response/meta、requests/responses日志及 `hooks/<trace-id>/stdin.bin`、started/finished、stdout/stderr都保留；不删除、不以汇总替代、不抓取认证头。P1 sources中包含实际API、`t078_raw_retention.py`、reader及三个调用者闭包，ready协议为 `rev2-raw-c-profile-v1` / `rev2-registered-raw-v1`。

完整 owner 待两角色真实 B1 manifests 齐全后，用主包 `BIND-OWNER-COMMAND.txt` 生成，不能现在填假PID。回收前按 rev2 先 capture（停机前导出库行、只收列明原件、结构脱敏）、外置归档逐成员字节读回、从归档独立重数并留每原件 `*.archive.json` 与 `bundle.archive.json`，通过后才单独批准 finish 正常停机/删root；停机后只验文件及关停尾部，不读SQLite。此处只有保留约束，没有运行采集/归档/清理。

预算不变：ideation四根/六POST，executor六根/十一POST，模型0。此处只备ideation首启；生成器顺带产生的 phases 草稿同样未签，本轮不批准执行。
