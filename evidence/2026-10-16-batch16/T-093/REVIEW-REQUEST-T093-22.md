# T-093 请求 22：只重跑 isolation 和 empty-reopen

整票 **INCOMPLETE**。依据主控 #139，产品与 app 不改，最小修复仅在 T-096 runner 的 renderer 就绪判定；新增离线测试和摘要保留旧红态。最终候选绑定交接末行 `T-093 FROZEN <完整 SHA>`。worker 本轮不调用模型、真实 CLI/helper，不申请升级，不用问题面板；原件和旧现场不改不删。

## 诊断和合同

T-096 要求每个已保存窗格保留身份。缺 argv 的主控和未恢复 worker 仍应显示 launch／角色与未恢复提示；只有显式关闭全部后第三个窗口才应为 panes=[]。不能把没有 launch 的占位格视为成功或正常的“未恢复”。

- r21-isolation 第一帧的三个 DOM pane 均缺 launch：构思 eaf7a950-8223-4cde-807a-f6afe2f7bac5、执行 63458f30-caab-4156-b784-b0a575622fff、worker 1e14971f-3bd9-44e5-af94-a34ff1972d5a；后端 snapshot 已分别提供缺 argv 拒绝／恢复成功／worker reclaim 拒绝。
- r21-empty-reopen 第一帧缺身份的是执行 0cd35c01-dbc4-4276-957d-3e034b19b390 和 worker cdc8b0d5-e82c-4c93-8dc6-67bca9c9b54d；构思已渲染。原 observer-protocol 的第 2 次 inspect 三格身份均齐全，runner 却仍用最早缓存的 second 逐格查找。
- r18b 同名两场的 after-view 均已有完整 DOM 身份；失败主控／worker 也有 launch 和未恢复提示。app、driver、runner 在 r18b 的 57c3bfb63 与 0be3d3ff2 间没有 diff。证据来源及只读清单见 r21-two-case-diagnosis-22.json。

driver 将 IPC snapshot 存入 map 的时刻早于 React 提交。inspect_window 原先把 map 存在误当 DOM 已就绪。现在要求同格 DOM 的 pane key、launch、task、role、preset、thread 和输入状态与 snapshot 对齐，才结束既有等待；没有从 snapshot 补 DOM 字段，没有忽略任何格。4 秒期限、64 RPC 预算以及所有后续绑定、只读／历史／argv、空窗和归档断言不改。

离线红态 renderer-readiness-red-22.json 使用 r18b 旧 runner 和保留原件观察，已检出过早就绪。修正后同一 24 项通过，见 renderer-readiness-green-22.json；持续占位仍超时，合法空窗和已渲染的拒绝恢复正例仍接受。测试只提取运行 inspect_window／wait 与原只读断言，不导入整个 runner，不启动外部进程或 GUI。本轮没有新增模型独审，也没有进行原生重跑。

## 主控沙箱外命令：仅两场

使用原 T096-REGRESSION-16.sh 的 HEAD／源码清洁／挂载／新目录保护；output 始终在外置盘 **T-096** 下。标签全新，不覆盖 r21。CLI 版本、mode／panes、初始化逐屏批准、模型和 POST 预算 0 沿原合同。worker 不执行下面命令。

```sh
repo=/Users/luckye/Documents/Code/a2a-wt-t093
candidate=替换为本轮完整冻结SHA
cli=/Users/luckye/.local/share/claude/versions/2.1.302
approval=主控本轮逐屏初始化批准记录位置
resume="$repo/evidence/2026-10-16-batch16/T-093/T096-REGRESSION-16.sh"
git -C "$repo" diff --quiet HEAD -- evidence/2026-10-16-batch16/T-096/run_restart.py
bash "$resume" isolation "$repo" "$candidate" "$cli" "$approval" t093-r22-isolation-01
```

要求 rc 0／PASS、cleanup_complete=true；构思缺 argv 明确未恢复／只读且无成功事件，执行仍按完整 argv／原 session／真实身份恢复并显示历史 nonce；worker 未恢复、receiver 未重启、attempt 不变。归档比较必须完整通过。任何异常保留新现场即停，不重跑其他五场、不自动补键。

首场全部通过后再运行：

```sh
bash "$resume" empty-reopen "$repo" "$candidate" "$cli" "$approval" t093-r22-empty-reopen-01
```

要求 rc 0／PASS、cleanup_complete=true；两主控的完整 argv、session、身份、历史和 worker 不恢复断言全部通过。显式关闭全部后 saved=true、pane／key 集合为空，重开第三窗口仍为空、不重新授权 worker、不改 task／attempt。模型／假 POST 均为 0。

isolation 旧现场的归档问题单列：当前只读清单显示 DB／WAL 大小不同，其余条目一致，原因尚未确定。旧 `/private/tmp/t078-2-t096-7mp3b5v6` 与外置原件原样保留；本修复没有清理它们，也没有放宽归档比较。新运行如再次归档失败仍为 INCOMPLETE，停止并保留新证据。

五场原生 PASS 只引用主控的 r21 结果，本轮不重跑。原两场 INCOMPLETE 不改写为 PASS。完整验收仍由主控在新证据后经唯一门禁完成。
