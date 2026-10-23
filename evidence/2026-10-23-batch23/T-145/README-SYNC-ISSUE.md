# T-145 范围外文档同步

状态：INCOMPLETE，非阻塞上报。

T-145 修改 `workbench/src/panes.ts` 的 `userInput`，让完整的终端协议上报仍写入 PTY，但不调用用户输入记录器，也不占用用户草稿。`project_map.py status --root .` 因此把 `workbench/README.md` 标为 stale。

位置：`workbench/README.md` 第 234 行只写了 agent 窗格输入、人工介入沿用原路径；任务卡允许范围未包含该文件，并禁止修改地图。worker 不自行扩大范围。

建议：执行主控集成时，在相应段落补充“终端鼠标、焦点和设备回复等完整协议上报原样发给 CLI，不记为用户输入或人工介入；真实键入与已有记录保持原样”，并复核 living doc 的 Verified。

复验命令：`python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .`。
