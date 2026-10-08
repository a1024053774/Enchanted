# T-040 B 主控决定 01：5 项全仓失败先做父修订对照（2026-10-08，Claude Code）

INCOMPLETE 交付与审查原样保留。B 改了桌面生命周期代码（26 行），desktop 的 3 项失败有可能与之相关，不能直接归为上游。授权一轮有界对照，不修上游测试：

1. 对 5 个失败用例所在的测试文件（desktop：appSnapManager、cuaDriverHost、native 图标持久化；server：ProviderCommandReactor），在父修订 `d3b5bcc` 与候选 `28e2f1b` 上各单独运行 3 次，交替进行、不并行，使用外置盘短路径临时目录（T-039 曾见长 tmp 路径 EINVAL）。父修订用临时 detached worktree 或在同一 checkout 切换都可以；若切换，必须先确认 A 部分没有在用该 checkout 跑测试（A 正在做计时定位，会调用门禁 CLI），冲突时先停下问主控。严禁移动、替换或链接构建输出与依赖目录。
2. 父修订通过而候选失败的用例，按本 ticket 回归处理：定位到 B 的哪处改动，先红后绿修复并重跑；两边同样失败或同样不稳定的，记为上游，写入证据。
3. 结论追加到 RESULTS，旧结论不覆盖。完成后回复一行 `T-040B DONE <状态> <a2a commit> <fork commit>`。
