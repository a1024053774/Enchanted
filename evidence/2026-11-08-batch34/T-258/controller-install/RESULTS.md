# T-258 集成与安装检查

状态：PASS。代码已通过门禁集成，安装包已核对，正式应用已替换并正常重启、读回。

- 交付候选：66e88ffe2251ea045a398c9003fef1795c8a2af8；集成：b5fed20893d499aae47a0a87bb2718c5d893819a。
- attempt：7043f6b6-95a1-403d-a487-4587e2c02d62；最终 review：79085ebc-b4b8-45b3-9362-4fd20fe376fe。
- 审查 119 案通过，4 个错误身份实现被检出；首审唯一测试缺口已关闭。完整报告在 ../controller/review-a4-02-result.json。
- 真实 CLI 新基线红绿与边界见 ../controller/RESULTS-NEWBASE.md。最终补测试没有修改产品或驱动，不称最终 SHA 重跑了真实 CLI。
- 包内 revision 与候选一致，codesign --verify --deep --strict 成功；check_package.py 使用包内 Electron 和源码运行 119 案通过。原输出见 package-runtime-01.json、package-module-01.json。
- 标准构建已清理缓存；独立 checkout 的依赖副本按 dependency-cleanup.json 清理。保留安装产物。两个 verification 工作树仅多出自动生成的模块结果 JSON，已核对并保留，见 ../controller/retained-verification-02.json。

Works：原始输入和身份核对成立时恢复晚启动；无可信来源、身份替换、过期 attempt 仍拒绝。
No regression：119 案保留原 117 案；同产品输入的 T-257 与 native-origin 结果经独立审查核对，未冒充本次重跑。
正式安装：`install-01.json` 保存原版本、目标版本与备份位置；`daemon-status-new-01.json` 和 `readback-01.json` 保存新后台与窗口观察。原界面正常退出，旧后台经 daemon_stop 停止；新界面显示“后台已连接”，T-258 为“已集成”。没有新文稿授权等待的日志证据。

Risk / undo：旧应用在 `/private/tmp/enchanted-rollback-t258-20261108/Enchanted.app`，可在正常停后台后恢复。修复只处理有可信身份的晚启动，不证明慢启动根因已消除。不 push，不手改正式数据库。
