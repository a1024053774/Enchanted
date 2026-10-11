# 工作台界面文档的覆盖登记待主控补充

观察：`.project-map/MAP.md:82` 的 workbench/README.md 当前仅覆盖 `workbench/src/**`、`workbench/hooks/**`。本卡新增 `workbench/app/**` 和 package.json 的构建／启动命令，README 已说明这些入口，但后续只修改 app 时，地图的 stale 检查无法提示 README 复核。

建议：执行主控在本卡交付后，将该行 Covers 补入 `workbench/app/**`、`workbench/package.json`；依据最终提交核对 README。worker 的边界禁止修改地图，因此本卡只上报，不代改。当前 status 为 0 problems、0 stale；这项登记工作不改变本卡产品或验收语义，不阻塞原生采集修复。
