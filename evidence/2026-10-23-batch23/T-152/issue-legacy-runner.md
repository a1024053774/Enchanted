T-152 范围外发现：`workbench/tests/run_t082_boundary.py:91–106` 仍用已移除的 sandboxMode/networkAccess/excludeSlashTmp 字面量定位变异，网络开启拒收也已被 T-141 取代；`test_t078_quality_host_bootstrap.py:16,121` 导入该 runner。共享 `controlled_quality_pty.ts:51–64` 展示 Open restricted 后不发 T-141 所需 native ready。因此不能只改当前测试的网络断言就取得端到端绿态。

建议：本票不改共享文件，使用专用 host 适配原生 ready、专用沙箱外脚本跑现行有效变异；旧 runner 后续另行迁移或标历史。另有历史小报告输入仍受控但在稀疏 checkout 中缺失，当前票将保存同一 Git blob 为专用输入，保留 roundtrip 检查。
