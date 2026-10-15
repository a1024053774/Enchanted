# T-082 主控记录 02（2026-10-15 UTC）

worker 第一切片后，沙箱外批次均由主控运行（OUTSIDE-COMMANDS-01..07）。worker 三次自行请求沙箱外升级（主控两次 Esc、用户一次选 No），之后改为全部交脚本。
- 01：副本复制探针，经 ROOT 路径错、目标不在 state、仓内 symlink 解析回源三次失败后 PASS（仓内 symlink 按内容复制、越界拒绝，SYMLINK-POLICY.md）。主控代删 worker 留在 /tmp 的 3 个临时项。
- 02：tracer + 四种启动参数变异；首轮 wrong-workspace 未被拒——产品缺陷（reviewLaunch 未核对 argv -C），修后全 PASS。脚本 find /tmp 不跟随符号链接，8 个 q76 目录由主控打包入证据后删除。
- 03/05/06：结束核对 PASS；T-077 PASS；T-076 质量 runner 被自带源码审计拒收（审计要求验收文件相对 a7f4cc30 不变，而 D3 必须替换只读断言，属预期后果）；主控否决了用 MAIN_ROOT 跑回归的 04（测不到候选）。
- 07（检查点提交 0dd00d09d 上）：票据点名的 T-076 三项性质 tracer_wrong_candidate、tracer_reused_native、tracer_writer_cannot_review PASS。
- 待：launch-policy 夹具错疑为旧快照 taskCards.ts 无 oracle_paths（需在 main 上证明既有）；T-076 runner 锚点是否迁到新基线作为待决问题上报；真实 Codex 回合（≤4）脚本待主控审。
