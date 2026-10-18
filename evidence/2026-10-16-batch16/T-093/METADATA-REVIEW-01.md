STATUS: INCOMPLETE
TARGET: 0a52043f86e5384efae943cbafe859ccb535ec14；仅审相对 47286b7bda7d6497a1c62a067308b18ea3fc1f7a 的元数据增量及直接调用链。
EVIDENCE:
- 开始、结束时 HEAD 均为冻结候选，受控文件无修改；project-map status 均为 0 problems、0 stale。
- 已读指定 skill、agent-products.md 及两个外部输入。product-chain-04-startup-red.json 记录旧候选六场景均在 Node main 前因真实 HOME 的 lstat EPERM 失败，没有结果 JSON，也未到达变异业务断言。
- 对新旧 policies 做纯内存 AST/S-expression 比较：C/F 仅增加精确 literal 路径的 file-read-metadata；其余规则一致，D 完全一致。未发现正文、写入、网络、fork 或 Security 权限扩张。外部 facts 入口使用同一 helper。
- C/F 新观察均在产品服务开始前执行：查询祖先元数据、解析入口、尝试读取现存公开 AGENTS.md 的正文及枚举其父目录；驱动在应用 profile 前验证目标存在且不是符号链接。
- 旧局部检查只证明构造、合成状态或 mock 行为。旧独立探针的 C 主进程及继承子进程都是 Python；F 虽启动 Node，却没有产品 F 的 HOME 读取屏障（probe_t093_parallel_profiles.py:36–54、270）。因此未覆盖实际 Node 入口与该读取屏障的组合。
FINDINGS:
- 本次边界内未发现可达或已复现的新增违约；此结论不构成 OS 验收通过。
COUNTEREXAMPLE:
- 纯内存执行新增结果谓词，正文可读、已读 1 字节后声称拒绝、ENOENT 冒充权限拒绝、目录可枚举及入口未解析五种记录均被拒绝。
- 新实际正文读取反例已接入 C/F，但尚无冻结候选上的 OS 执行结果；现有 synthetic recorder 证据不能替代它。
LIMITATIONS:
- 未执行 OS sandbox、服务、供应商 CLI、真实认证、Security 查询或 ps；未修改文件或原始证据。
- 新测试视为待核验的证据，没有作为独立 oracle。实际启动恢复、权限优先级及正文／目录拒绝仍须通过真实入口重跑。
- 适用轴为编排、异步、身份范围、CLI、文件、外部副作用和运维；本次只覆盖它们与元数据增量的交点。检索／记忆 N/A：该增量不涉及。
RULE:
- 防止再次以缩减探针替代实际入口：冻结候选须经 run_t093_login_chain.py 跑完六场景，再由独立结果核对器确认各预期业务断言、C/F 元数据成功及正文／目录拒绝；外部 facts 入口另作真实启动复验。缺失结果或入口前崩溃必须保留为 INCOMPLETE。
