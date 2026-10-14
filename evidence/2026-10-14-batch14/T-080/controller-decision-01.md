# T-080 执行主控决策记录

## 开工（2026-10-14 UTC 13:2x）

依据 assign 20261014T055042Z-ideation-assign-001（用户原话见条目"## 授权"）。T-077 已关闭（main cdf8fe9b），blocked_by 解除。新建 worktree /Users/luckye/Documents/Code/a2a-wt-t080（分支 exec/t080，起点 cdf8fe9b），按 workbench/README 安装依赖（npm ci，外置盘缓存），node-pty spawn-helper 缺执行位按 README 先例手工 755。启动 worker s14-t080（wF:p3S，launch-8156a548…，gpt-6.1-sol xhigh、service_tier="default"、--no-daemon、workspace-write、on-request），空闲内存 68%。存活 a2a Codex 会话 2/3（s13-t078m、s14-t080）。
文件所有权：T-080 独占 gates/taskCards.ts、gates/core.ts、相关测试与任务卡模板；T-078 只改 gates/cli.ts 的 UserPromptSubmit 输出路径、panes.ts、daemon.ts、app/ 与测试。T-081 在 T-080 合并后开；T-082 在 T-080 与 T-078 之后。

## 红态读回（2026-10-14 UTC 13:3x）

red-01：rc=1，冻结源码解包用 tarfile filter 参数，本机 python3 3.9.6 不支持；业务未运行，原样保留。red-02（逐成员校验解包、排除受控场景不执行的 hook 链接别名）：rc=0，红态成立——allow ["."] 的卡、候选只改 acceptance/criterion.py（改为 pass），产品值仍 "base\n"，独立断言 exit 1，门禁 verified=true、integrated=true，夹具 main=候选 4f2649ab；审查结论为夹具合成（declared-contract 已声明，只证明机械门禁缺口）；真实模型 0。批准进入实现。

## 共享文件分配（2026-10-14 UTC 14:2x）

FINAL-01 交接指出依赖：workbench/src/gates/qualityProtocol.ts 的 scoreRecords 严格 checks、scripts/score 的 CHECKS 与帮助文本须新增 oracle，workbench/README.md 须同步门禁说明（project-map 1 stale）。三者当前无其他写入者，属 T-080 第 3、5 条范围，交 T-080 worker 修改。历史 records/scores.jsonl 为追加式旧数据，不改写、不加兼容分支；校验只针对新记录要求 oracle，若现有校验会整表重读旧行导致失败，worker 先停下报告。

## 打分记录格式决定（2026-10-14 UTC 14:4x）

worker 报 BLOCKED（history-format-blocker-01.json）：scripts/score 写入前整表重读校验（:135–148），12 行历史中 11 行无 oracle，直接把 oracle 设为必填会使旧行失败。执行主控决定：记录 schema 版本化——新写入行一律 schema=2，rejections 必须含 oracle；历史 schema=1 行只读、按 v1 检查集校验，不改写、不迁移；scripts/score 与 qualityProtocol.ts 的 scoreRecords 都按行的 schema 选检查集，写入端只写 schema 2，不保留写 schema 1 的路径。不采用另开日志（双存储）或缺项按 0（改变语义）。正反例须覆盖：v1 旧行通过、v2 缺 oracle 拒收、v2 完整通过、未知 schema 拒收、user 分 score_of 指向 v1/v2 原记录均可。
