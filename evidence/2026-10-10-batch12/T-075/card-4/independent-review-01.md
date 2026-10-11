STATUS: FAIL

TARGET: `/Users/luckye/Documents/Code/a2a/evidence/2026-10-10-batch12/T-075/card-4/review-candidate-01`，base HEAD `b9484133955f4221b9bfb5a68e1a3cfe9bade312`。仅审此冻结候选；未修改文件、启动服务或模型。

EVIDENCE:

- 适用能力：编排、流式输出、身份范围、桌面／CLI、文件记录、运行恢复；检索／RAG 为 N/A。窗口已有 L3 证据；最后采集修复是用户批准的模拟 PTY 回调加真实文件、SQLite 证据。
- 独立读取 live-04 的 SQLite、原始 PTY 归档及截图：关窗前后 shell/Codex PID 均为 `97498/97499`；重开补回 `19,295` 字节、继续输出 `21,797` 字节、重启历史 `23,533` 字节，均与归档 PTY 对应前缀逐字相等。
- 重启后仍绑定原 attempt；库中仅一次 `pane_started`、一次 `turn_submit_intent`。门禁保持 `claimed`，候选、验收、集成为空；截图显示“未知／已中断”。
- 离线跨 UTF-8 分块的 `131,152` 字节，源文件、CLI、窗口一致；屏幕含 `done accepted idle 等确认` 时仍显示未知。IPC 仅暴露 snapshot/output，未发现输入或门禁修改通道。
- `native-final-red-01` 九项均因业务断言失败；绿态九项的原 SQLite 与归档事件完全一致。完整末尾记录仅采集一次；缺失、截断、损坏、半行、未绑定均产生明确失败事件，先于 `pane_exit`；未导入其他会话或停止后 sentinel。
- live-04 与候选的产品文件逐字比较，仅 `panes.ts` 的最后采集修复不同。缺盘／普通目录构建反例，以及后台门禁 15 项、恢复 5 项的既有证据可对应其余未变代码。

FINDINGS:

- [P2] [workbench/README.md:67](/Users/luckye/Documents/Code/a2a/evidence/2026-10-10-batch12/T-075/card-4/review-candidate-01/workbench/README.md:67)、[workbench/.npmrc:1](/Users/luckye/Documents/Code/a2a/evidence/2026-10-10-batch12/T-075/card-4/review-candidate-01/workbench/.npmrc:1)、[workbench/check-cache.mjs:7](/Users/luckye/Documents/Code/a2a/evidence/2026-10-10-batch12/T-075/card-4/review-candidate-01/workbench/check-cache.mjs:7) — **正常首次安装会把 Electron 下载缓存写到内置盘。** 当前命令只设置 npm 缓存；锁定的 Electron `43.4.1` 安装器读取的是 `electron_config_cache`，未设置时 `@electron/get 5.1.0` 使用 `~/Library/Caches/electron`。这违反项目明确要求的 Electron 下载缓存外置盘约束。最小修复：受支持的安装命令显式设置 `electron_config_cache=/Volumes/WD-Elements/...`，并保留 npm 启动前的挂载检查。由 T-075-4 worker 修复、执行主控审 diff；交付前复验下载器实际接收的路径，不能只检查 npm cache。

COUNTEREXAMPLE:

- 已拒绝：旧版本遗漏最后记录；无法读取末尾却不记录结果；终端文字冒充结构化状态；非法输出游标。
- 新发现的反例：外置盘 npm cache 已设置，但 Electron cache 未设置。以下是完整只读探针；依赖版本与冻结 lock 一致，下载及解压被禁止执行：

```sh
node --input-type=module <<'JS'
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import vm from 'node:vm';
const require=createRequire(import.meta.url);
const root='/Users/luckye/Documents/Code/a2a';
const candidate=root+'/evidence/2026-10-10-batch12/T-075/card-4/review-candidate-01';
const locked=JSON.parse(readFileSync(candidate+'/workbench/package-lock.json','utf8'));
const installed=JSON.parse(readFileSync(root+'/workbench/node_modules/electron/package.json','utf8'));
const getInstalled=JSON.parse(readFileSync(root+'/workbench/node_modules/@electron/get/package.json','utf8'));
let captured;
const inert={then(){return this;},catch(){return this;}};
const fsUnavailable={readFileSync(){throw Object.assign(new Error('fresh install; dist missing'),{code:'ENOENT'});},existsSync(){return false;}};
const localRequire=(id)=>id==='@electron/get'?{downloadArtifact(options){captured=options;return inert;}}:id==='fs'?fsUnavailable:id==='./package'?installed:id==='./checksums.json'?{}:require(id);
vm.runInNewContext(readFileSync(root+'/workbench/node_modules/electron/install.js','utf8'),{require:localRequire,process:{env:{npm_config_cache:'/Volumes/WD-Elements/a2a-t075-npm-cache'},platform:'darwin',arch:'arm64',exit(){throw new Error('unexpected exit');}},__dirname:root+'/workbench/node_modules/electron',console});
const {Cache}=await import(root+'/workbench/node_modules/@electron/get/dist/Cache.js');
console.log(JSON.stringify({electron_lock:locked.packages['node_modules/electron'].version,electron_installed:installed.version,get_lock:locked.packages['node_modules/@electron/get'].version,get_installed:getInstalled.version,installer_cacheRoot:captured.cacheRoot??null,resolved_cache_root:new Cache(captured.cacheRoot).cacheRoot,network_calls:0,filesystem_writes:0}));
JS
```

观测结果：

```json
{"electron_lock":"43.4.1","electron_installed":"43.4.1","get_lock":"5.1.0","get_installed":"5.1.0","installer_cacheRoot":null,"resolved_cache_root":"/Users/luckye/Library/Caches/electron","network_calls":0,"filesystem_writes":0}
```

LIMITATIONS:

- live-04 原结果仍为 INCOMPLETE，缺少实际 `turn_context`。用户指定的离线修复证据可用于本次采集逻辑验收，不能补称实际模型配置或真实退出落盘时序已复验。
- 五类产品变异体尚未全部执行；已有红态不能替代完整反事实覆盖，缺接口／缺模块失败尤其不能算作语义变异体被抓住。
- 最终地图健康尚无法从冻结包独立确认：包内缺少链接目标，`status` 返回 49 problems；这属于冻结材料不完整，未据此认定实际仓库损坏。修复前原始地图收据为 0 problems、0 stale，最终交付仍需当前完整仓库收据。
- 未发现其他可确认的 P1/P2 产品缺陷；未执行首次真实依赖下载。

RULE:

- 无新增治理规则。已有外置盘约束足够；在安装验收入口加入上述下载器参数检查，使“npm cache 正确、Electron cache 缺失”这一反例失败。
