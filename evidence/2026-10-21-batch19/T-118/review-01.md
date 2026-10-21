codex
结论：**NO_GO**。审查期间未修改文件、未提交；结束时，工作区受审 diff 仍与提供的 `t118.diff` 一致。

按严重程度列出发现：

1. **P1：普通终端环境过滤过头。**  
   [panes.ts:132](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:132) 删除全部 `CLAUDE_CODE_*`，包括正常配置 `CLAUDE_CODE_OAUTH_TOKEN`、`CLAUDE_CODE_USE_BEDROCK`。用户通过后台环境提供认证或供应商配置、且 zsh 配置没有重新设置时，新终端里的 Claude 会丢失认证或改变服务来源。内存探针确认这些变量全部被删。它们是[官方支持的配置变量](https://code.claude.com/docs/en/env-vars)，应与子会话标记区分。

2. **P1：切换项目期间渲染进程退出，会留下失效窗格。**  
   [main.ts:608](/Users/luckye/Documents/Code/a2a/workbench/app/main.ts:608) 立即 reload，没有等待 `context.switching`。新 renderer 可在切换完成前通过 `selection()` 取得旧 pane key；随后 [main.ts:421](/Users/luckye/Documents/Code/a2a/workbench/app/main.ts:421) 替换窗格集合。新界面继续请求旧 key，报 `Task view is changing` 或 `Unknown pane key`，而初始化后的定时刷新只更新侧栏，不重新同步 selection。已用实际 `selection/changeView` 函数的内存探针确认该时序。

3. **P2：重连仍会显示补读过程。**  
   [renderer.tsx:221](/Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx:221)、[renderer.tsx:263](/Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx:263)：首次追平后 `restoring=false`；断连期间积累输出，再点“重新连接”时不会重新隐藏。内存探针确认补读期间 `hidden=false`，因此仍可能出现快进的中间帧。

4. **P2：部分失败状态会永久显示“正在恢复终端内容”。**  
   [renderer.tsx:243](/Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx:243)、[renderer.tsx:258](/Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx:258)：无 launch 时持续绕过解除隐藏；初次 snapshot/output 失败时，catch 也不结束恢复状态。无当前 attempt 的占位窗格、初次 socket 错误或 trace 不可读时可触发。**空 trace 本身正常**：返回零字节后会解除隐藏。

5. **P2：持续崩溃可导致无限重载。**  
   [main.ts:606](/Users/luckye/Documents/Code/a2a/workbench/app/main.ts:606) 对所有退出原因立即 reload，没有次数限制或停止条件。若原因是加载页面即崩溃、持续 OOM 等，重新加载会再次触发同一事件。关窗已有 `closing/closed/isDestroyed` 防护；现有单次 `Page.crash` 证据不能覆盖持续失败。

6. **P2：放开版本后，部分版本事实仍记录旧值。**  
   [claudeLogin.ts:155](/Users/luckye/Documents/Code/a2a/workbench/src/claudeLogin.ts:155) 的最终审计仍使用 `input.version`；manifest 为旧版本、实际 CLI 已更新时，审计版本错误。恢复路径的 [panes.ts:388](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:388) 也保留旧 `cli_version`，新版本只进入 `version_probe` 事件，状态展示仍取旧启动记录。

7. **P3：仍有要求比较版本的过期文案。**  
   [README.md:605](/Users/luckye/Documents/Code/a2a/workbench/README.md:605) 仍声称启动时“核对 manifest 中本次观测值”；第 21 行也保留“原版本／session 核对”。与本次行为不一致。生产源码中未发现剩余的 CLI 版本相等比较；版本格式校验仍存在。

测试证据判断：

- 环境测试的断言独立于生产实现，已有修前标记泄漏、修后清除的证据；但 [test_t118_shell_env_e2e.py:25](/Users/luckye/Documents/Code/a2a/workbench/tests/test_t118_shell_env_e2e.py:25) 只检查保留普通变量，无法检出第 1 项。
- Claude 版本测试有修前及重新加入比较的变异反例；Codex、恢复测试也有符合预期原因的修前失败记录。
- GUI 验收仍 **INCOMPLETE**：旧版同脚本对照未完成；未覆盖重连、错误、切换项目、关窗与持续崩溃。20ms 抽样只能证明采样点未见中间帧；`Page.crash` 也不等同于外部 SIGTERM。
- 本次只运行了无文件写入的内存探针，未重新执行会创建夹具或证据文件的端到端测试。
