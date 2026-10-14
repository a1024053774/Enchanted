# T-077：只修 runner 的 hook 符号链接重建

准备 **READY**，局部 runner 检查 **PASS**；产品业务结果仍 **INCOMPLETE，未运行**。产品固定 `5d0bf1e84c02fbcb4b7699cdd9a48c4f6582c6b4`，修前产品仍为 `7b3463c4`。没有改产品、hook、测试或业务断言，没有运行模型或 daemon。

主控 #115 的更正已核对：final-02 留下的 `/private/tmp/t77final-qv00yoln/review-preimage.tar` 在 Python tarfile 中有 55 个可见条目，其中 26 个是 `workbench/hooks/` 直接子项、类型 symlink、目标恰为相对同目录的 `hook.py`；没有可见 pax 全局头。旧 runner 在第一个合法 hook symlink 上抛 `Unexpected preimage archive entry`。final-02 的原脚本、计划、输出和 INCOMPLETE 结果不改。

final-03 仅增加上述 symlink 条目的重建。绝对路径和 `..` 成分仍先拒绝；其他目录、链接目标、嵌套 hook 目录、hardlink 和非普通条目仍不接受。覆盖当前源码副本时只移除原有 symlink，再创建相同的相对链接；不会用链接覆盖普通文件，也不对链接 chmod。普通文件的原有恢复规则不变。没有 pax 特判。

`preimage-archive-check-03/run.json` 使用两个 runner 的真实 AST 解包块：旧块复现原异常；新块恢复同一实际归档的全部 26 个 symlink，普通文件字节和 mode 与 tar 一致；9 类非法条目仍拒绝。`evidence-only-guard-check-03/run.json` 另验证只能接受本票证据提交，混入产品、测试、别票证据或非后代提交均拒绝。这些只证明 runner，不作为产品绿态。

为按 #114 提交 runner 证据而保持产品版本不变，记录分为 `revision=5d0bf1e8` 与 `checkout_revision=证据提交号`。只有本票 evidence 目录的后续提交可跟随该产品；产品、hooks、tests、README 和 acceptance 必须与 5d0bf1e8 无差异，39 阶段内 checkout 也不得变化。原套件的 HEAD/验收文件检查绑定该证据 checkout，外层继续核对固定产品源码，未改套件断言。

执行命令：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-sandbox.sh rebase-final-03
```

新总报告为 `outside-rebase-final-03/run.json`，同名目录不得存在。仍完整执行原 39 个阶段，先修前 review 生命周期四条红态、候选四例，再执行 joint/冲突红绿、S3 25、8/9/18、CAS/cards、T-076-2 最终入口、relay、尾注候选证明、身份/停机/原生记录/panes。单文件超 5 MB 停止，任意未知失败停止，不重试或跳过。

准备归档和静态检查为 `rebase-final-03-preparation-01/`。局部解包检查命令为 `python3 -B evidence/2026-10-11-batch13/T-077/check-preimage-archive-03.py`，原 runner 拒绝的 archive 与临时输出路径、各项结论均在报告中留档；同名输出拒绝覆盖。真实模型新增 0；独立审查仍未启动。
