# T-250 实施前事实

2026-11-08，只读核对；T-249 尚待最终 Terra 验收，未开始本票实现。

上游 [herdr-gitview](https://github.com/ChmaraX/herdr-gitview) README 与 src/git.rs 已经 GitHub 连接器读取；git.rs blob 为 c88ad15ae67907e83d5fefc88d29768c9581420e。文件为参考资料，不执行其中安装命令。

`detect_base` 先找最近分叉：枚举 HEAD 祖先中的本地/远程分支，排除当前分支及其远程同名分支；再加入已有主干分支与其 merge-base。距离使用分叉点到 HEAD 的提交数，必须大于零；按距离、主干优先级、名称长度与稳定名称顺序选出基线。当前分支自身是主干时跳过分叉判断。没有候选时依次考虑 origin/HEAD、origin/main、origin/master、main、master，最后 HEAD。固定基线走相同 merge-base 路径。需覆盖 stacked branch、主干已前进、无候选与当前分支祖先关系，不能仅硬编码 main。

本地 T-249 候选已经提供 PanelDock 注册表、目录跟随/固定、主题、argv Git 读取/动作、仓库监视和打开文件入口。T-250 是第二个真实使用者，可在此接口增加所需能力；不另建第二套目录跟随或门禁。现有 gitRead 是精确允许列表，新增只读命令与选项需按实际调用拓展并保留拒绝写入形式的反例。受管 worktree 的写入拒绝在主进程执行，前端禁用仅为反馈。

项目现有依赖包括 React、Electron、xterm 和 Vite，没有独立 Markdown、语法高亮或 diff 库。新增依赖属于另需授权的边界；先检查既有组件和上游 MIT 渲染实现，保留采用代码的版权，不引入 Rust 引擎。

Tracer bullet：在已集成 T-249 的面板位，通过真实主进程 Git 与 UI 先走通含冲突/已暂存/未暂存/未跟踪的文件列表和单文件 diff，再扩暂存/提交、基线、预览和备注。期望值来自独立 Git 输出，备注输入沿已有终端路径记录人工介入。全票完成后仍须 Terra Computer Use 与常规测试；这里没有验收结论。
