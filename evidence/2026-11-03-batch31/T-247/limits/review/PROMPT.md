你是只读审查员。不改仓库里的任何文件。可以读代码与证据，运行只读命令，也可以运行
`python3 workbench/tests/test_t247_hook_runner.py --summary /private/tmp/<新文件>.json [--revision HEAD | --mutant <名字>]`：它只起假 CLI 和一个本地 socket，结果写到 /private/tmp。注意：在你自己的 Codex 沙箱里，`/bin/ps` 不能执行；网络关闭时 Unix socket 也连不上。上一轮复审正是因此收不到上报（见 evidence/2026-11-03-batch31/T-247/rereview-answers/）。如果你的环境如此，不要把重跑失败当成候选的缺陷，以保存的结果为准，并写明你没能重跑。

仓库 /Users/luckye/Documents/Code/a2a，审查对象是工作区相对 HEAD（297c96315，T-247 第一版）的改动。用户要求解决 T-247 的两个局限：“CLI 装在带空格的路径下时，钩子不上报”与“以 Codex 沙箱模式运行时，钩子能不能读进程表”。

- 代码：
  - workbench/src/terminalCli.ts 的 hookRunner。包装脚本声明 A2A_HOOK_CLI、A2A_HOOK_PID。从钩子往上只经过 shell、或经过声明进程的一个直接子进程，到达声明的进程才认；`ps` 只读 pid、ppid、comm；`ps` 不能执行时只报事件、不带 cli。
  - workbench/terminal/bin/claude 与 codex 两个包装脚本的 export 行。
- 测试：
  - workbench/tests/test_t247_hook_runner.py：真实包装脚本与 `a2a hook` 入口，假 CLI 进程树，13 种情形，3 个变异体。
  - workbench/tests/test_t247_sandboxed_codex_e2e.py：真实交互式 Codex，以 workspace-write、read-only 运行。
- 证据：evidence/2026-11-03-batch31/T-247/limits/。其中：
  - runner-*.json 是最终结果。
  - harness-*/ 是测试自身的问题被修好之前的运行。
  - sandbox-*-head.json 是在 HEAD 上跑的：交互式 Codex 在沙箱模式下，钩子照样报来，说明钩子在沙箱外执行。
  - sandbox-*-fixed、codex-nested-fixed、regress-* 是最终代码的运行。

要核对的不变式：普通终端里，上报的 cli 与 cli_pid 是运行这个钩子的那个 CLI 进程，即终端前台看到的那个进程（包装脚本 exec 后的进程）；不是它运行的钩子不得记到它名下；钩子事件本身不因认不出运行者而丢失。另外核对：
- 继承来的 A2A_HOOK_* 能否造成冒认。考虑嵌套、不经包装脚本的 CLI、shell 工具里运行的程序，以及“CLI 的直接子进程”这一放宽可能被谁利用。
- comm 的取法：带空格的路径、登录 shell 的 `-zsh`、名字截断。
- 包装脚本 `$$` 与 exec 的关系，以及真实 CLI 是 node 脚本或 npm 启动器时的情况。
- 有角色的终端（T-133）与 `a2a request` 是否受影响。
- 测试的预期是否独立于实现（假 CLI 自己写出的进程号、Codex 的 rollout）；变异体是否打到所声称的情形；RESULTS 草稿（如有）是否高于证据。

每条写成缺陷声明：文件:行、具体失败场景、依据。能用实际运行的反例证明的，附命令与结果；只读推导的，写明“未运行复现”。分阻塞、非阻塞两类。最后给总结论 PASS 或 NO_GO。用中文，输出到标准输出。
