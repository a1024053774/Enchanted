STATUS: FAIL

FINDINGS:

- [P1] [panes.ts:1605](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:1605)、[daemon.ts:78](/Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts:78) — 记录失败不再阻止本次提交。Claude/Codex 跳过写回车前的记录，回车在 `panes.ts:1625` 已写入；随后钩子记录失败只抛异常，`gates/cli.ts:226` 返回退出码 1。本机 Claude 将该退出码视为非阻断错误，因此可能执行没有用户输入记录、没有人工介入事件的提示词。违反 T-206 明确保留的 fail-closed 契约。

- [P1] [panes.ts:535](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:535) — 历史上已经提交、但没有新增 `dispatch_prompt_claimed` 事件的派发仍可被认领。查询不排除已有提交事实，也没有运行期间的边界；旧库中的受管主控恢复后，用户从历史重发该派发全文，会被当成系统输入吞掉。恢复路径保留原 launch，见 `panes.ts:909`。

- [P1] [panes.ts:2149](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:2149) — Claude 的正文不一致阻断分支在 `2128–2134` 直接返回，绕过唯一的用户提交记录点。存在旧草稿与派发正文混合、用户提交后被阻断的路径时，原始钩子虽留在事件中，却没有用户输入记录及派生人工介入。原有反例见 `tests/test_t078_empty_declaration_entry.ts:126`。

- [P2] [panes.ts:2146](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:2146) — 缺少 `prompt` 的检查仍晚于 `2139–2143` 对 active/state 和提交事件的修改。有效身份的新钩子缺字段时，会先留下忙碌的提交，再报错，无法完成正常回合关联。[REPORT.md:12](/Users/luckye/Documents/Code/a2a-worktrees/T-229-evidence/REPORT.md:12) 和第 63 行声称检查已经前移，与候选不符。

- [P2] [test_t229_worker_input_e2e.py:186](/Users/luckye/Documents/Code/a2a/workbench/tests/test_t229_worker_input_e2e.py:186)、[同文件:197](/Users/luckye/Documents/Code/a2a/workbench/tests/test_t229_worker_input_e2e.py:197) — 第二次提交只是重复用户自己的 `abdc`，没有重发已认领派发的全文；`claims` 在第 209 行也只保存、不断言。“所有带主控标签的提交永久忽略”这种错误实现仍能通过新增测试。T-216 回归验证的是 shell 主控的另一条认领路径，不能证明 worker 的 `noteSubmission` 只认领一次。

EVIDENCE:

- 读取了票面、T-206、T-216、候选八个文件及直接调用路径；HEAD 为 `59815ea30e3811d2e449bf5c67b7c70b050081ec`。在内存中逐字比较，限定文件的工作区 diff 与 `candidate.patch` 相同。
- `red-claude.json`、`red-codex.json`：`revision=59815ea30`，`observed.after_1` 带按键、`after_2=[]`，确实在业务断言失败。
- `final-claude.json`、`final-codex.json`：各四项通过，`claims=2`、`human_interventions=2`；agy/opencode 各四项通过，保留 `text_uncertain`，人工介入各三条。
- 五个变异均在对应业务断言失败；T-206 修改后的断言符合新票要求，没有削弱文字、清稿及终端字节检查。
- 以只读、immutable 方式读取三个回归夹具库：T-216 的各条 worker 派发分别认领一次；T-166 门禁反馈认领一次；T-207 门禁反馈认领零次且未进入用户输入，与 REPORT 第 69 行一致。
- `submitHook` 覆盖当前任务卡允许的四种 CLI 名称；新增 catch 重新抛错，未发现新增吞异常、重试或 fallback。Claude 包装由 `claudeSubmittedText` 解开，新派发末尾换行已由 `store.ts:155` 去掉，未将规范化差异单独判为缺陷。

LIMITATIONS:

- 未运行测试、status 脚本或供应商命令，未连接 hc；上述问题来自静态可达路径与已有证据，未新增复现。
- 恢复、阻断提交及记录故障没有本候选的真实入口证据；Codex 忙中排队、Tab 补全也没有专门场景。
- agy/opencode 现有证据使用替身；未验证真实 CLI 行为及报告中的进程清理结论。