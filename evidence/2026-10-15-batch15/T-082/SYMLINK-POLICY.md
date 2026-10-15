# T-082 symlink policy

## Decision

候选副本中的仓内相对 symlink 按内容复制为普通文件或目录；解析目标不在候选来源 worktree 内的 symlink 拒绝。副本不保留 `.git`，也不保留任何会回到审查 worktree、worker worktree 或共享仓库的链接。

## Reason

T-082/D3 允许 reviewer 只在一次性候选副本中写变异，同时要求候选与审查边界保持不变。直接保留 symlink 的目标文本可能仍解析到来源 worktree；outside-command-03 已复现 `link.txt -> sub/value.txt` 在副本中解析到来源目录，触发边界拒绝。按内容复制保留 reviewer 读取和修改候选文件的语义，且不会把写入穿透到受保护目录。全部拒绝会把安全的仓内链接一并排除，扩大拒收范围，没有票据依据。

## Counterexample

探针新增越界链接反例：目标在来源 worktree 外时必须以 `review_candidate_copy_symlink` 拒绝。
