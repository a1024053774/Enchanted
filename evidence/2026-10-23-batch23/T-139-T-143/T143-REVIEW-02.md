# T-143 有界复核 02

状态：**INCOMPLETE**。限定复核未发现未解除缺陷；整体真实联合验收仍未运行。

审查来源：同一独立只读会话 `/root/t143_acceptance_review`，冻结版本 `130284e35808f9faddaedd5eea581938e920693e`。
只复核前次 P1 和新增保留集边界检查；审查期间 HEAD、tracked 文件及原有两份 untracked inbox 文件保持不变。

P1 已解除：联合 e2e 第 206、209 行均使用 `[aria-labelledby="settings-terminal-accessibility"] input`。
独立解析实际 section，唯一匹配其中 checkbox；旧选择器已不存在。
证据：`/private/tmp/t143-review-selector-130284e35.json`。

独立重跑 selection：PASS。隐藏数 N−1=3、N=4 时保留最旧窗格和凭据；N+1=5 时淘汰最旧窗格，
其 snapshot 请求拒绝且凭据撤销；关窗后所有已签发凭据均关闭。

```sh
node --experimental-vm-modules workbench/tests/test_t139_selection.mjs /private/tmp/t143-review-selection-130284e35.json
```

project-map 为 0 problems、0 stale docs。未启动 Electron/GPU，未运行真实联合 e2e 或性能测量。
真实结果需由 RUN-OUTSIDE-02 取得，不将本地隔离检查上调为最终通过。
