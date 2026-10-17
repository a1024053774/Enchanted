# 09A-3 变基后检查与冻结交接

2026-10-14，主控 #143。变基已由主控完成，起点 `ff3708d0b647ddf71d272e6fb87f6424c7533163`，基线 main `87e954a2f4059d471e3e240872b565217e29b0b5`。五个停点的原日志、冲突原件、解决稿、固定预期与实际执行结果均保留在 rebase-continue-01～05，随本次提交纳入；worker 没有自行 add／continue。

**沙箱内相关检查局部 PASS；沙箱外回归与新材料仍 INCOMPLETE。** 没有启动真实 Codex／Claude／API／模型或额外代理，不改 gates/core.ts／taskCards.ts，不 push。

## 新证据

- [入口 17 项](rebased-local-09a3-02/entry/results.json)、epochs 7、窗口身份 5、窗口绑定 8、inbox 域 11、主控静态计划 2、Claude signal 3、Esc 收据 12、两回合配置 3、假 HTTP handler 内存检查全部通过，原始命令与输出在 [local result](rebased-local-09a3-02/result.json)。该汇总因旧 pane 夹具失败仍保持 INCOMPLETE，不改写为全绿。
- 旧 pane 夹具缺 record.env.CODEX_HOME，三项出现 TypeError。只补齐每 launch HOME、native metadata cwd 与 nativeEnded=false，断言不改；[独立重跑 11/11 PASS](rebased-pane-runtime-green-09a3/results.json)。这是夹具契约更新，不给产品加旧配置 fallback。
- [真实 inbox 客户端 8/8 PASS](rebased-inbox-entry-09a3/results.json)，经实际门禁 CLI／daemon／SQLite，未启动 agent。
- [变基后已知坏变体](rebased-counterexample-09a3/result.json) 重新执行真实 socket/hook CLI：忽略声明代次、恢复旧控制字节分类、丢弃成功阻断 JSON，均触发目标行为违约并被拒绝，exit 1。副本只在 /tmp，不改产品、core 或其他分支，不构建；不复用变基前反例。
- T-078 的两个终端 receiver 也缺 metadata.cwd；[真实文件写入探针红态](rebased-receiver-metadata-red-09a3/result.json) 两者 cwd 都缺失，补齐后 [2/2 PASS](rebased-receiver-metadata-green-09a3/result.json)。cwd 含中文、引号、反斜杠，C 写入按 JSON 规则转义。探针在 pipe 上只检查终端设置前写出的 metadata，预期 ENOTTY 退出不是缺陷红态，也不是完整 PTY 验收。

首个本地汇总脚本的源文件打包错误（将 Python 的 -B 当路径）保留在 rebased-local-09a3-01，未执行产品检查、不当红态。所有修正后的证据另存，未覆盖失败。

## 环境失败与主控阶段

worker 错把依赖 /bin/ps 的 coop 回归放进沙箱；八项在身份核对与清理处均 PermissionError，0 failures／16 errors，不算产品红态，原件保留在 rebased-coop-local-09a3。八个隔离 Node 后台待主控的精确 cleanup 阶段核对并经认证 daemon_stop 停止，根与原件保留；已向 executor 收件箱发送 `20261014T142134Z-worker:t078-09a3r-report-001`，不再用提问工具发请求。

同一 [阶段脚本](rebased-stage-09a3.py) 有 cleanup 和 regression 两个明确模式。regression 要求 cleanup PASS 与冻结提交不变；串行运行实际 Electron/PTY 的 runtime 12、input-failures 11、worker-inbox 14、四个 worker 权限反例，再跑现有 8/9/18 与 CAS 1（顺序以脚本为准）。真实供应商回合为 0，原受控 receiver 替代 vendor；构建缓存必须在外置盘，缺盘即停，不回退。每段失败保留，不重试；不把 GUI/PTY 夹具当实际 Claude 证明。

现有 8/9/18 运行器的受保护业务断言保持原样，由当前 main 的外部 actor/reviewer 夹具执行；旧坐标 auditor 是日期记录，不改断言去迎合旧坐标。三个旧门禁 fence/CAS/lock 变体本阶段未重新执行；变基前结论不转为本阶段 PASS。独立 reviewer 仍待主控，不冒称通过。

## 新材料

生成工具改为必须显式指定新代 `09a3r`，新实例分别为 p1-materials-09a3r／p1-materials-09a3r-block。旧根与旧材料保留；旧 `outside-09a3.sh clean launch` 参数不能暗中选择新实例。新调用必须带 `09a3r`，还须逐次 launch、screen、key、readiness、continue 审批。

正例仍由主控自行处理草稿、看到空框后声明放行；反例保留恢复草稿并特意作空框声明，要求 UPS JSON block、API 总数只有 1。驱动不代发清空键、不自动点声明、不裁剪、不重送，Stop 不改。两个实例串行，真实模型上限 0。

先提交本批夹具更新、生成工具与证据，写入冻结提交号，再执行沙箱外阶段；之后用该提交生成两套新根／ID／nonce／来源快照，静态逐字节核对，最后交新 launch 审批与材料提交。当前尚未生成新包，也未启动实验；T-078 保持 open、INCOMPLETE。

本轮随后读回主控 cleanup 结果：八个后台逐项身份核对、认证停止及退出确认均 PASS，根与失败原件保留，见 rebased-outside-cleanup-09a3/result.json。执行交接另写入 executor 收件箱 `20261014T143421Z-worker:t078-09a3r-report-001`，并按用户“有问题直接向主控发送”用 Herdr 对已核对的主控窗格 wF:pM／session 9a64ed90-d8e7-497a-803e-3ecdbc8fd69e 提交一次通知。实际文字在该窗格可见；其后主控报告 Usage limit reached again，自动继续时间为本地 13:00。未操控限额界面、未重启服务器、未额外开代理，不把消息写入收据当执行完成。当前 Git 仍为 ff3708d0；冻结提交与外部回归结果尚不存在，因此新材料仍 INCOMPLETE，不能标 MATERIALS READY。
