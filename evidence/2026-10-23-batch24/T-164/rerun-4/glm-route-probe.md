# GLM 路线探针（2026-10-24，执行主控）

用户 ~/.codex/config.toml 现为 model=gpt-6.1-sol，无 openai_base_url；GLM 经 [model_providers.magpie]（127.0.0.1:3425/v1，令牌为占位字 magpie）。隔离 CODEX_HOME 只写 model_provider="magpie" 与该节，命令：

`CODEX_HOME=<tmp> codex exec --skip-git-repo-check -m zcode/GLM-5.3-Flash -c model_reasoning_effort="max" "只回复两个字：收到" </dev/null`

magpie /v1/models 返回 200，含 zcode/GLM-5.3-Flash。结果 exit=1，原文：

```
warning: Model metadata for `zcode/GLM-5.3-Flash` not found. Defaulting to fallback metadata; this can degrade performance and cause issues.
ERROR: Reconnecting... 1/5
ERROR: Reconnecting... 2/5
ERROR: Reconnecting... 3/5
ERROR: Reconnecting... 4/5
ERROR: Reconnecting... 5/5
ERROR: unexpected status 405 Method Not Allowed: ZCode: 405 Method Not Allowed — the provider's network firewall blocked requests from this IP; wait a while, or switch to another network or proxy, url: http://127.0.0.1:3425/v1/responses
ERROR: unexpected status 405 Method Not Allowed: ZCode: 405 Method Not Allowed — the provider's network firewall blocked requests from this IP; wait a while, or switch to another network or proxy, url: http://127.0.0.1:3425/v1/responses
```

首次探针未关 stdin，codex exec 一直等 stdin，8 分钟后由执行主控终止，不算 GLM 结果。

追加：`auto/GLM-5.3-Flash` 同样 405（同一上游防火墙）。构思主控 answer 20261024T162332Z 选 A，应用内 Codex 改用 gpt-6.1-sol high，不再探 GLM。

开跑读数（外层会话日志 2026-10-24T14:25:24Z）：5h 窗口已用 52%（300 分钟窗口），周窗口已用 23%。实例 `/private/tmp/t164-dogfood-dc_5rakx`，Electron PID 96695，daemon PID 96694，基线 aacc1bb81。隔离 CODEX_HOME 只含 auth.json 副本与对 demo-repo 的信任。
