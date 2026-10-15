# T-078 主控 #185：green-3 收尾与 09B 计划材料审阅

green-3 已实跑并读回 **PASS**：三次 API Messages，ACK／FINAL_ACK，真实 Stop 的 inbox_list 只执行一次，ideation scope sentinel 正确，反馈第二根到达；intent2、turn_end2、idle2，许可 Enter 为 control action，无 user intent。读回见 `slice1-green-3-closeout/readback.json`。供应商模型0；范围只到单角色真实假服务闭环，不替 09B／09C／整票验收。

先运行：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/cleanup-slice1-green-185.py --approval-ref "主控 #185"
```

脚本固定核对 root `/private/tmp/t078-2-p1-slice1-green-3-jzfi4ju5`、launch/session、API49173、daemon49190、CLI49211、shell49210 的命令/root、PIDfile和双读 lifetime；认证 daemon_stop 后确认三服务退出，API 最多一次 SIGTERM；外置逐成员归档读回后删除成功 root。slot 另列，保持不动。只有 cleanup PASS 才运行提交脚本。

然后运行：

```sh
sh /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/commit-closeout-and-09b-materials.sh
```

脚本以原启动身份固定当前 HEAD `b5b8b165d06c5cc5ab341c965679d7932d74c8a3`；先提交 green-3 读回、#184 修复结论、cleanup 与计划材料脚本，再静态生成 `09b-materials-01`，Git/tar逐文件核对，第二次提交材料。没有启动 CLI/API/Electron/确定性目标，也没有删除 slot。

09B 仅计划审阅，`launch_status=NO_GO`：一套新 broker/state/repo/project/task，两个实际 Claude 角色（独立 HOME/config/tmp/shell/requests/hooks/user-data）、一个受管确定性目标，真实 dispatch/claim 取得 attempt/session/fence/worktree，材料不伪造身份。建议 ideation 4根/6 Messages、executor 6根/11 Messages，合计17，模型0，保留逐屏/每次工具一次 Yes 和身份／role／scope／ack／重复副作用反例。当前 P1 共享六目录且只支持 1/2 根；此最小前置已取静态 PASS 并上报 `ISSUE-09B-PROFILE-PRECONDITIONS.md`，需审阅后实现，不绕过。

审阅入口：[09B-MATERIALS-REVIEW-01.md](09B-MATERIALS-REVIEW-01.md)，包内含空 launch/actions 审批模板、协议、独立 oracle、任务卡（含 `oracle_paths`）、角色卡和预算。09C 仍等待 09B 实际通过后单独冻结；不启动、不关闭 T-078、不集成/push。

T-078 09B-MATERIALS READY
