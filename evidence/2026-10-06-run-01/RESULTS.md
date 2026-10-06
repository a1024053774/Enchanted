# T-008 自动运行验收（2026-10-06）

状态：PASS，限本地受管运行契约。固定候选：
907672e1d362c99f5b2173d40f58af47423241c0。
真实成功使用 655b5a332adfc744e8b49d68f5ef368cac962b05，产品源码与固定候选相同。

## 验收结果

- run 自动分派、等待当前 attempt 显式 submit、受锁验收/集成，并回收自己的 pane。
- expected-attempt 条件使旧 run 不能接管或清理替换者。
- 隔离编排矩阵 18/18（312 条断言）；此层 Herdr/Codex 为替身，Git/SQLite/CLI 为真。
- 修复后的 T-006 回归 8/8、T-007 回归 9/9，执行源码与候选相同。
- 一次真实自动 run PASS，集成 commit：2aea50b94ac460d4d0670f95acc3b28efd4da2c8。
  run_id：46c59c07fe514c32b058f47c63f42c79；attempt_id：77c1be5dfbed4d8b807379cbfdd22729。
- 12 项独立 oracle 通过；权威引用、用户原分支和既有 pane/terminal 均已读回核对。
- 验收脚本只有一次驱动 run 调用，没有由主控逐条调用 verify/integrate/reclaim 代办。
- [独立审查 PASS](review.txt)；所有本项目临时 pane 已回收，见 final-panes.json。

## 已保留的真实失败和反事实

live-auto-01 因正常辅助 shell 加入被旧实现误拒绝：
Codex 前台组领导者 PID 23852 未变，临时 zsh 为 PID 25405。
程序暂停，没有错误集成；旧代码产物与完整记录保留。
修复只核对原 Codex 领导者、shell、terminal 和已记录原生会话。
旧源码 10bbee5 在新增辅助进程正例发生业务失败；修复后正例通过，
领导者变化即使旧 PID 仍在也拒绝。随后同一真实入口重跑成功。

忽略 expected attempt 的 mutant 被业务断言抓住，错误地启动验收、改变引用及 reflog。
有效反事实为 mutant-ignore-attempt-valid.json 和
check-20261006T071543.735031Z-510d4f94.json。
较早的 mutant 因诊断 Path 无法序列化导致 JSON 截断，不算产品反证；
修复只改变诊断路径表示并先保存 stdout/stderr，未放宽业务断言。

替换场景最初的屏障也阻塞了 controller reclaim，属于夹具错误。
改为一次性屏障后，仍保持旧观察直到替换 attempt 已提交才释放，竞态断言没有削弱。

## 复现与证据

```sh
python3 -B acceptance/test_run_e2e.py
python3 -B acceptance/test_coop_e2e.py
python3 -B acceptance/test_recovery_e2e.py
```

真实执行的命令：

```sh
python3 -B acceptance/live_run.py --parent-pane wF:p1 \
  --fixture-repo /Users/luckye/Documents/Code/a2a/.runtime/run-live-fixture \
  --output evidence/2026-10-06-run-01/live-auto-02
```

重跑需新的输出目录和干净独立夹具，不能复位旧的集成引用来覆盖证据。
live-auto-02/commands.jsonl 保存实际调用和独立读回。
最终隔离矩阵为 check-20261006T072644.143282Z-6d0d7be8.json。
完整 *-artifacts 已按原样封装在同名 tar.gz，包括 Git 对象、SQL及源码快照；
原目录仍在本地，被 Git 忽略。artifact-archives*.json 为索引。
归档纠正了将内嵌测试仓库误登记为 gitlink 的问题，没有删除或改写失败现场。

## 限制

本轮不是跨 CLI、Herdr server 崩溃、恶意同用户隔离或完整 run 进程自动恢复的证明。
真实成功仅一次；替身负例不能等同于全部真实模型失败模式。
未主张成本、吞吐、可靠性提升或供应商实际 Fast tier。
邮箱、hook 与更多 CLI 仍属未展开范围。
