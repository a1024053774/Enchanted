# T-077 第一次合入 T-076-2：变基发起步骤

回应主控 #101。**INCOMPLETE**：当前 HEAD `863e8b8afe272530b3c5bddc130a2d684f2a9b85`，目标 main `7a1ecae84121b4dc43ddf79b595d6ff4917ab6c9`，共同基线 `457e02a8`。已核对受控文件没有未提交修改，r2/r3 未跟踪原始目录仍在，其完整压缩归档已提交；不删除原目录。

当前权限明确只允许写 worker worktree；共享 Git 元数据在 `/Users/luckye/Documents/Code/a2a/.git`，属于只读范围。未尝试写入或请求提权。请执行主控在沙箱外运行：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/rebase-main-01.sh
```

脚本固定当前分支/HEAD/目标 main，检查受控文件干净后执行唯一一次 rebase main；不 stash、reset、abort，不重试。若有冲突，保持 rebase 进行中，回传停止点后由本 worker 解决冲突，再由主控继续需要写共享元数据的步骤。

按 #101 保留双方意图：main 的 dispatch_intent 速度标签 default、质量串及原生记录归属、审查复用/重审；本卡的生命周期、R8 第四次停止与冲突回写。不能靠删除 T-076 行为让旧 T-077 测试通过。

变基尚未完成，因此第 2 步 rebase-final-01 不能先称就绪；将在冲突解决后的 HEAD 上准备。第 3 步 fresh-context 审查按主控要求等待单独指令，尚未 spawn agent 或启动任何模型。
