REVIEW-01

结论：**NO_GO**。候选存在把仍在运行的复盘误判为结束、观察失败后持续显示“进行中”，以及并发检查重复写入结束事件的问题。

审查对象为基于 `82e747f4ad0baf6106f58b711c0602ba7b8b9293` 的 `candidate.diff`。审查结束时，该补丁与六个候选文件的工作区差异一致。全程未修改文件，未运行会写入夹具或清理既有进程的测试；以下区分现有运行证据、静态核对和本次只读探针。

1. **阻塞 · P1：没有内存窗格，不能直接证明终端已经消失。**

   位置：[panes.ts:640](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:640)。

   `!pane` 直接返回 `gone`，但恢复流程存在“CLI 仍活着、窗格没有恢复”的明确路径：[panes.ts:812](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:812) 在查找 hc 终端、核对身份或读取凭据时抛错，会记录 `shell_exit_unconfirmed`；此时可能尚未创建内存窗格。下一次复盘检查却把这个未确认状态永久记为 `ended / terminal_gone`。

   此外，每分钟定时器没有等待 `recovery`。恢复超过一分钟时，尚未轮到恢复的活终端也可能被提前判成消失；请求入口的 `daemon_recovering` 检查保护不到这个定时器。

   本次从候选补丁提取 `shellFront` 做内存探针：存在 shell 启动记录、没有内存窗格、没有退出确认时，结果确实是 `gone`，且没有查询进程。

   建议：恢复期间不作结束判定；恢复结束后也须区分“已确认退出”和“恢复失败、退出未确认”。后者显示未知并保留诊断。增加“恢复失败但进程仍活着”的反例。

2. **阻塞 · P1：前台判定依赖 zsh 开启 job control，当前启动契约没有保证这一点。**

   位置：[panes.ts:642](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:642)。

   `pid == pgid == tpgid` 能识别通常的独立前台进程组，但关闭 zsh 的 `MONITOR` 后，前台程序可以与 shell 共用进程组。候选先排除 shell，再找进程组领导者，于是把仍在执行程序的终端判成 `prompt`。

   这是可达配置：[.zshrc:4](/Users/luckye/Documents/Code/a2a/workbench/terminal/zdotdir/.zshrc:4) 会加载用户自己的启动文件，没有强制恢复 `MONITOR`。

   本次在临时 PTY 中启动不加载用户配置的 zsh，执行 `unsetopt MONITOR; /bin/sleep 2; :`，通过项目的真实 `processSnapshot.py` 得到：

   ```text
   zsh：  pid=2777，pgid=2777，tpgid=2777
   sleep：pid=2778，pgid=2777，tpgid=2777
   ```

   将这种快照交给候选判定，结果为 `prompt`。同样形态的复盘 CLI 运行超过宽限后，就会被错误记为结束。

   建议：没有找到独立进程组领导者时，不直接推导为提示符；应核对仍在运行的同组子进程，无法确认则显示未知。补充关闭 job control 的真实终端反例。

3. **阻塞 · P1：观察错误被转成检查成功，原缺陷会在错误路径下持续存在。**

   位置：[daemon.ts:149](/Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts:149)。

   任何 `shellFront` 错误都只记一条全局事件并 `continue`。该复盘没有结束或未知状态，界面继续显示“进行中”；请求仍返回 `ok: true`。错误持续存在时，每分钟都会再写一条相同事件。

   此处还把错误压成 `String(error)`，丢掉了 `processInfo` 专门附带的 `process_query` 信息，包括 stderr、退出码和耗时。

   本次对候选检查代码连续注入两次带诊断的观察错误，得到两条相同的 `retrospective_end_check_failed`；两个检查均正常返回空 `ended`，诊断字段均丢失。

   建议：把观察失败明确反映到该复盘的未知状态及检查结果中，保留结构化诊断；相同持续故障按状态变化记录，避免每分钟重复追加。增加持续错误及随后恢复的反例。项目已有 [panes.ts:1318](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:1318) 所描述的同类去重要求，这次应由故障注入检查守住。

4. **阻塞 · P2：两个检查重叠时，会为同一次复盘写入两条 `ended`。**

   位置：[daemon.ts:146](/Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts:146)、[daemon.ts:151](/Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts:151)。

   `unfinished()` 在 `await shellFront()` 前取得列表。两个请求，或请求与每分钟定时器重叠时，都能取得同一个未结束复盘；等待结束后，两边直接追加事件，没有重新核对状态。

   本次用候选代码在内存中挂起两个 `shellFront` 调用，再同时返回 `prompt`，实际写入：

   ```text
   R ended {"reason":"cli_not_running"}
   R ended {"reason":"cli_not_running"}
   ```

   现有测试只顺序执行两次 tick，证明不了并发下“只记一条”。另一个 tick 在等待期间完成导入时，也存在使用旧列表继续写 `ended` 的窗口。

   建议：在同步写入前重新核对该 run 尚未结束、尚未导入，再完成状态转换；增加重叠 tick，以及等待期间发生导入的反例。

5. **阻塞 · P2：缺少本缺陷在 Reflect 页上的修后验收。**

   位置：[test_t237_retrospective_end_e2e.py:145](/Users/luckye/Documents/Code/a2a/workbench/tests/test_t237_retrospective_end_e2e.py:145)、[RetrospectiveSections.tsx:105](/Users/luckye/Documents/Code/a2a/workbench/app/RetrospectiveSections.tsx:105)。

   新测试检查后台事件，没有启动 Electron。即使完全撤回本次前端修改，让 Reflect 页继续显示“进行中”，新测试及四个变异检查仍可通过。

   已有 T-136 回归验证建议、批准和导入失败，但没有验证 T-237 的已结束行。因此，现有证据不能关闭最初通过 Computer Use 发现的界面缺陷。

   建议：通过真实 Reflect 入口验证退出、关闭终端及重启场景，核对目标行的文字与 `data-run-state`，保留截图；再证明撤回前端修复会使该检查失败。同时补上“先 ended，之后补齐报告，再变成已完成”的场景。

其余审查意见如下。

- **非阻塞：时间计算未发现时区错误。**  
  [retrospective.ts:94](/Users/luckye/Documents/Code/a2a/workbench/src/retrospective.ts:94) 使用带 `Z` 的 ISO 时间记录 `started`，与 tick 的 epoch 毫秒相减，不受 DST 或本地显示时区影响。恰好 60 秒时进入结束检查；每分钟轮询意味着正常情况下约在启动后 60～120 秒发现退出。系统时钟回拨会延长宽限，这是墙钟计算的边界。现有测试覆盖 5 秒和 61 秒，没有覆盖恰好 60 秒。

- **非阻塞：状态优先级和后续导入的代码符合请求。**  
  前端顺序确实是“已完成 > 没能启动 > 导入失败 > 已结束 > 进行中”。`importFinished()` 只排除已导入项，不排除 `ended`，所以之后补齐合法产物仍可导入；前端也会优先显示已完成。这部分目前只有静态证据，缺少上述状态转换的运行验证。`pane.stopped` 会返回 `gone`；但 `pane_gone_confirmed` 占位窗格当前由 worker/reviewer 等恢复路径创建，并非复盘 shell 的通常恢复路径。

- **非阻塞：README 大体一致，但应写明状态优先级。**  
  [README.md:1235](/Users/luckye/Documents/Code/a2a/workbench/README.md:1235) 无条件描述记入 `ended` 后显示“已结束，没有报告”；实际同时存在 `import_failed` 时，会继续显示导入失败。建议补上这个限定。另须随第 1 条修正“未恢复就等于终端已不在”的描述。

- **非阻塞：`pkill -f` 缩小了匹配范围，但不是进程所有权证明。**  
  [test_t237_retrospective_end_e2e.py:142](/Users/luckye/Documents/Code/a2a/workbench/tests/test_t237_retrospective_end_e2e.py:142) 使用随机夹具路径，当前路径没有需要额外转义的正则元字符，通常不会匹配另一个夹具。但任何命令行含该路径的进程都会被终止，包括用户为查看夹具而启动的 `tail` 等进程，不能保证“只杀本夹具创建的进程”。建议记录并核对夹具进程身份后定向清理。

现有证据的核对结果：

| 证据 | 审查判断 |
| --- | --- |
| `red-baseline.json`、`red-no-end-check.json` | 均失败于 `exited_cli_marked_ended`，能抓住原有缺陷 |
| `red-no-grace.json` | 失败于宽限期业务断言 |
| `red-gone-is-running.json` | 失败于终端消失后的业务断言 |
| `red-end-before-import.json` | 抓到 `started → ended → imported` 的错误顺序 |
| `green-2.json`、`green-3.json` | 六项后台业务检查均记录 PASS |
| `green-1.json` | 记录 PASS，但 `early` 中已有 C；当前测试此时尚未启动 C，不能计作当前测试版本的第三次重复证明 |
| T-136、T-223 三个时区回归 | 现有产物均记录 PASS；本次未重跑 |
| 项目地图检查 | 开始及结束均为 Problems 0、Stale living docs 0 |

红态 JSON 将业务断言失败统一标成 `INCOMPLETE`；本次依据具体错误判断其反例有效，没有将该状态改报为 PASS。

本次新增探针证明了控制流缺陷，其中 job control 使用了真实 PTY 与 libproc 边界；其余内存探针不替代完整后台或界面验收。未运行完整构建、原生模型复盘或 Electron 修后场景，也未写入 `REVIEW-01.md`，按用户要求将完整审查直接输出于此。

**最终结论：NO_GO。**
