# 09A-2 重启后仅清理旧 slot

2026-10-14，主控 #128。脚本准备 **PASS**；实际清理 **INCOMPLETE，未运行**。不把旧 cleanup INCOMPLETE 或 slot-cleanup BLOCKED 改成 PASS。

固定目标只有 `/Volumes/WD-Elements/a2a-workbench/t078-09-d2d9c666-5621-4467-bbe4-d99450bd5503`。旧 `/private/tmp/t078-2-p1-09a2-sm_du7jo` 已不存在，本脚本不恢复、归档或删除它，不复制用户 CLI 或配置，不发信号。

执行主控另批并在沙箱外运行：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/cleanup-slot-after-reboot-09a2.py --approval-ref '实际主控批准条目引用'
```

前置条件：外置盘确为挂载点，目标和父路径没有符号链接；仓库 approval、实际 continue 与 Electron argv 及 slot 的 build.json 都指向同一 launch／slot／本 worktree 源码；当前系统启动时间晚于旧外置归档记录。原根必须仍不存在。旧 PID 不能证明当前运行身份，重启后不沿用原清理脚本的 PID／root／cleanup PASS 前置。

脚本核对当前进程无该 slot、旧 root 或 launch 引用，再用 lsof 确认 slot 中没有打开文件；任何未知、错误或正在使用的事实都 BLOCKED，既不删也不发信号。无关用户进程命令行不落证据。检查各限 30 秒，没有重试。

完整 slot 归档到独占新目录 `/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078/slot-after-reboot-09a2-01/slot.tar.gz`。符号链接存为链接，不复制其目标；核对完整成员集合、文件字节、链接目标及源 inventory 稳定性，不计算 hash。归档读回通过后再次核对使用情况与源未改变，才删除上述精确目录；其他 slot、源码、依赖和原外置 fixture 归档保留。

仓库运行结果将写入 `slot-after-reboot-09a2-01/result.json`，含批准引用、命令、使用检查、build manifest、inventory、外置原件位置及实际删除结果。已有目录拒绝再次运行，保留失败，不覆盖。归档或删除未完成仍报告 BLOCKED；运行者核对结果后再报告清理状态。

本地静态证据：[2/2 PASS](slot-archive-static-09a3/result.json)，只测试归档 helper 的精确字节和链接保留；已知坏“跟随链接”变异实际复制外部夹具成员，被完整成员 oracle 拒绝。没有运行实际 ps/lsof、外置写入或删除，也不证明整个清理流程已执行。

```sh
python3 -B workbench/tests/test_t078_reboot_slot_archive.py --output /绝对路径/新本地归档检查目录
```
