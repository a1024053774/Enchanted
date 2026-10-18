STATUS: INCOMPLETE
TARGET: 034964517cc57d404e417eb3dec07d794e565d35
EVIDENCE:
- 只读检查指定探针、launcher 和两个直接辅助文件；依据独立提供的 OS 边界契约。
- 网络负例明确要求 EPERM/EACCES；synthetic HOME mutant 保留真实 HOME 拒写规则，并检查创建、删除及业务断言失败。
- 清单差异仅作信息记录。未执行 OS 探针。
FINDINGS:
- [P1] workbench/tests/probe_t093_parallel_profiles.py:128,191 — 任意非零 Mach 查询结果都被当作权限拒绝。服务不存在或不可用也能满足断言，无法证明 Security Mach 被沙箱拒绝。只接受权限拒绝对应的返回码；不可用应报告 INCOMPLETE。
- [P1] workbench/tests/probe_t093_parallel_profiles.py:115,151,405；workbench/tests/t093_profile_endpoint.mjs:58 — 60 秒期限只在 Node 启动后生效。独立 U 进程在此前及 Node 结束后执行没有硬期限的元数据遍历；若 C 的 sandbox-exec 启动失败，controller 的清理不会运行，U 可能无限期残留。应在每个独立进程开始角色工作前设置跨 exec 保留的硬期限。
COUNTEREXAMPLE:
- 删除 Mach deny 规则，而两个查询返回服务不可用的非零码：当前业务断言仍会接受。此反例由静态判断确认，未进行真实查询。
- C 无法进入 controller，同时 U 停留在元数据遍历：Node 定时器尚未安装，controller 清理也未运行，当前代码没有强制终止期限。
LIMITATIONS:
- 没有真实 OS 边界证据，因此不能判定沙箱契约 PASS。
- 未启动服务、供应商 CLI，未读取认证内容，未执行 Security 查询或请求提权。
- 此审查仅涉及待执行探针的安全与误判风险，不构成产品链路验收。
RULE:
- 权限负例须接受明确的权限拒绝结果，不能把资源不可用当作权限隔离；在探针结果断言处检查。
- 独立后台进程的硬期限须覆盖启动、前置检查和收尾，不能依赖主控成功启动；在进程进入角色工作前设置。
