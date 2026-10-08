# T-027 最终复验许可：主控批准（附前置条件，2026-10-06）

核对：/tmp/t027-* 下无 auth.json 残留（find 结果 0）；run-03 的隔离 home 已删除。
发现：候选 c5a9cb0 仍有 386 个文件含 musterdev / muster.dev（全局改名把上游引用改坏），主控此前的修正请求未被执行。

前置条件（先做，再复验）：
1. 指向上游的仓库、issue、文档链接恢复为 herdrdev/herdr 或 herdr.dev（作为来源引用，不是网络访问）；Cargo.toml 的 repository 改为 https://github.com/a1024053774/a2a；全仓库不得再出现 musterdev 或 muster.dev。用 `git grep -nE 'musterdev|muster\.dev'` 证明为 0，并重新证明运行时不访问 herdr.dev。
2. 修正后冻结新的候选提交，相关的单元与 shell/endpoint 检查在新候选上重跑。

许可（只用一次，用于上述新候选）：新建一个 /tmp/t027-* 隔离 CODEX_HOME，只安装并信任相同的 4 个 Muster 上报 hook；用户 auth/config 原件不写，副本不入证据或 Git；验收后删除整个 home 并记录；默认 Herdr server 不动。其他 trust 或权限请求不在许可内。
README 的 stale 由主控在 T-027 审查通过后统一更新，worker 不改。
