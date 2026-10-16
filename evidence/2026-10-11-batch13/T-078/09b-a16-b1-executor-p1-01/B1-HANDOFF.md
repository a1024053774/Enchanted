# A-16 executor B1 与排队期间首启（主控 #347，仅备材料）

材料绑定实际 A-16 readiness、源码 `7a6edbff87df85077b3a05d38f3cfd5654cde9c1`、`09b-executable-materials-16-02` 和 I1 `execute-02/result.json`。生成器已只读核对真实 relay 的 pending 收据；本轮只写 executor P1、隔离配置、protocol-plan 与空签字材料，未启动executor CLI、B1 dry-run、读屏、发键或release。

沿用 root `/private/tmp/t078-2-09b-run-z9ov_cco` 与既有 executor API34331/64319，`api_url` 保持 `http://127.0.0.1:0` 模板，由既有 ready/完整argv/lstart核对解析；不会启动第二只 API。原stop为 `d48f9f7c-187e-4fcd-b125-58ec345710b6`，`created_at=2026-10-16T21:06:39.345Z`，不得重置时间或重新send；本材料不填假dispatch id/seq。

## 主控单步执行

1. 核对并签 `stage-b-approval.json`，binding逐字取本次readiness，两项签字目前均空。
2. 从 `B1-COMMANDS.txt` 先单独取第一条dry-run；预期 READY_FOR_ROLE、无spawn。失败停止，不能接着执行real。
3. dry-run通过后单独取第二条real，只启动executor到首屏；启动后的原stop只应排队，unknown首启期间不得paste/提交或标delivered，executor应0 POST。
4. real PASS 后执行 `BIND-LAUNCH.txt`，从真实result与manifest核对launch/session并填入实际label；完成前不得运行含 `LAUNCH_LABEL` 的首启命令，不复制manifest。
5. `ONBOARD-COMMANDS.txt` **一条一条执行**：先读原屏、核对、签对应草稿、只发这个键，随后执行紧跟的 `observe-startup-queued.py`，通过后才看下一屏/签下一键。不得整文件连续执行，不得先initial release。

| 原屏 | 键 | 单键purpose | 键后检查 expected-keys |
|---|---|---|---|
| s1主题：Dark→Auto | ArrowUp | onboarding-theme | 1 |
| s3主题：Auto→Dark | ArrowDown | onboarding-theme | 2 |
| s5主题：Dark | Enter | onboarding-theme | 3 |
| s7 Security notes逐字核对 | Enter | onboarding-notice | 4 |
| s9信任：No→Yes | ArrowDown | workspace-trust | 5 |
| s11信任：光标在Yes | Enter | workspace-trust | 6 |

B1整体计划仍是带原文的 `security-notice`，只有s7单键purpose为 `onboarding-notice`。信任用ArrowDown到Yes，再单独Enter，不用Digit1或默认Enter。六份单键批准均未签；每份绑定本次launch/session、夹具repo、screen_id/key/purpose和该原屏文件。

初读不符时用该屏 `-02` 新label独立重读，不发键、不覆盖初读；若采用-02，批准与键命令的screen_file同时改指它。每次按键后若采集报错，先保留原结果、核对written，不把它当作未送达而重按。本场冻结工具不变，后续动作由主控按实际收据决定。

每次queued读回都通过真实 `inbox_list` 刷新原条目收据，核对 `created_at` 未变、仍queued、历史没有delivered、pane unknown/active null、队列对应原条目、业务输入0、I2未登记、累计首启键数恰为1～6。它不是业务派发/中断/ack；任一不符即停，不能继续下一键。s13只读空提示符/manual，**不自动确认readiness、不release、不运行E1**；I2 arm和E1初始release另批。

## 完整读屏与原件

所有screen及键后快照继续用冻结的 `p1_output.read_complete_output`，offset0分页至固定total/EOF，完整保存screen.bin与页范围；总长变化/缺页/零进度/无EOF拒绝。相对A15只换本次真实绑定，没有改reader、观察器或产品源码。

两角色逐POST request/response/meta与hooks stdin/started/finished/stdout/stderr留在实际role目录，rev2捕获接口不收认证头。I1的两POST原件仍在活root，尚未外置归档；不能以本轮summary替代。两角色真实B1 manifests齐全后按主包BIND-OWNER命令建owner；结束前先capture、外置归档逐成员字节读回、从tar独立重数并保留每原件archive指针，再单独批准正常停机/删root；停机后不读SQLite。

预算保持 ideation4根/6 POST、executor6根/11 POST、全场17 POST、模型0。I1已用ideation1根/2 POST；executor首启预期0根/0 POST。生成器附带的E阶段草稿同样未签，本轮只交B1/首启。
