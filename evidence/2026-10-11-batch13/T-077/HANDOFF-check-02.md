# T-077-1 R8 与剩余白名单红态交接（2026-10-11）

状态：**INCOMPLETE**。已独立读回 green-01：12 项全部通过、0 failures/errors；red-02：R8 上限的 2 个业务断言失败、0 errors。两批原始产物保持不变，真实回合仍为 0/4。

本轮改动：

- 从 verify 提取锁内的 `verifyCandidate`，显式验收与 R8 共用一条生产路径，不递归获取同一操作锁。
- G 已变化时，持久保存原 attempt 的失配计数，再执行新验收；最多三次自动重验，第 4 次失配暂停并上报。保留旧 verification 与用途引用，重复请求不能清零额度。
- Git 事务未成功 prepare、进程已明确非零退出、无 I/O 未知且引用已变化时，可以重验；不以 stderr 关键词判断。prepare 后的失败及中断恢复中的 pending intent 仍保持 `needs_reconciliation` 语义。
- 事件记录候选审查的完整身份绑定，作为 T-076-2 衔接信息；不是审查通过凭据，尚未证明真实 reviewer 沿用。
- 按 W01 改“一次基线变化立即拒收”的旧断言。W05/W07/W09/W11 仍未修改，先补它们各自的起点红态。

执行命令：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-sandbox.sh check-02
```

命令顺序：

1. `outside-green-02`：一次 G 变化自动重验，以及第 4 次失配停止/上报/持久计数/重复请求不再启动 oracle。候选预期 2 项全绿；出现失败则停止脚本，交回主控。
2. `outside-red-03`：从 red-01 归档重建起点，逐文件与 git show 起点核对后运行 5 项：加强后的计数/重放场景、缺尾注候选自动重验（W09）、旧 run 的旧目录清理（W05）、历史/当前/外来 attempt 隔离清理（W07）、实际 CAS 写入前竞争后的重验（W11）。每项预期业务红态，errors/skips 必须为 0。

冻结范围扩到原始 CLI/daemon/gates、受控线程 host 和 `acceptance/entry/`，避免把候选 daemon 配旧 core 当成“起点”。当前测试与生命周期适配器只负责夹具，命令实际进入冻结产品；每次 sources 归档、baseline-binding 和 daemon ready 记录可核对入口。

W07 的 focused 夹具给三个执行者声明不相交的文件范围，目的是在旧 CLI 不认识 overlap 参数时也能测试清理；不会替生产路径默认授予并行理由。原历史回收用例的三个理由调用点仍待 W13 单独接入。W05 先执行尚未修改的原“旧 run 不接管 replacement”场景，再追加清理要求，不替换其身份/引用/关闭对象断言。

实际写入前竞争的 Git 屏障只卡第一次 CAS，后续明确放行；oracle 控制同样明确释放，防止把夹具等不到第二次 release 当成产品失败。并发作者只修改 `/tmp` 夹具仓库，不动任何真实 checkout。

本轮未启动后台或真实 Codex；已完成 Node 语法/模块加载、Python AST/导入、Shell 语法检查。尚未跑完整 8/9/18、真实冲突场景、最终审查或变基。

已读取 main 的 `42e2b8ed3caed775133eb3cafff5f4ee5ab68330`：原生身份、尾注事实和停机改动目前尚未进入本分支。合流时保留 `runtime_identity`、关闭流程和测试 host 的新身份供应；不会用本分支旧代码覆盖它们。T-076-2 的质量串应接入 `verifyCandidate`，不另保留一套只给 R8 用的检查串。

后续顺序仍按主控 #31：检查通过并确认剩余红态后完成白名单迁移 → 8/9/18 回归 → 冲突流程的红/绿及真实场景 → 一次独立审查 → 最新 main 变基与重跑后交付。任何业务失败原样保留并交回，不改白名单之外的断言。
