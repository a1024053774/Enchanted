# T-161-1 / a1 修前红态

RED / PASS。产品修复与交付仍为 INCOMPLETE。

复现命令：`zsh evidence/2026-10-23-batch24/T-161/RUN-OUTSIDE-04.sh`。主控在沙箱外运行，同一测试以 `--revision 3c56f743f` 构建真实隔离 Electron；完整版本为 `3c56f743fa605ce0b3c7b99e4278b933202cf627`。结果见 `red04-20261024T034907Z.json`、同名 log 与四张截图。原始夹具 `/private/tmp/t161-gyqt5x6l` 保留，待主控按 T-088 归档。

脚本 exit=1；summary 的产品验收状态为 INCOMPLETE，error、cleanup_errors 均无值。15 条检查中恰好六条缺陷断言失败，九条对照通过；不把修前产品状态改为 PASS。

| 条件 | 预期 | 修前观察 |
| --- | --- | --- |
| 查看只读 reviewer | 无输入横幅、不请求输入焦点 | 出现 focus-observation / Window is not available for input，焦点进入终端 |
| 查看历史 worker | 无输入横幅、不请求输入焦点 | 同上 |
| 已确认执行主控，隐藏侧栏 | 窗格头保留普通终端并显示执行主控 | 只有普通终端 |
| 同一主控重命名 | 自定义名称、普通终端、执行主控均可辨认 | 自定义名称与普通终端存在，缺执行主控 |

通过的对照：两种只读窗格均确有真实 PTY 焦点模式输出、input_enabled=false，且无输入凭据；释放角色后不再显示主控；可写 worker 的超限输入经真实 IPC 拒绝后仍显示输入错误；模型请求为 0。受控 CLI 的交付元数据是明确标识的测试替身数据，不能当成供应商模型或服务档位证据。

实现保持 pending：根因在 renderer 的焦点条件、输出观察条件及头部角色来源。main/preload 的凭据检查正确地拒绝了只读输入通道，没有必需改动。等待执行主控通知 T-157 合并后，再在新 main 上 rebase、改 renderer；不通过放宽主进程权限绕过缺陷。

修后计划复跑同一 T-161 真实 Electron 场景及其变异，并运行 T-159 的真实分屏回归，核对普通终端标签、主控角色、任务分屏与输入归属。旧版本的通过结论不替候选背书。
