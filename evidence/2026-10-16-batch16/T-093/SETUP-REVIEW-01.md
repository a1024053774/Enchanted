STATUS: FAIL
TARGET: 28276275d96e97d3ac861600530831a5f2d84f91
EVIDENCE:
- 开始、结束 HEAD 相同；受控文件无变化，原有未跟踪文件清单未变。project_map status：0 problems、0 stale。
- 指定外部证据确认旧链停于 R；15.236 秒只支持超时推断，原始命令和异常仍未知。external-facts-05 只证明旧候选的 V 入口。
- 独立纯内存检查通过：回收失败保持原超时对象及部分 stderr；阶段、errno、脱敏消息保留；独立合成凭据变体未进入捕获输出。没有写盘、启动进程或发送信号。
- 只读检查三种保留目录；初始目录通过 inspect，且完全没有进程身份检查。未读取认证正文或删除夹具。
FINDINGS:
- [P2] workbench/tests/cleanup_t093_retained_fixture.py:45 — 无元数据时直接跳过全部停机检查并允许 remove 删除。run_t093_login_chain.py:155–181 的运行中 R/G 阶段恰好具有这种目录结构，最长可持续至 90 秒；因此“已识别目录”不能证明“已停机”。应要求初始夹具也具有绑定根目录的 R/G 停机证据，缺失时拒绝删除。
COUNTEREXAMPLE:
- 在 R 已创建初始目录、G 仍扫描时调用清理入口：目录满足全部结构条件，没有 metadata_files，inspect 返回成功，remove 随后删除活动运行目录；当前未拒绝。
- Git 回收抛出独立 PermissionError 的反例被正确处理：原 TimeoutExpired 保留，回收错误单列。
LIMITATIONS:
- 没有当前候选的完整 OS 链绿态、真实进程组终止或实际保留夹具清理证据；这些边界仍为 INCOMPLETE。
- 当前保留目录未被证明正在运行；上述发现针对入口可到达的活动初始目录状态。
- 新增测试仅作待审证据，未用其通过结果替代外部 oracle。
RULE:
- N/A；未确认本次发现属于已有重复失败类别。
