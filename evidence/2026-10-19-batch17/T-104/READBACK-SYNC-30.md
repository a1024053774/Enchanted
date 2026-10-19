# T-104 测试读回同步修复

状态：**INCOMPLETE**。主控 #30 已授权修改测试同步并先提交；代码修改与确定性重放检查通过，沙箱外提交和两次真实后台重跑仍待主控执行。产品代码、审查脚本及其已有原件未改。

起点：`45c127b5af03bfdc50802579bda50b88a98dc2c7`。task／attempt 仍为 T-104／a1，沿用已有 worker 启动绑定。只修改 `workbench/tests/test_t104_shell_e2e.py` 及本 worker 的小型诊断／同步证据；独立审查者的两个未受控交付文件保持原样，不由此脚本暂存。

## 根因与修正

真实红态见 `replay-diagnosis-28.json`：最后一次读回为 738 字节，pwd／LOGIN 已到，唯一环境行从第 738 字节开始，旧谓词先满足、精确断言随即对空列表失败。这是测试同步缺陷，不是产品多继承了变量。

现在在 env 管道之后用 printf 输出新的 UUID 完成标记；只在解析后的完整行集合中找到该标记才返回读回。随后显式核对 pwd、LOGIN、原 stdout marker，原来的 A2A_ 精确断言逐字保留。既不增加固定延时，也不放宽环境值的判定。

同一文件只有这一处等待 pwd／LOGIN 的读回点。另一处 `nonce in output_lines(first)` 等的是独立 nonce 的完整行，只证明指定输入已到 PTY；其后没有依赖尚未读到的尾部字段，未发现本次同类竞态，保持不变。其他 wait_for 等待后台恢复状态、进程树或进程退出，不是这类流式内容尾部读取。

## 反事实与局部验证

`CHECK-READINESS-30.py` 执行冻结旧版本与新版本的实际 output_lines、等待 lambda，以及同一条环境断言，不启动后台、PTY、Electron 或模型。期望来自主控的“env 完成后才断言”要求。

`readiness-check-30.json` 为 PASS：真实延迟前缀使旧谓词提前满足，新谓词仍等待；命令回显中的标记、不完整标记、尚无标记的完整旧 trace 均不结束读回；补齐完成行后通过原环境断言，额外 A2A_UNEXPECTED 仍被原断言拒绝。完整 trace 后补标记属于确定性解析重放，不冒称本轮新跑的 PTY。

复现局部检查（使用新输出文件）：

```sh
python3 evidence/2026-10-19-batch17/T-104/CHECK-READINESS-30.py /绝对路径/新同步检查.json
```

## 提交与连续两次真实运行

按主控要求先提交，主控在沙箱外运行：

```sh
bash evidence/2026-10-19-batch17/T-104/RUN-OUTSIDE-10-COMMIT-SYNC.sh
```

脚本核对唯一受控改动是该测试，并核对补丁与局部通过证据完全一致；`git add --sparse`，由现有钩子加 worker 尾注，不手写尾注、不 push。提交号尚待主控回传。

然后连续运行，分别使用新编号，不覆盖已有失败现场：

```sh
bash evidence/2026-10-19-batch17/T-104/RUN-OUTSIDE-01-BACKEND.sh sync-30-01
bash evidence/2026-10-19-batch17/T-104/RUN-OUTSIDE-01-BACKEND.sh sync-30-02
```

每次均运行完整后台套件，包括好候选、两个旧版本及三个变异、四项原回归，保留各次真实 stdout／事件／数据库与退出记录。依赖和缓存沿用现有方式，原始场景归档到外置盘，缺盘失败。未将两次尚未运行的结果写成 PASS，也不据两次运行就宣称普遍可靠性改善。
