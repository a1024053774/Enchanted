# T-078 #188：09B driver/oracle 与可执行包交接

已完成纯夹具阶段（无 socket、CLI、daemon、目标、模型）：

- red：登记 dispatch 正文与观察正文差一字符，oracle 拒绝；
- green：I=4/6、E=6/11、合计17，真实 stop/request/inbox/ack IDs，dispatch.seq 全局连续，反馈正文绑定登记文本；
- 反例：seq-reset、identity、duplicate-esc 分别被独立 oracle 拒绝。

实现见 `workbench/tests/t078_09b_driver.py`，说明见 `09B-DRIVER.md`。driver 中 I/E 阶段按预算展开，不写死 `#1/#2`，target 的 attempt/session/fence/leader/native/session 和 received bytes 都是 oracle 输入；operator 不执行业务动作。

请按原身份运行：

```sh
sh /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/commit-09b-driver.sh
```

脚本固定 HEAD `50efd2f0f6f27fffa89d8609c5d952906cd1125a`、task/session、暂存区和 allowlist；第一提交冻结产品前置、driver、red/green/反例与文档，随后静态生成全新 `09b-executable-materials-01`：两个角色 approval、独立目录、共用 broker/state/repo、target card（`oracle_paths`）、空审批和 source tar。第二提交冻结材料。

生成包明确 `launch_status=NO_GO`：target claim 尚未从真实 dispatch/claim 取得，不能用 null 或假 attempt/fence；材料生成只构造 argv，不启动任何真实 CLI/API/目标。批准前不做真实运行。09B 真实红绿／权限反例、09C 和独立 reviewer 仍 INCOMPLETE。

T-078 09B-DRIVER READY
