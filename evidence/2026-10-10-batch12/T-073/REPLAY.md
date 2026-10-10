# T-073 重放命令

所有目录和 label 必须全新，不覆盖已有失败证据。无模型的 CLI/Git 套件：

```sh
python3 -B acceptance/test_herdr_traceability_e2e.py --artifacts evidence/2026-10-10-batch12/T-073/new-local
python3 -B evidence/2026-10-10-batch12/T-073/make-mutant.py /tmp/new-mutant
python3 -B acceptance/test_herdr_traceability_e2e.py --scripts-root /tmp/new-mutant/scripts --case test_commit_no_verify_and_plain_counterexample --artifacts evidence/2026-10-10-batch12/T-073/new-mutant-output
```

套件的 Herdr 为明确标注的替身，Git、文件与产品 CLI 真实；每次自动保存命令、stdout、stderr、退出码、summary 和每个 Git 夹具的完整归档。最后一条应在尾注数 8≠9 处失败。

真实模型绿态（需要处于本票授权范围，且当前终端为 Herdr pane）：

```sh
python3 -B evidence/2026-10-10-batch12/T-073/real-probe.py prepare new-green
python3 -B evidence/2026-10-10-batch12/T-073/real-probe.py start-green new-green
cp evidence/2026-10-10-batch12/T-073/green02/prompt.txt evidence/2026-10-10-batch12/T-073/new-green/prompt.txt
python3 -B evidence/2026-10-10-batch12/T-073/real-probe.py prompt new-green
python3 -B evidence/2026-10-10-batch12/T-073/real-probe.py inspect new-green
```

要复验审查发现的重复旧尾注场景，把上述 cp 的来源改为 green03/prompt.txt；预期旧身份清除、Signed-off-by 保留且受管尾注仍为 9 项。已知坏版本的两条用例在 review-red-duplicates01、review-red-checks01；当前完整绿态为 local04-review-fixes。

确认该 agent done/idle、两个提交都存在后，再按此顺序执行，不能在 plain 之后重跑 collect（此时 HEAD 已变化）：

```sh
python3 -B evidence/2026-10-10-batch12/T-073/real-probe.py collect new-green
python3 -B evidence/2026-10-10-batch12/T-073/real-probe.py plain new-green
python3 -B evidence/2026-10-10-batch12/T-073/real-probe.py finish new-green
```

collect 保存两份消息、完整启动记录、环境读回、两行原钩子痕迹、主控给定的精确计数命令输出和完整 Git 归档。finish 仅在 done/idle 执行，复制不含认证的原生记录到 Git 忽略的 sessions 目录，保存用量摘要，关闭自己的 pane，再删本次隔离 home。

打分只在一个 attempt 结束时写一次；现有 green02/green01 的夹具 attempt 已记分，不得重复。原始命令和独立字段核对见 `score01/commands.jsonl`、`check-score.py`。重新生成打分 evidence 时，以全新的启动记录号和 attempt 调用：

```sh
scripts/score --launch NEW_LAUNCH --facts evidence/2026-10-10-batch12/T-073/score-facts.json --result 通过 --boundary-discipline 3 --boundary-reason '夹具：允许路径内' --engineering-taste 2 --engineering-reason '夹具：可直接使用' --notes '独立打分夹具'
scripts/score --launch NEW_ABANDON_LAUNCH --result 放弃 --reason '夹具放弃原因'
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
```

缺必填项反例是第一条移除 `--notes`；预期非零，`records/scores.jsonl` 字节不变。每次都把命令/结果读回保存到新目录。Herdr 期的事实 JSON 是执行主控提供的独立验收事实，脚本从它和启动记录填写客观字段；本切片没有门禁事件自动汇总。
