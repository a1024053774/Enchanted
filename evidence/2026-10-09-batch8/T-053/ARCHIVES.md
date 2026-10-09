# T-053 证据归档

- `raw-runs.tar.gz`：最初入口缺失红态、早期绿态、初始候选绿态和两轮 mutant 的完整原始目录。
- `independent-review-raw.tar.gz`：唯一 fresh-context 审查的独立临时目录，含冻结源码、9 项复跑、13 项探针、FAIL 的命令/输出/夹具。
- `review-correction-raw.tar.gz`：审查发现的红态、修复后 12 项绿态、独立探针重放、修复后两个 mutant 的完整目录。

归档保留 UTF-8 与故意构造的非 UTF-8 文件、未发布的 17 字节 tmp、symlink 和完整正文，不沿 symlink 读取。工作区内原始运行目录移到被现有 gitignore 覆盖的 `raw-artifacts/`，内容不删不改；原位置留下命令、结果和必要的可重放快照。记录内旧绝对路径对应归档中的原布局，解包到独立目录即可检查。

归档解包命令：

```sh
tar -xzf evidence/2026-10-09-batch8/T-053/review-correction-raw.tar.gz -C /tmp/T-053-unpack
```

先自行建立独立解包目录。完整重放命令在 RESULTS.md；不要向已有原始证据目录重放。
