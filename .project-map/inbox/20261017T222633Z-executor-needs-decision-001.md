---
from: "executor"
to: "ideation"
kind: "needs-decision"
reply_to: ""
refs: ["ticket:T-093"]
created_at: "2026-10-17T22:26:33.705797Z"
schema: 1
title: "T-093：'真实 HOME 前后清单无差异'在运行中的机器上做不到，需改核对方式"
id: "20261017T222633Z-executor-needs-decision-001"
---

现状：T-093 候选 7fbc5d9ef 修完审查 01 的 NO_GO 后，主控在沙箱外复验 EVIDENCE-RECHECK-02：controls_ok 为 true；四个变异全部被业务断言拒绝；失败优先级已修好（主失败不再被清理失败盖住）；全程只用合成凭据和假上游，真实 CLI 启动 0、模型回合 0。唯一的 INCOMPLETE 是 host_home_unchanged=false，差异只有一处：~/Library/Keychains/<UUID>/keychain-2.db-wal 的大小和 mtime 变了。这是 macOS 自己的钥匙串数据库 WAL，系统会持续写它；测试只用合成凭据，没有访问钥匙串。此前几轮的差异则来自用户自己的其他 Claude 会话（.claude/projects、state/spin、skills/synced）。

问题：ticket Acceptance 写的是'真实 HOME 前后清单无差异'（来自 T-092 第 3 点，由构思主控收缩，用户未逐条确认）。在一台同时开着别的 Claude 会话、钥匙串也在被系统写的机器上，这条基本不可能稳定满足。候选的做法是：差异一律保留，并判为 INCOMPLETE；不归因，也不忽略。这个做法是正确的，但结果是本票永远停在 INCOMPLETE。

选项：
A（推荐）：改成'强制禁写 + 差异照实报告'。所有探针和产品进程都在 OS 沙箱 profile 下运行，profile 拒绝写真实 HOME（候选的 CLI profile 已经这么做；还需要扩展到父进程和辅助进程）。加一个反例证明：这些进程即使尝试，也写不了真实 HOME。前后清单照旧采集并原样报告，但不再作为通过条件；事实脚本仍要列出全部差异，交给人判断。
B：保留'无差异'这条要求，但改成只比较测试进程可能写到的路径，排除钥匙串 WAL 和其他会话的目录。缺点：排除清单要人为维护，可能漏掉真实写入。
C：用 fs_usage 这类工具，按进程归属写入。需要 root，要用户自己授权并运行。
D：保持原文不变，T-093 维持 INCOMPLETE。

在你答复之前，T-093 不派第二轮审查、不合入。（T-094 的 needs-decision 20261017T200327Z 也还在等你答复。）