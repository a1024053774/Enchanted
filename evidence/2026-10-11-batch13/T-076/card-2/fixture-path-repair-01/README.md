# F09受控reviewer路径夹具修复

状态：**PASS（离线夹具核对）／产品INCOMPLETE**。真实回合0/8，完整W07待沙箱外运行。原02证据未改。

## 根因与最小修复

02保存的reviewer launch `ac541f4d-d442-439e-b9ba-3177c5709b34`使用`/bin/zsh`，CODEX_HOME为`/private/tmp/a5-47piz1vh/t-z7d5arsy/quality-control/review-home-0`。归档config已经列出全部8个reviewer home，但拼写为`/tmp/a5-47piz1vh/t-z7d5arsy/quality-control/review-home-0`。两者解析为同一目录，原夹具的精确字符串匹配因此拒绝；不是漏登记reviewer，也不是shell错误。

`legacy_quality_driver.prepare_review_control()`现在先对自建root执行`resolve(strict=True)`，再创建配置、独立home、role和版本程序，配置值从一开始就是产品传入的真实路径。`controlled_quality_pty.ts`的原home/shell拒绝条件不变，只在拒绝时追加实际值与登记值，便于保留诊断。Panes及产品逻辑没有改动。

原文件保存为`*.before`；精确修改diff在`offline-02/*.diff`。旧02没有session文件、没有pane_started，符合受控spawn在写session前拒绝的顺序；原机械passed/task paused/review unknown/issue仍保留。

## W07前置核对

| 前置 | 已核对的事实 | 证据界限 |
| --- | --- | --- |
| home/shell | 旧值复现拒绝；新值接受；8个reviewer与worker home互异；未登记home和/bin/sh仍拒绝 | 只调用JS受控spawn，不创建终端进程 |
| session | 文件位于传入的同一CODEX_HOME；session_meta为根CLI，文件名尾部对应native ID；task_started和turn_context绑定fixture-turn-1 | 合成输入字节一致性，不冒称真实模型会话 |
| hook argv | 02的shell program拆词与已登记argv一致；UserPromptSubmit/Stop/PermissionRequest三条command均指向正确Node、CLI、state、launch；Node/CLI路径存在 | 只解析归档参数，没有执行shell/hook |
| B文件 | 生产JSON校验与writeReviewRequest/readWorkerRequests在自建目录完成读写，路径为realpath、权限0600、完整JSON且相同内容重放不变 | 文件协议局部检查，无socket/relay/gate判定 |
| 身份传递 | 受控metadata完整保留输入env；driver用该launch的env发Stop，native ID/turn取同一记录；daemon按Stop的session_id核对caller | 静态调用链与文件probe，不替代完整W07 |
| 剩余前置 | 产品按独立home扫描，createReview选登记slot；匹配Stop后落B文件；review-result后仅idle回收；没有新增ACK模型回合 | 已读相关调用者，完整路径仍须legacy-green-03 |

探针不启动后台、socket、ps、shell、provider或模型。`terminal.kill()`在此仅调用已安装的JS假终端回调，不发送OS信号。

## 探针自身错误与复放

offline-01先把shell program读成`launch.shell_argv[2]`，实际该位置是`-c`，program在索引3。错误分类为probe_error，保留`probe-error.json`及原脚本`check_paths.py.before-fix`。修复仅这个读取索引并补前三项精确核对；没有修改产品、放松任何期望或重跑失败产品。

offline-02通过旧/新配置各一次文件探针；完整命令与stdout/stderr在`run.json`，自建目录另归档为`fixtures.tar.gz`，源目录也保留。再生成需换新输出名：

```sh
python3 -B evidence/2026-10-11-batch13/T-076/card-2/fixture-path-repair-01/check_paths.py --output evidence/2026-10-11-batch13/T-076/card-2/fixture-path-repair-01/offline-03
```

该命令不能当作产品绿态。legacy-green-03仍重新冻结并先跑F10/W07来源反事实，失败即停。
