# T-249 v9 主控交接

INCOMPLETE：worker 已恢复原候选并重新取得三项机械结果。下一步是限定独立审查、新 Test 包和 Terra 验收；本次没有运行外部窗口或构建。

本候选的完整提交号以本次身份 submit 为准。恢复输入 B、C、base 与 attempt/session/fence/spec 见 run-context.json；代码字节、执行位、保护路径与主控历史文本来源见 equivalence.json。README 唯一适配是保留当前 T-265 材料文件段落。

外部运行集中在下面，执行者是主控，worker 不执行。先固定候选副本，核对工作目录与最终提交，再按审查员提出的 2–5 个小变异运行；不得以本文件预先代替审查员选择反例。

本次后台与旧 C 不同，需要新包或主控明确完成重新绑定。已有标准隔离脚本会跑冻结检查、完整候选窗口、原五项变异，并以 `--variant test` 标准打包、核对正式进程、清理自有缓存；在最终候选工作目录下执行一次：

```sh
bash workbench/app/RUN-OUTSIDE-T249.sh t249-v9-ccae173b
```

它是原 C 原样恢复的脚本，不是此次新执行的结果；输出位置由脚本打印，正式 /Applications/Enchanted.app 不替换。脚本中的原五项变异不替代审查员的新增小变异或 Terra。若主控需要重新取得未跟踪文件、列宽与迟到返回整组窗口证据，已有准确命令如下（输出目录必须全新）：

```sh
/usr/bin/python3 '/Users/luckye/Library/Application Support/a2a-orchestrator/worktrees/a2a/T-249-1-a8/evidence/2026-11-08-batch34/T-249/worker-untracked/run_windows.py' --output '/Users/luckye/Documents/Code/a2a/evidence/2026-11-09-batch35/T-249/controller/recovery-v9-window-01'
```

该组不打包；不要在 native sandbox 重试 ps/Electron，也不要重新执行已完成的旧包流程却冒称绑定新提交。保留 stdout、exit、run.json、清理状态和执行者来源；真实启动失败保持 INCOMPLETE。

治理 issue `5d266908-1d60-42b8-aa64-395d5fca1aa1` 已排队，REVIEW.md 的 Verified 待主控按权限核验；worker 未改地图、冻结验收或 REVIEW.md。额外目录改动：无。最终 submit 的 queued 仅表示请求文件存在，Stop hook 转交后仍须门禁确认受理。
