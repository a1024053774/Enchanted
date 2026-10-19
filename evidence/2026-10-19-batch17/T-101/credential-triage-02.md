# T-101 完整历史扫描凭据分诊 02（2026-10-19）

**INCOMPLETE：71 处已逐项分诊，追加豁免草案待用户确认；原扫描仍为 NO_GO。**

对应未瘦身主仓库的完整扫描：89,525 个对象，484 处命中，413 处已批准豁免，71 处未豁免。新命中全部为 credential-assignment，涉及 64 个对象、3 个不同载荷，不表示独立真实密钥数量。

| 类别 | 数量 | 判断 |
| --- | ---: | --- |
| a：公开测试/fixture 假值 | 71 | 68 处既有假 API 常量，2 处窗格 IPC 夹具，1 处 T-102 桌面测试假 token |
| b：示例/占位 | 0 | 无 |
| c：无法判断/疑似真实凭据 | 0 | 无 |

## 判断依据与最小处置

- 68 处与隔离假 API 源码常量完全同值，载荷自带 fixture/not-a-secret 标记；来源主要是 T-078 命令输出、rehearsal、flow、startup 等假服务产物。
- 2 处与窗格 IPC 测试 fixture token 完全同值，载荷有明确假值标记。新对象未继承旧定位的豁免，符合精确绑定要求。
- 1 处由 test_t102_desktop.mjs 第 31 行手写，载荷带明确 fake/fixture 标记，属于桌面测试假输入。
- JSON 的 append_exemptions_draft.entries 仅含新增 71 个 object+offset，没有原文，与旧 413 个定位不重叠。由主控交用户确认；确认前不修改生效豁免。
- 本轮无需要按真实密钥轮换处理的 c 类；静态依据不等同于厂商有效性验证。

## c 类逐条列表

无，c=0。

## 71 处逐条列表

每处在原对象/offset 重新匹配成功，原文仅在内存处理；表中只留前四字符掩码。长度为载荷字节数，offset 为原扫描完整匹配起点。

| ID | 路径 | 对象 | offset | 类型 | 分类 | 长度 | 前四字符掩码 | 判断依据 |
| --- | --- | --- | ---: | --- | --- | ---: | --- | --- |
| N001 | evidence/2026-10-11-batch13/T-078/09b-a06-b1-ideation-p1-01/09b-a06-b1-ideation-01/command-output/00004.stdout.bin | bb4f10ceb72114d8afc3956a251565aad79fa0ae | 3557 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N002 | evidence/2026-10-11-batch13/T-078/09b-a07-b1-ideation-p1-01/09b-a07-b1-ideation-01/command-output/00004.stdout.bin | 218d4f9baf028b8ddaa9fa0d8fab917a8fa99b68 | 3557 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N003 | evidence/2026-10-11-batch13/T-078/09b-a08-b1-ideation-p1-01/09b-a08-b1-ideation-01/command-output/00004.stdout.bin | dee262230fabbe3a355c18577e0a12a1a4edb500 | 3557 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N004 | evidence/2026-10-11-batch13/T-078/09b-a09-b1-ideation-p1-01/09b-a09-b1-ideation-01/command-output/00004.stdout.bin | cb12ffeebaf93a8c2a857716caf83726eba9b5e8 | 3557 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N005 | evidence/2026-10-11-batch13/T-078/09b-a10-b1-ideation-p1-01/09b-a10-b1-ideation-01/command-output/00004.stdout.bin | 1e373164595c1e0097d4f91f615a859fe936a3da | 3557 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N006 | evidence/2026-10-11-batch13/T-078/09b-a11-b1-ideation-p1-01/09b-a11-b1-ideation-01/command-output/00004.stdout.bin | f23a4a127d62380f6b7f934fa5422335ed20d785 | 3557 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N007 | evidence/2026-10-11-batch13/T-078/09b-a12-b1-ideation-p1-01/09b-a12-b1-ideation-01/command-output/00004.stdout.bin | 2527523560b6e4228b60bc375cbc7f6ea8a24bd9 | 3557 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N008 | evidence/2026-10-11-batch13/T-078/09b-a13-b1-ideation-p1-01/09b-a13-b1-ideation-02/command-output/00004.stdout.bin | f8804f5da3d338ef77c57dc77baa44e2814c9a26 | 3557 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N009 | evidence/2026-10-11-batch13/T-078/09b-a14-b1-executor-p1-01/09b-a14-b1-executor-01/command-output/00004.stdout.bin | e6bb839e089bc01da8a47fb6a5ba4324b332907c | 3566 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N010 | evidence/2026-10-11-batch13/T-078/09b-a14-b1-ideation-p1-01/09b-a14-b1-ideation-01/command-output/00004.stdout.bin | db11ee38d5b1cf2033329d1e61a86fa6d41ac59d | 3566 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N011 | evidence/2026-10-11-batch13/T-078/09b-a14-rehearsal-01/flow/sqlite/state.sqlite3 | f434324a652c27939600d339072dfbf41ddadee3 | 226195 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N012 | evidence/2026-10-11-batch13/T-078/09b-a14-rehearsal-01/flow/sqlite/state.sqlite3 | f434324a652c27939600d339072dfbf41ddadee3 | 263059 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N013 | evidence/2026-10-11-batch13/T-078/09b-a14-rehearsal-01/timeout/sqlite/state.sqlite3 | 353434d42b9d4dc516534ebcb2cd285b2dd48f87 | 226192 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N014 | evidence/2026-10-11-batch13/T-078/09b-a15-b1-executor-p1-01/09b-a15-b1-executor-01/command-output/00004.stdout.bin | c42a3de1d02ab2b9591ee68722171822be110e91 | 3566 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N015 | evidence/2026-10-11-batch13/T-078/09b-a15-b1-ideation-p1-01/09b-a15-b1-ideation-01/command-output/00004.stdout.bin | bfd17cfd3e93135b7fc739a696bc3b6ce2675cfe | 3566 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N016 | evidence/2026-10-11-batch13/T-078/09b-a16-b1-executor-p1-01/09b-a16-b1-executor-01/command-output/00004.stdout.bin | c3f19aa77269a06a07ba46d7e9e67fc19bf020b1 | 3566 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N017 | evidence/2026-10-11-batch13/T-078/09b-a16-b1-ideation-p1-01/09b-a16-b1-ideation-01/command-output/00004.stdout.bin | 3f9afbd79bd9cc24aa2f14c7bbbe675f99693260 | 3566 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N018 | evidence/2026-10-11-batch13/T-078/09b-pending-green-01/state.sqlite3 | c6e764c0fc0aa07988e054bbc11769fdbc736add | 197844 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N019 | evidence/2026-10-11-batch13/T-078/09b-pending-green-02/state.sqlite3 | efdb788079486cf56e4f3294fd385b6adbfc7ed4 | 197844 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N020 | evidence/2026-10-11-batch13/T-078/09b-pending-local-01/pending/state.sqlite3 | 1b3a296c8b5ff482628b2e02f3b62ec56031e566 | 201940 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N021 | evidence/2026-10-11-batch13/T-078/09b-pending-local-02/pending/failure-state.sqlite3 | f2f6e3e162e929ac1ec021affa08bacb23fc77b0 | 201940 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N022 | evidence/2026-10-11-batch13/T-078/09b-pending-local-03/pending/state.sqlite3 | b80d7b51df11b1a95b45dfe3d2b94046a091bfd8 | 201940 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N023 | evidence/2026-10-11-batch13/T-078/09b-stage-b-ideation-p1-02/09b-stage-b1-ideation-04/command-output/00004.stdout.bin | fe0033e6cb31d7f60392ceac4ed9debf1b0df9c9 | 3557 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N024 | evidence/2026-10-11-batch13/T-078/09b-startup-pending-entry-02/green/state.sqlite3 | 2151b6252f62fc355bf11fda43b49701d33c2534 | 201922 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N025 | evidence/2026-10-11-batch13/T-078/09b-startup-pending-entry-02/red/state.sqlite3 | fb0ac06633b2b901b185039ee993df25ca4efce7 | 201928 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N026 | evidence/2026-10-11-batch13/T-078/09b-startup-receipt-entry-01/candidate/test/state.sqlite3 | 97b0861baf2a28abdab6429fc285aaf7fce67899 | 201904 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N027 | evidence/2026-10-11-batch13/T-078/09b-startup-receipt-entry-01/m5/test/state.sqlite3 | 0c1ba341fb040d2809228b3141aacecfd22d0176 | 201925 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N028 | evidence/2026-10-11-batch13/T-078/09c-c1-b1-executor-p1-01/09c-c1-b1-executor-01/command-output/00004.stdout.bin | b1954053a6a614815653266f12945211b8536360 | 3566 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N029 | evidence/2026-10-11-batch13/T-078/09c-c1-b1-ideation-p1-01/09c-c1-b1-ideation-01/command-output/00004.stdout.bin | ec4d7aa586b3a0de4dfa75e366eafad05aa8c25f | 3566 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N030 | evidence/2026-10-11-batch13/T-078/09c-c2-b1-executor-p1-01/09c-c2-b1-executor-01/command-output/00004.stdout.bin | f705363d393c4cfbca89aec5b9dc6657b5b2962e | 3566 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N031 | evidence/2026-10-11-batch13/T-078/09c-c2-b1-ideation-p1-01/09c-c2-b1-ideation-01/command-output/00004.stdout.bin | dab9f249d72aef0c67950f6669bc975e1c208908 | 3566 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N032 | evidence/2026-10-11-batch13/T-078/09c-c3-b1-executor-p1-01/09c-c3-b1-executor-01/command-output/00004.stdout.bin | e645325936bd8beb86d84d463f20d72daca87758 | 3566 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N033 | evidence/2026-10-11-batch13/T-078/09c-c3-b1-ideation-p1-01/09c-c3-b1-ideation-01/command-output/00004.stdout.bin | 9ea2e213acb502ae50981c41ac43d3c7a0ad2762 | 3566 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N034 | evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-01/flow/sqlite/state.sqlite3 | c86f530aeb512132070147fc8e4a9ce398e07e83 | 226185 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N035 | evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-01/flow/sqlite/state.sqlite3 | c86f530aeb512132070147fc8e4a9ce398e07e83 | 242569 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N036 | evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-02/flow/sqlite/state.sqlite3 | 5ea22d1c4fca27ddcbcd5bcccf998f318600160a | 226185 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N037 | evidence/2026-10-11-batch13/T-078/09c-caffeinate-parity-rehearsal-02/flow/sqlite/state.sqlite3 | 5ea22d1c4fca27ddcbcd5bcccf998f318600160a | 242569 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N038 | evidence/2026-10-11-batch13/T-078/09c-coordinator-rehearsal-01/real-chain-outside-01/flow/sqlite/state.sqlite3 | 2c3d5ba5326d1c31fa13b6270cc0bdcf779169a2 | 226169 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N039 | evidence/2026-10-11-batch13/T-078/09c-coordinator-rehearsal-01/real-chain-outside-01/flow/sqlite/state.sqlite3 | 2c3d5ba5326d1c31fa13b6270cc0bdcf779169a2 | 242553 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N040 | evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-01/flow/sqlite/state.sqlite3 | 17c90f3e9f8b022339fecd4d030930fc5c6e3119 | 226187 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N041 | evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-01/flow/sqlite/state.sqlite3 | 17c90f3e9f8b022339fecd4d030930fc5c6e3119 | 242571 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N042 | evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-02/flow/sqlite/state.sqlite3 | 901005892501e2546e38bf791233976f0af17075 | 226187 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N043 | evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-02/flow/sqlite/state.sqlite3 | 901005892501e2546e38bf791233976f0af17075 | 242571 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N044 | evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-03/flow/sqlite/state.sqlite3 | 83bd03df0b920fff66255b43407fef3666f00cf7 | 226187 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N045 | evidence/2026-10-11-batch13/T-078/09c-fix-01/real-chain-outside-03/flow/sqlite/state.sqlite3 | 83bd03df0b920fff66255b43407fef3666f00cf7 | 242571 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N046 | evidence/2026-10-11-batch13/T-078/09c-topology-probe-run-01/ideation-p1/09b-a365-b1-ideation-01/command-output/00004.stdout.bin | 8b2fa86a35650f84535ed8e8452c629b8bad22ee | 3624 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N047 | evidence/2026-10-11-batch13/T-078/merge-main-3-outside-01/pending/pending/state.sqlite3 | 94214d7a945e73b033e61f7548b9d4a2212cf9bb | 201940 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N048 | evidence/2026-10-11-batch13/T-078/merge-main-3-outside-01/startup-entry/candidate/test/state.sqlite3 | acbc82fbde5a7c8188277a0383625ff1f4bdca17 | 201904 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N049 | evidence/2026-10-11-batch13/T-078/merge-main-3-outside-01/startup-entry/m5/test/state.sqlite3 | c90df0fd4b6fcc3daa274ccf9e91d29ad7e94e3c | 201925 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N050 | evidence/2026-10-11-batch13/T-078/merge-main-4-t078-regressions-01/pending/pending/state.sqlite3 | b5cebc6f8aa88bfc05e9d6735779ae2079a746c7 | 201940 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N051 | evidence/2026-10-11-batch13/T-078/merge-main-4-t078-regressions-01/startup-entry/candidate/test/state.sqlite3 | a95bf6c6cda76519d1854bc142cbee1f99136e7c | 201904 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N052 | evidence/2026-10-11-batch13/T-078/merge-main-4-t078-regressions-01/startup-entry/m5/test/state.sqlite3 | 0171ce99917dbec44f6ef11b89efe12d5ead01a5 | 201925 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N053 | evidence/2026-10-11-batch13/T-078/p1-materials-03/launch/command-output/00010.stdout.bin | 1646b3744e4a2358c35d16aa2a67fc238262d9e3 | 3246 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N054 | evidence/2026-10-11-batch13/T-078/p1-materials-05/launch/command-output/00010.stdout.bin | b6fcaaf104c9013718bcb15148145356ce586c26 | 3260 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N055 | evidence/2026-10-11-batch13/T-078/p1-materials-06/launch/command-output/00010.stdout.bin | 410b021a7b324ee69e15ca84e9c02de895f0f10e | 3265 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N056 | evidence/2026-10-11-batch13/T-078/p1-materials-08/launch/command-output/00010.stdout.bin | 50016bae5ed3c1977a97684d5f32fa53b5fd2b48 | 3361 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N057 | evidence/2026-10-11-batch13/T-078/p1-materials-08b/launch/command-output/00010.stdout.bin | 2e39a48500fb0a82ee0a4a42ae39cbd680191ab5 | 3373 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N058 | evidence/2026-10-11-batch13/T-078/p1-materials-08c/launch/command-output/00010.stdout.bin | d5c1d70d7268b2938e8c34cee8b5ae91bb7b5343 | 3373 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N059 | evidence/2026-10-11-batch13/T-078/p1-materials-08d/launch/command-output/00010.stdout.bin | a6689016f5fdb1d44d86efa1ac25f965267751e5 | 3373 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N060 | evidence/2026-10-11-batch13/T-078/p1-materials-08e/launch/command-output/00010.stdout.bin | 3b5cc1e81af5115ab042050aa510c82faa2eb29a | 3373 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N061 | evidence/2026-10-11-batch13/T-078/p1-materials-09/launch/command-output/00010.stdout.bin | ae9933c9a19f286c93c1bf851487101d39c18676 | 3361 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N062 | evidence/2026-10-11-batch13/T-078/p1-materials-09a2/launch/command-output/00010.stdout.bin | 0dac879dd06e55d7702f027a7ecdfd2d024a5baf | 3385 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N063 | evidence/2026-10-11-batch13/T-078/p1-materials-09a3r2-block/launch/command-output/00010.stdout.bin | 35eed30ab725f7f23e0f5550230099502a2126bd | 3481 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N064 | evidence/2026-10-11-batch13/T-078/p1-materials-09a3r2/launch/command-output/00010.stdout.bin | ba604ad264ee05291c44f00eff9668d0034fc2c0 | 3409 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N065 | evidence/2026-10-11-batch13/T-078/p1-materials-slice1-green-3/launch/command-output/00010.stdout.bin | 1fa4b6b9784258484f276450991e32fbac6f92c7 | 3714 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N066 | evidence/2026-10-11-batch13/T-078/p1-materials-slice1-green/launch/command-output/00010.stdout.bin | 3d33b3d19de2a6f6ba60bcfd6f50b7af78f83e70 | 3690 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N067 | evidence/2026-10-11-batch13/T-078/p1-materials-slice1-red/launch/command-output/00010.stdout.bin | 1c371729eda3b9ae88f519cff609de3ae271fb64 | 3666 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N068 | evidence/2026-10-11-batch13/T-078/slice1-readback/database/state.sqlite3-wal | 82bf454c1a4036ae1751fa208ae2c54f908d8fce | 754621 | credential-assignment | a | 28 | a2a-… | 与已核对的 claudeLaunch.ts 隔离假 API 常量逐字节相同；载荷含 fixture/not-a-secret 标记，属于固定假服务数据。 |
| N069 | workbench/tests/test_t091_pane_ipc.mjs | 08732f613a4bd3832b4501e28c3158a4888ca2e1 | 8197 | credential-assignment | a | 24 | non-… | 与既有 pane IPC 测试的假 transport/window-input 响应常量完全相同，载荷有 fixture/fake 标记；新对象不能继承旧定位豁免。 |
| N070 | workbench/tests/test_t102_desktop.mjs | b717945e8d28d602cb708127ca1b62cfa3955608 | 2481 | credential-assignment | a | 15 | priv… | test_t102_desktop.mjs 第 31 行手写受控桌面测试假 token，载荷带明确 fake/fixture 标记，未从用户认证文件取得。 |
| N071 | workbench/tests/test_t091_pane_ipc.mjs | 426ebb1de1aaf523f655c8bd7cb99e11384a9474 | 6714 | credential-assignment | a | 24 | non-… | 与既有 pane IPC 测试的假 transport/window-input 响应常量完全相同，载荷有 fixture/fake 标记；新对象不能继承旧定位豁免。 |

## 源码定义定位

仅比对字节相同与源码假值标记，不保存常量原文。

| 组 | 路径 | 对象 | offset | 行 |
| --- | --- | --- | ---: | ---: |
| fake_api | workbench/src/claudeLaunch.ts | 119f37d3e8707e0c1cf9a7f58607c2f0cac0829e | 5914 | 74 |
| pane_ipc | workbench/tests/test_t091_pane_ipc.mjs | 986d184a07ce6e0e531ec7fb035161317c24233f | 4635 | 71 |
| desktop | workbench/tests/test_t102_desktop.mjs | b717945e8d28d602cb708127ca1b62cfa3955608 | 2481 | 31 |

## 范围与状态

用户本轮裁定为不瘦身、直接快进推送 main，再处理已有 GitHub 备份的不需要的大文件。本报告只分诊新增命中，不推送或清理；旧 413 条批准不会自动授权新增 71 条。

源扫描：`/private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/4cb6cda5-1e37-4e3e-8ff5-2755a799eb7c/scratchpad/t101-full-scan.json`。

未访问外置盘；未修改规则、生效豁免清单、历史、其他证据或用户配置；未调用额外模型。project_map status 仍为稀疏 worktree 原有 8 problems、0 stale living docs，未改地图/术语表。
