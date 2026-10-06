---
id: T-014
title: Check evidence capture and artifact packaging before model runs
type: task
status: open
blocked_by: [T-009]
claimed_by:
supersedes:
---

## Question

如何让证据采集、失败分类与归档问题在更昂贵的真实模型实验前暴露？
已有实例包括 Python 写文件 API 不兼容、观察器未正确读取 intent、诊断 Path 无法序列化、
工具输出截断及内嵌 Git repo 误登记为 gitlink。证据：
[F06、F07](../../findings/a2a-session-retrospective-2026-10-06.zh-CN.md)。

优先复用现有采集脚本和已修复的路径，避免新增重复包装器。
检查需覆盖目标 Python 环境、原始 stdout/stderr 先保存、结构化结果有效、
业务失败与夹具错误分开，以及归档确实包含所需 Git/SQLite/源码材料。
提交前检查意外 gitlink；保留旧目录与错误产物，不为绿色结果重置现场。
已知坏采集器不能产生产品 PASS；有效的产品反例仍须在业务断言上失败。
不得仅检查 JSON 可以解析就宣称产品通过，也不使用海量终端输出代替保存的完整原始记录。

本票记录待办，不重跑现有模型实验，不改动已有验收预期。

## Resolution

未执行。
