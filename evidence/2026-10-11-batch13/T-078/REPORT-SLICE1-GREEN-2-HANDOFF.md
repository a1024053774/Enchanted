# 主控 #182：入口等待修复交接

诊断 **PASS**：原 outside-01 的 SQLite 原件只读事件表明 seq29 真实执行、seq34 反馈 paste、seq38 CR；入口夹具在异步 drain 完成前断言，因此是夹具等待缺失，不是产品未转交或未写 CR。原失败及 SQLite 原字节归档保留。

先用实际 drain 最小复现相同 undefined !== '\r'，再等特定 dispatch 的 turn_submitted，局部 **PASS**；CR、busy、active、intent2 断言保留。产品源码不改。入口只补有期限的观察等待及前后／超时快照；README 按 #182 分配同步。

请按原启动身份运行 `sh /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/commit-and-prepare-slice1-green-2.sh`。固定 HEAD=455696c98e99b73a118886345ab1d83de24e0bdf、原 task/session、空暂存区与明示清单；第一提交后核对 project_map status，再续跑新 outside-02（controller-entry6 全跑及后续空框17/runtime12/input-failures11/worker-inbox14）。全 PASS 才生成全新 slice1-green、静态核对、提交材料；任何失败停、不重试、不删现场，**不 launch**。

完整新入口、实例生成／实际 Claude 绿态、独立审查、09B/09C、整票 **INCOMPLETE**。说明见 `SLICE-1-GREEN-2.md`；供应商模型0、根2／Messages3／Bash1、逐屏与许可审批范围不变。

T-078 SLICE-1-GREEN-2 READY
