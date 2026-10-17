# P1 同实例续跑：continue-05b

2026-10-13，主控 #93 的失败已定位为探针材料交接缺失。**诊断／静态准备 PASS；实际 continue 仍 INCOMPLETE／待审批。** 本轮未调用 CLI、后台 socket、ps 或信号，未向现有窗格发送输入、未重启或 cleanup。

## 原因与最小修复

原 continue 读取 `/private/tmp/t078-2-p1-05-sgtocfk7/initial-ready.json`，但该文件未生成；主控的就绪观察和 continue 批准已经存在于消息 #93 与决定 04。其余输入、API 端口和 runtime manifest 均存在，源码与首次启动快照逐字节一致。只读结果见 [diagnosis](p1-continue-diagnosis-05b.json)。原 `p1-materials-05/continue/result.json` 保留；commands.jsonl 实际不存在，command-output 为空，假 API 请求与 release 文件也不存在。

runner 现显式接受 `--readiness-file`，不再假定主控另有一个未生成的根目录文件，不自行把未知状态当作已批准。材料中的 confirmed_by=executor 指确认就绪的来源；prepared_by=worker:s13-t078s 指 JSON 的整理者，二者分开。依据是主控已报告的提示符、无主题／key／信任提示，以及 `T-078 controller-decision-04 p1-05-continue`。这份就绪确认不替代本次 continue-05b 执行审批。

异常结果新增完整 traceback 和 error_filename。主控给出的原失败为真实红态；[诊断合同检查](p1-continue-diagnostic-contract-05b.json) 用安全的只读缺失文件输入执行原快照／候选的真实异常处理块，确认旧版丢失路径与 traceback、候选保留。它只验证错误记录，不冒充完整 continue 已运行。

为了不覆盖原失败，runner 支持显式输出 label 和本次 driver 快照。修改仅为 runner、outside wrapper 与 README；所有 `workbench/src` 产品源码、API 实现、现有 CLI 参数、环境、hooks 和角色卡保持启动 05 时的原字节。新快照不会替换旧 `sources.tar.gz` 或修改数据库启动记录。

## 相同实例与参数

仍使用材料 05 的实例根、launch `776a1e76-12d3-46bd-801d-2f6b29a4eb2a`、session `5cba7310-f985-4003-b94e-04345c41518a`，API 端口 50845；不重新启动 API、后台或 Claude。继续前再次核对原 runtime manifest、API ready 绑定、就绪文件，以及原 process-manifest 中 CLI PID／启动时间／命令。身份变更、缺文件或无法核对即停，不重新寻找或替换实例。

同实例材料：[readiness.json](p1-resume-materials-05b/readiness.json)、[binding.json](p1-resume-materials-05b/binding.json)、[主控决定原文](p1-resume-materials-05b/controller-decision-04-update-93.md)、[driver-only.diff](p1-resume-materials-05b/driver-only.diff)、[源码快照](p1-resume-materials-05b/sources.tar.gz)、[静态准备](p1-resume-materials-05b/preparation.json)。[ready-screen.bin](p1-resume-materials-05b/ready-screen.bin) 是整理时只读复制的原始终端输出；不据此自动判断状态或权限。

审批后运行的准确 driver argv 是：

```sh
/usr/bin/python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/workbench/tests/run_t078_p1.py --materials /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/p1-materials-05 --phase continue --label continue-05b --source-materials /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/p1-resume-materials-05b --readiness-file /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/p1-resume-materials-05b/readiness.json
```

控制端环境仍为原材料 05 的白名单及本实例 operator 凭据路径；不读或复制用户认证，也不改变实际调用者的后台认证。只有确认通过后，才放行该主控并经登记的 bracketed paste＋单独回车发送原 nonce 一次。Messages 请求预算仍为 1，真实模型预算 0，无 Codex 回合。协议、hook、身份、忙闲或完成计数不符合即停，不重试；任何批准／目录信任提示保留原文，不按键或选默认。

实际输出将写 `p1-materials-05/continue-05b/`；原 `continue/` 原样保留。不会自动 cleanup。`p1-cleanup-05b` 使用同一新 driver 快照、原进程绑定与独立 `cleanup-05b/`，须主控读回后安排；退出核对修复仍待真实复验。

## 交执行主控的阶段

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh p1-continue-05b
```

准备命令为 `python3 -B evidence/2026-10-11-batch13/T-078/prepare-p1-continue-05b.py`；诊断合同命令为 `python3 -B evidence/2026-10-11-batch13/T-078/check-p1-continue-05b.py`。二者只适用于保留的该实例；重放须使用新产物标签，不能覆盖旧目录。实例若已被清理或退出，应先交主控决定，不能用此材料自动重开。
