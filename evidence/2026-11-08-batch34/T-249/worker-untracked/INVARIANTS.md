# T-249 限定修复：验收与失败方式（实现前）

小目标：Git 图点击未跟踪普通文本，显示该文件的内容 diff；有 HEAD 和 unborn 都成立。
非目标：T-250、列宽实现调整、暂存、改索引/refs/对象库、公开 API、新依赖、门禁或构建脚本变化。
Tracer bullet：原始文件 → gitRead 主进程 → CommitDetails diff → 文件与独立 Git oracle。
Deep modules：复用既有 gitRead、diffArgs、diffRows，不增加平行读取接口。
Ubiquitous language：未跟踪文件、diff。

失败方式与检测：
- 有 HEAD/unborn 被当成 tracked diff 而丢内容；原 C 的 diffArgs 加上文件状态后仍返回空 diff，内容断言应失败。
- 同目录另一个文件混入；随机内容与独立 Git 全文核对，覆盖 *、[、:(、以 - 开头及单个 -。
- 空文件或二进制被伪装成文本；核对无 hunk 及 Git 原始二进制提示，空文件明确提示。
- 选别的文件/提交或关闭后旧请求覆盖新选择；窗口检查连续切换，并对延迟旧请求使用独立调度探针。
- no-index 扩大只读边界；仅允许精确参数、/dev/null 与仓库内普通文件，拒绝输出选项/缩写、目录、越界、符号链接与 Git 元数据。
- 所有读取前后，核对 rev-parse 返回的真实 git-dir/common-dir 的文件路径及原始字节；不算哈希。
- 列宽拖动或双击未接线；真实 CDP Input 鼠标事件操作可见分隔条，测量前后几何宽度；禁用处理 mutant 必须命中业务断言。

旧 C 内容业务红态必须先于产品修复。Electron/后台由主控在沙箱外运行；worker 不调用 ps，不启动这些进程。
冻结 acceptance/T-249/check_git_graph.py、REVIEW.md 与任务票不变。主控负责新的限定独立审查、标准 Test 包、Terra Computer Use、集成安装。
