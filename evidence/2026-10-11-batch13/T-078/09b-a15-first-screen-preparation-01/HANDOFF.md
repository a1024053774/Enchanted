# A-15 ideation 首屏与第一键

材料 PASS；本轮只写文件，没有读屏、发键或调用门禁。实际 B1 启动原件已由 `02afa5df7455d3afe69f66185991221dc5805e3e` 提交：dry-run 为 READY_FOR_ROLE，real 外层为 PASS、cli_spawned=true；内层 P1 为 INCOMPLETE，明确只完成进程启动，未声称已读屏或首启就绪。manifest 保存 shell 65816、CLI 65817；它们是启动时的身份，不是本轮存活探测结论。

命令在 `09b-a15-b1-ideation-p1-01/FIRST-SCREEN-COMMANDS.txt`。四条是候选命令，必须分开运行，不能整份执行：

1. 先运行 candidate 1 的 read-only screen。它绑定实际成功的 launch label `09b-a15-b1-ideation-01`，输出 `a15-ideation-s1-screen-01/`，screen-id 为 `ideation-s1`。
2. 主控检查 screen.bin。预期是 Claude Code v2.1.296 的主题选择首屏，提示为 “Choose the text style that looks best with your terminal”，当前选中 Dark mode。若内容不符，不发键，只运行 candidate 2 的只读重读，输出新目录 `a15-ideation-s1-screen-02/`；仍不符就停，保留两份原件。
3. 若 -01 符合预期，核对 `onboarding/s1-ArrowUp.json` 后再签字，只运行 candidate 1 的 ArrowUp 命令。若实际采用 -02，则改用 `onboarding/s1-ArrowUp-screen-02.json` 和 candidate 2 的 ArrowUp 命令。两份草稿的 approved_by、approval_ref 均为空，分别固定引用各自 screen.bin；只选择并签一份。
4. 首键仅 ArrowUp，目标选项为 Auto (match terminal)。写出后立即保存 `ideation-s2` 快照并停，不自动 ArrowDown、Enter 或 release；后续每个键仍待主控逐屏核对、单独签字。

两个读屏目录和两个候选按键输出目录目前均不存在。screen.bin 要在主控实际读屏后才产生，不能把其缺失误当成材料输入路径错误。静态检查已确认 runner、P1、实际 launch manifest、两份未签草稿和源码文件路径存在；没有运行 P1 screen/key，也没有执行带模拟批准的 dry-run。

文件绑定使用既有 `prepare-a14.py --mode bind-launch`，只从 B1 外层结果定位内层 manifest，没有复制 manifest 或构造替代会话。ONBOARD-COMMANDS 的实际 launch label/后续 permission manifest 也由该既有步骤填入；s1 的 -01/-02 标签与本次批准草稿一致。首屏和首键仍属 INCOMPLETE／未运行，预算不变。
