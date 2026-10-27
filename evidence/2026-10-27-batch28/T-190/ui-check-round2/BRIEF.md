# T-190 / T-191 界面实操验收（Computer Use）

你是验收员，只用 Computer Use 操作应用 **Enchanted Test**（bundle id `org.a2a.workbench.test`，打包的隔离测试版，侧栏项目是 beta / epsilon / gamma）。不要操作用户自己的 Enchanted（bundle id `org.a2a.workbench`，项目名是 a2a、a1024053774.github.io 等）、浏览器或其他应用；不改任何文件，只把截图和报告写进 `/private/tmp/t190/ui-check/`。遇到系统授权、登录、付款弹窗就停下报告。

隔离数据：项目 beta（仓库在，有一个已认领未回收的任务 T-1）、gamma（仓库目录已被删，有已认领的 T-1）、epsilon（没有任务；原来的终端已结束）。先点侧栏 epsilon，再点右上“新建终端”，开一个运行中的普通终端，然后再做下面各项。

逐项做，每项截图（文件名用编号），记录看到了什么：

1. 侧栏总览：gamma 那一行是否显示“目录不存在”；epsilon 的普通终端状态图标是否静止（空闲），不是转圈。
2. 右键 epsilon →“从列表移除”：应出现对话框，说还有运行中的终端，要先关掉；只有“取消”。点取消。
3. 右键 beta →“从列表移除”：对话框应列出 T-1 和状态，并有“取消 / 保留并移除 / 回收并移除”。点“保留并移除”，beta 应从侧栏消失。
4. 右键 gamma →“从列表移除”→“保留并移除”：gamma 消失。
5. 点侧栏顶部“+”打开项目，选目录 `/private/tmp/t190/beta`：beta 应回到侧栏，T-1 仍在（点 beta 看任务格）。
6. 在 epsilon 的普通终端里输入 `opencode` 回车，等 10 秒：侧栏这一行应换成 opencode 图标、CLI 名 opencode，状态跟着 opencode 走；再在终端里按 Ctrl+C 两次退出 opencode，等 10 秒：图标消失，回到 zsh、空闲。若 opencode 要求登录或授权，停下记录，不要登录。
7. 浅色、深色各截一张侧栏（切换外观用窗口左上角的太阳图标，若有）。

最后输出报告 `/private/tmp/t190/ui-check/REPORT.md`：每项写 PASS / FAIL / BLOCKED 和依据（截图文件名），不要把没做的写成 PASS。最后一条回复也给出同样的结论。
