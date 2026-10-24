# GLM-5.3-Flash 看图能力探针（T-164 第三轮前）

- 时间：2026-10-24T10:06:00Z；codex-cli 0.164.0；隔离 CODEX_HOME（/private/tmp 下，只复制 auth.json，config 只有 model=zcode/GLM-5.3-Flash、effort max、openai_base_url 取自用户 ~/.codex 的 http://127.0.0.1:3425/backend-api/codex），用后整个删除，不入证据。
- 命令：`codex exec --skip-git-repo-check -s read-only "<问左侧栏文字>" -i shot.png`，图为 `evidence/2026-10-23-batch24/T-169/green-1.png`。
- 结果：逐字列出 8 条左侧栏文字（demo、2、main · 无上游、执行主控 项目终端 · 未知、刚刚、worker T-166-probe · cl… 刚刚、独立终端 家目录、刷新列表），执行主控打开原图核对一致。结论：能读截图，外层测试员可换 GLM。Computer Use 插件本身是否与该模型配合，以开跑后实际操作为准。
