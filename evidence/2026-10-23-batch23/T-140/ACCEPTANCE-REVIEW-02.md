STATUS: INCOMPLETE
TARGET: 3e8f2a5e6b036fb5d1bda455c91ce551b021f61a

EVIDENCE:
- 验收来源：T-140 ticket 与外部任务卡；要求真实 Electron/CLI 的授权、未授权拒绝及移除后撤权。
- `test_t140_extra_dirs_e2e.py:230–243` 分开点击移除和保存，中间观察 React 目录行消失；新增保存事件必须为 `[[X], []]`，原有两家 worker 的 X/Y 写入断言保留。
- 直接只读查询旧 SQLite：普通绿态与移除变异均保存 `[X]` 两次；T-RC 启动仍含 X 授权。旧结果不能证明撤权失败。
- 旧 shell 变异的 T-C/T-D 写入断言通过，随后出现 `review_launch_boundary`，实际已有一个 reviewer；不能证明 shell 断言有效。
- 新 mutant 只修改 Claude worker 的 denyWrite。`RUN-OUTSIDE-02.sh:59–82` 要求 T-C 实际结果为 `{x:false,y:false}`、X 出现在 denyWrite、零 reviewer，且普通 green 成功后才认可任一 mutant。
- 冻结驱动和内嵌 Python 语法解析、`zsh -n` 通过；候选与相关工作树文件一致。未发现确定的设置失败。
- 适用能力轴：编排、异步、身份/撤权、界面、文件及本地写副作用；检索与部署运营不适用本次修订。

FINDINGS:
- 无已确认的新失败；两项修正的静态逻辑符合本次审查目标。

COUNTEREXAMPLE:
- 旧 shell 变异会被新判据拒绝：失败位置错误且 reviewer 已启动。
- 旧移除变异会被新判据拒绝：保存事件不是 `[[X], []]`，普通绿态也未成功。
- 新 shell-deny、目录保留变异的原生拒绝结果尚未取得。

LIMITATIONS:
- RUN-OUTSIDE-02 尚未原生运行；不能把静态正确性升级为行为 PASS。
- 本次未启动服务、修改文件或重写旧证据。脚本化模型接口不证明真实模型理解能力。

RULE:
- 在 RUN-OUTSIDE-02 保持“普通绿态通过 + 指定业务断言失败 + 实际边界观察”的联合检查，避免把驱动错误或 reviewer 设置失败计作变异敏感性证据。
