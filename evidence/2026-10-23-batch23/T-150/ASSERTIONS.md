# T-150 修改前断言清单（2026-10-23）

INCOMPLETE：这是编辑前的清单，起点 `32ffb4e6dcc0472b20bbb64331a355621c9b73a9`。每个含 assert 的原始行均列出；同一行多条断言一起保留。表中的行号始终指起点版本。

目标：迁到现行契约，保留跨窗与凭据边界，在当前代码取得绿态及有效检查上的变异红态。非目标：产品代码、其他测试、HISTORICAL、地图。未知：迁移后的夹具是否完整表达现行导航；以规格与 ticket 固定期望后运行检验，不读当前输出作为答案。此任务为单一 VM 合同模块，无跨层 Tracer bullet 实现；沿用 Ubiquitous language，不新增 Deep modules 包装层。

契约来源：T-150 与授权收件箱；T-091 的独立 pane key/window identity/sequence；T-096 的布局恢复和空布局；T-107/T-109 的层级；T-110 的应用内通知；T-112 的配置透传；T-119 的未选择项目终端；T-132、T-134～137 的新页面；T-139 的项目/任务/agent 视图与结束只读；T-140 的额外目录。代码仅用来确定调用边界与变异位置（main.ts、preload.ts），不据运行输出生成期望。

原始执行：`node --experimental-vm-modules workbench/tests/test_t091_pane_ipc.mjs evidence/2026-10-23-batch23/T-150/baseline-01.json`，退出 1。预期原测试过时；实际停在旧 handler 名单，属测试契约缺陷红态，不是产品缺陷，也不替代后续保留检查上的变异红态。

| 原行 | 原断言/检查 | 判定、迁移与依据 |
| --- | --- | --- |
| 23 | `assert.ok(['legacy', 'picker', 'shell', 'panes', 'creation', 'sidebar', 'questions', 'flow', 'questions-flow'].includes(values.contract), 'Select an explicit known IPC contract');` | 过时：删除历史 contract 模式，默认只核对现行接口；T-150。 |
| 100 | `assert.equal(identity.kind, 'operator');` | 现行有效：保留夹具的身份、目录、有效凭据及 VM 外部边界检查；T-091/T-096/T-119。 |
| 117 | `assert.equal(identity.kind, 'operator');` | 现行有效：保留夹具的身份、目录、有效凭据及 VM 外部边界检查；T-091/T-096/T-119。 |
| 118 | `assert.ok(input.project === fixtureProject &#124;&#124; withPanes && input.project === null, 'Terminal project must come from the selected task or be unassigned');` | 现行有效：保留夹具的身份、目录、有效凭据及 VM 外部边界检查；T-091/T-096/T-119。 |
| 119 | `assert.equal(input.cwd, input.project === null ? (await import('node:os')).homedir() : '/fixture/project-repo', 'Terminal cwd must come from the selected directory source');` | 现行有效：保留夹具的身份、目录、有效凭据及 VM 外部边界检查；T-091/T-096/T-119。 |
| 131 | `assert.equal(identity.kind, 'operator', 'Layout persistence requires the operator identity');` | 现行有效：保留夹具的身份、目录、有效凭据及 VM 外部边界检查；T-091/T-096/T-119。 |
| 134 | `assert.ok(input.project === fixtureProject &#124;&#124; withPanes && input.project === null);` | 现行有效：保留夹具的身份、目录、有效凭据及 VM 外部边界检查；T-091/T-096/T-119。 |
| 147 | `assert.equal(identity.kind, 'operator');` | 现行有效：保留夹具的身份、目录、有效凭据及 VM 外部边界检查；T-091/T-096/T-119。 |
| 154 | `assert.ok(liveCredentials.has(identity?.window), 'Input/close must use a live pane credential');` | 现行有效：保留夹具的身份、目录、有效凭据及 VM 外部边界检查；T-091/T-096/T-119。 |
| 180 | `assert.equal(spec, 'electron');` | 现行有效：保留夹具的身份、目录、有效凭据及 VM 外部边界检查；T-091/T-096/T-119。 |
| 210 | `assert.equal(initialKeys.length, 1, 'Never-saved layout must still select the current worker');` | 限定语过时：只在显式 task 的从未保存布局验证 worker 回退；新增无选择启动为空；T-119/T-139。 |
| 211 | `assert.equal((await handlers.get('a2a:snapshot')({ sender: initial.webContents, senderFrame: initial.webContents.mainFrame }, initialKeys[0])).launch.id, 'worker');` | 保留 task 内 worker 回退；不再把它当全局启动默认；T-119/T-139。 |
| 212 | `assert.equal(layoutSaved, true, 'Initial default selection must be persisted');` | 保留显式 task 初次选择持久化；T-096。 |
| 223 | `assert.ok(rejected, 'Unregistered pane key was accepted');` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 227 | `assert.equal(first.pane_key, aKey); assert.equal(first.window_id, simultaneous.window_id); assert.equal(first.input_enabled, true);` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 228 | `assert.equal(requests.filter(row => row.command === 'window_open').length - credentialRequestsBeforeA, 1);` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 231 | `assert.equal(second.input_enabled, true, 'Nullable controller attempt must remain writable');` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 232 | `assert.notEqual(aKey, bKey); assert.notEqual(first.window_id, second.window_id);` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 233 | `assert.deepEqual([...registrations].sort(), [...expectedHandlers].sort(), 'IPC handler names must match the selected contract');` | 过时名单：按 T-119/T-132/T-134～137/T-140 补全接口；不从运行输出生成名单。 |
| 234 | `assert.equal(new Set(registrations).size, registrations.length, 'IPC handler registration must not repeat');` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 243 | `await assert.rejects(() => invoke(a, channel, bKey, ...trailing[channel]));` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 244 | `assert.equal(requests.length, beforeDenied, 'Cross-window pane key must not reach the transport');` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 248 | `await assert.rejects(() => Promise.resolve().then(() => handlers.get(channel)({ ...event(a), senderFrame: {} }, ...validArguments[channel])));` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 249 | `await assert.rejects(() => Promise.resolve().then(() => handlers.get(channel)({ sender: unknownSender, senderFrame: unknownSender.mainFrame }, ...validArguments[channel])));` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 250 | `assert.equal(requests.length, beforeDenied, 'Denied sender must not reach the transport');` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 252 | `assert.equal(requests.length, beforeDenied, 'Denied sender/key must not reach the transport');` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 255 | `assert.deepEqual(inputs.map(row => [row.target, row.input.data, row.input.sequence]), [['worker', 'A', 1], ['controller', 'B', 1]]);` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 256 | `assert.equal((await invoke(a, 'a2a:output', aKey, 0)).launch, 'worker');` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 257 | `assert.equal((await invoke(b, 'a2a:output', bKey, 0)).launch, 'controller');` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 259 | `assert.equal((await invoke(h, 'a2a:snapshot', key(h))).input_enabled, false);` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 263 | `assert.deepEqual(Object.keys(bridge).sort(), [...expectedBridge].sort(), 'Preload names must match the selected contract');` | 过时名单：同上，显式 main/preload 接口对应表。 |
| 264 | `assert.equal(bridge.paneKeys[0], aKey); assert.ok(Object.isFrozen(bridge.paneKeys));` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 265 | `assert.equal((await bridge.snapshot(aKey)).window_id, first.window_id);` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 266 | `await assert.rejects(() => bridge.snapshot(bKey));` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 269 | `await assert.rejects(() => bridge.answer(bKey, 'question-sentinel', ['独立答复']));` | 现行有效：保留参数校验、无副作用拒收及原样透传；T-108/T-112。 |
| 270 | `await assert.rejects(() => bridge.answer(aKey, '', ['独立答复']));` | 现行有效：保留参数校验、无副作用拒收及原样透传；T-108/T-112。 |
| 271 | `await assert.rejects(() => bridge.answer(aKey, 'question-sentinel', []));` | 现行有效：保留参数校验、无副作用拒收及原样透传；T-108/T-112。 |
| 272 | `assert.equal(requests.length, before, 'Denied answers must not reach the transport');` | 现行有效：保留参数校验、无副作用拒收及原样透传；T-108/T-112。 |
| 275 | `assert.equal(sent.command, 'window_answer'); assert.equal(sent.target, 'worker');` | 现行有效：保留参数校验、无副作用拒收及原样透传；T-108/T-112。 |
| 276 | `assert.deepEqual(sent.input.answers, ['独立答复']); assert.equal(sent.input.question, 'question-sentinel');` | 现行有效：保留参数校验、无副作用拒收及原样透传；T-108/T-112。 |
| 283 | `await assert.rejects(() => bridge.executionSettings(change));` | 现行有效：保留参数校验、无副作用拒收及原样透传；T-108/T-112。 |
| 284 | `assert.equal(requests.length, before, 'Invalid execution settings must not reach transport');` | 现行有效：保留参数校验、无副作用拒收及原样透传；T-108/T-112。 |
| 285 | `assert.equal((await bridge.executionSettings()).worker.effort, 'high');` | 现行有效：保留参数校验、无副作用拒收及原样透传；T-108/T-112。 |
| 287 | `assert.equal(saved.reviewer.model, 'custom-model-sentinel', 'Model selection must reach backend unchanged');` | 现行有效：保留参数校验、无副作用拒收及原样透传；T-108/T-112。 |
| 288 | `assert.equal(saved.reviewer.effort, 'ultra-sentinel', 'Effort selection must reach backend unchanged');` | 现行有效：保留参数校验、无副作用拒收及原样透传；T-108/T-112。 |
| 289 | `assert.equal(saved.reviewer.fast, true, 'Fast selection must reach backend unchanged');` | 现行有效：保留参数校验、无副作用拒收及原样透传；T-108/T-112。 |
| 290 | `assert.deepEqual(requests.at(-1).input, {command:'execution_settings_save', role:'reviewer', model:'custom-model-sentinel', effort:'ultra-sentinel', fast:true});` | 现行有效：保留参数校验、无副作用拒收及原样透传；T-108/T-112。 |
| 296 | `assert.deepEqual(JSON.parse(JSON.stringify(flow)), {lanes:[{task:'T-flow-sentinel',title:'随输入变化',stage:'review'}],unassigned:[{id:'orphan-sentinel'}]}, 'Flow must preserve daemon facts');` | 现行有效：保留只读流程、层级事实透传及不发凭据；T-107/T-109/T-111。 |
| 297 | `assert.deepEqual(requests.slice(beforeFlow).map(row=>row.input), [{command:'flow_snapshot'}], 'Flow must use only the read command');` | 现行有效：保留只读流程、层级事实透传及不发凭据；T-107/T-109/T-111。 |
| 298 | `assert.equal(credentialNumber, beforeFlowCredentials, 'Flow must not issue pane credentials');` | 现行有效：保留只读流程、层级事实透传及不发凭据；T-107/T-109/T-111。 |
| 301 | `assert.equal(hierarchy.find(row => row.id === 'worker').parent, 'controller');` | 现行有效：保留只读流程、层级事实透传及不发凭据；T-107/T-109/T-111。 |
| 302 | `assert.equal(hierarchy.find(row => row.id === 'controller').parent, 'ideation');` | 现行有效：保留只读流程、层级事实透传及不发凭据；T-107/T-109/T-111。 |
| 303 | `assert.equal(hierarchy.find(row => row.id === 'ideation').descendants.count, 2);` | 现行有效：保留只读流程、层级事实透传及不发凭据；T-107/T-109/T-111。 |
| 304 | `assert.equal(hierarchy.find(row => row.id === 'controller').descendants.state, 'waiting_user_answer');` | 现行有效：保留只读流程、层级事实透传及不发凭据；T-107/T-109/T-111。 |
| 305 | `assert.equal(hierarchy.find(row => row.id === 'controller').descendants.counts[0].label, '等待用户回答');` | 现行有效：保留只读流程、层级事实透传及不发凭据；T-107/T-109/T-111。 |
| 306 | `await assert.rejects(() => bridge.selectAgent('absent'));` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 307 | `await assert.rejects(() => bridge.selectAgent('../invalid'));` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 308 | `await assert.rejects(() => bridge.notificationSetting('yes'));` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 312 | `assert.equal(focused.focusKey, aKey);` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 314 | `assert.notEqual(readonly.focusKey, aKey);` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 315 | `assert.equal((await bridge.snapshot(readonly.focusKey)).input_enabled, false);` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 316 | `await assert.rejects(() => bridge.input(readonly.focusKey, 'no credential'));` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 317 | `assert.equal(credentialNumber, before, 'Sidebar inspection must not grant input');` | 过时：只读 reviewer/ended 不得签发；当前 running worker 可复用已有凭据；T-139。 |
| 318 | `await assert.rejects(() => bridge.selectAgent('foreign'), /mismatch/);` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 319 | `assert.equal((await bridge.selection()).task.task_id, originalSelection.task.task_id);` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 321 | `assert.equal((await bridge.snapshot(controllerView.focusKey)).input_enabled, false, 'Transient controller view must not issue an input credential');` | 过时：运行中主控可写；此处改为 ended 主控只读；T-139/T-146。 |
| 322 | `assert.equal(credentialNumber, before, 'Transient view cannot acquire credentials');` | 改为 ended 主控不签发凭据；T-139/T-146。 |
| 326 | `assert.equal(requests.filter(row => row.command === 'pane_layout_close').length, removals, 'Transient close must not change saved layout');` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 327 | `assert.equal(await bridge.notificationSetting(), true);` | 现行有效：保留通知、去重、开关、Dock 与断连不重试；T-110。 |
| 330 | `assert.equal(notice.notices?.length, 1, 'Only entering waiting-user emits one notification');` | 现行有效：保留通知、去重、开关、Dock 与断连不重试；T-110。 |
| 331 | `assert.equal(notice.notices[0].id, 'question-one');` | 现行有效：保留通知、去重、开关、Dock 与断连不重试；T-110。 |
| 332 | `assert.equal(notice.notices[0].launch, 'worker');` | 现行有效：保留通知、去重、开关、Dock 与断连不重试；T-110。 |
| 333 | `assert.equal((await bridge.sidebar()).notices.length, 1, 'Repeated reads keep a single notification');` | 现行有效：保留通知、去重、开关、Dock 与断连不重试；T-110。 |
| 334 | `assert.equal(notificationCalls.length, 0, 'System notification API must never be called');` | 现行有效：保留通知、去重、开关、Dock 与断连不重试；T-110。 |
| 335 | `assert.equal(badgeCalls.at(-1), 1, 'Background Dock badge counts pending user questions');` | 现行有效：保留通知、去重、开关、Dock 与断连不重试；T-110。 |
| 337 | `assert.equal(badgeCalls.at(-1), 0, 'Foreground clears Dock badge');` | 现行有效：保留通知、去重、开关、Dock 与断连不重试；T-110。 |
| 339 | `assert.equal(badgeCalls.at(-1), 1, 'Background restores Dock count');` | 现行有效：保留通知、去重、开关、Dock 与断连不重试；T-110。 |
| 340 | `assert.equal(await bridge.notificationSetting(false, 'dockBadges'), false);` | 现行有效：保留通知、去重、开关、Dock 与断连不重试；T-110。 |
| 341 | `assert.equal(badgeCalls.at(-1), 0, 'Dock setting clears badge immediately');` | 现行有效：保留通知、去重、开关、Dock 与断连不重试；T-110。 |
| 343 | `assert.equal(badgeCalls.at(-1), 1);` | 现行有效：保留通知、去重、开关、Dock 与断连不重试；T-110。 |
| 346 | `assert.equal((await bridge.sidebar()).notices.length, 0, 'Other states do not notify');` | 现行有效：保留通知、去重、开关、Dock 与断连不重试；T-110。 |
| 347 | `assert.equal(badgeCalls.at(-1), 0);` | 现行有效：保留通知、去重、开关、Dock 与断连不重试；T-110。 |
| 350 | `assert.equal((await bridge.sidebar()).notices.length, 0, 'The same question never notifies twice');` | 现行有效：保留通知、去重、开关、Dock 与断连不重试；T-110。 |
| 352 | `assert.equal((await bridge.sidebar()).notices.length, 1, 'A different question while waiting notifies once');` | 现行有效：保留通知、去重、开关、Dock 与断连不重试；T-110。 |
| 353 | `assert.equal(await bridge.notificationSetting(false), false);` | 现行有效：保留通知、去重、开关、Dock 与断连不重试；T-110。 |
| 354 | `assert.equal((await bridge.sidebar()).notices.length, 0, 'Disabled notifications stay silent');` | 现行有效：保留通知、去重、开关、Dock 与断连不重试；T-110。 |
| 358 | `assert.equal((await bridge.sidebar()).notices.length, 0, 'Enabling while already waiting is not a new question');` | 现行有效：保留通知、去重、开关、Dock 与断连不重试；T-110。 |
| 360 | `assert.equal((await bridge.sidebar()).notices.length, 0, 'Missing question identity cannot notify');` | 现行有效：保留通知、去重、开关、Dock 与断连不重试；T-110。 |
| 362 | `assert.equal((await bridge.sidebar()).notices.length, 1);` | 现行有效：保留通知、去重、开关、Dock 与断连不重试；T-110。 |
| 363 | `await assert.rejects(() => bridge.notificationSetting(true, 'foreign'));` | 现行有效：保留通知、去重、开关、Dock 与断连不重试；T-110。 |
| 364 | `await assert.rejects(() => bridge.notificationSetting('yes', 'dockBadges'));` | 现行有效：保留通知、去重、开关、Dock 与断连不重试；T-110。 |
| 367 | `assert.equal((await bridge.sidebar()).notices.length, 1);` | 现行有效：保留通知、去重、开关、Dock 与断连不重试；T-110。 |
| 368 | `assert.equal(badgeCalls.at(-1), 1, 'Disconnect probe starts with a trusted pending question');` | 现行有效：保留通知、去重、开关、Dock 与断连不重试；T-110。 |
| 371 | `if (failure === 'transport') await assert.rejects(() => bridge.sidebar(), error => error === disconnectedError,` | 现行有效：保留通知、去重、开关、Dock 与断连不重试；T-110。 |
| 373 | `else await assert.rejects(() => bridge.sidebar(), /t110-sidebar-unavailable/);` | 现行有效：保留通知、去重、开关、Dock 与断连不重试；T-110。 |
| 374 | `assert.equal(requests.length, beforeFailure + 1, 'A failed sidebar read must not retry');` | 现行有效：保留通知、去重、开关、Dock 与断连不重试；T-110。 |
| 375 | `assert.equal(badgeCalls.at(-1), 0, 'Disconnected unknown state must clear Dock badge');` | 现行有效：保留通知、去重、开关、Dock 与断连不重试；T-110。 |
| 377 | `assert.equal(badgeCalls.at(-1), 0, 'Focus changes must not restore an untrusted count');` | 现行有效：保留通知、去重、开关、Dock 与断连不重试；T-110。 |
| 379 | `assert.equal((await bridge.sidebar()).notices.length, 0, 'Reconnect preserves question deduplication');` | 现行有效：保留通知、去重、开关、Dock 与断连不重试；T-110。 |
| 380 | `assert.equal(badgeCalls.at(-1), 1, 'A fresh verified read may restore the pending count');` | 现行有效：保留通知、去重、开关、Dock 与断连不重试；T-110。 |
| 381 | `assert.equal((await invoke(b, 'a2a:sidebar')).notices.length, 0, 'Sibling window shares the invalidated notice state');` | 现行有效：保留通知、去重、开关、Dock 与断连不重试；T-110。 |
| 390 | `assert.ok(bindingCommands.every(row => row.window === first.window_id));` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 394 | `assert.ok(openingResolve);` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 396 | `await assert.rejects(() => invoke(opening, 'a2a:input', key(opening), 'late'));` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 397 | `assert.equal(opening.destroyed, false, 'Closing must wait for the admitted identity request');` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 400 | `assert.equal(opening.destroyed, true);` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 401 | `assert.ok(![...liveCredentials.values()].includes('opening'), 'Late identity must be revoked');` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 404 | `assert.ok(a.destroyed); assert.equal(handlers.size, expectedHandlers.length);` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 405 | `if (withRecovery) assert.ok(layout.has('worker'), 'Closing the application view must preserve the open pane set');` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 407 | `assert.equal(requests.at(-1).target, 'controller');` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 410 | `assert.equal(threeKeys.length, 3, 'Three selected launches must create three pane keys in one window');` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 412 | `assert.deepEqual(threeSnapshots.map(value => value.launch.id), ['ideation', 'controller', 'worker']);` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 413 | `assert.equal(new Set(threeSnapshots.map(value => value.window_id)).size, 3);` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 416 | `assert.equal((await invoke(three, 'a2a:output', paneKey, 0)).launch, threeSnapshots[index].launch.id);` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 418 | `assert.deepEqual(requests.filter(row => row.command === 'window_input').slice(-3).map(row => row.input.sequence), [1, 1, 1]);` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 423 | `assert.deepEqual(declarations.map(row => [row.window, row.input.declaration.window_id, row.input.declaration.launch]),` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 425 | `assert.equal(registrations.length, expectedHandlers.length, 'Adding panes must not register more IPC handlers');` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 428 | `await assert.rejects(() => run({ ...options, launch: ['ideation', 'controller', launch] }));` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 429 | `assert.equal(windowNumber, beforeWindows, 'Invalid third pane must not create a window');` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 430 | `assert.equal(credentialNumber, beforeCredentials, 'Invalid third pane must not receive a credential');` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 432 | `await assert.rejects(() => run({ ...options, launch: ['worker', 'worker'] }));` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 438 | `assert.ok(index >= 0, 'Reviewer must coexist with other agent panes');` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 439 | `assert.equal(results[index].input_enabled, false, 'Reviewer pane must remain read-only');` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 441 | `assert.equal((await invoke(reviewed, 'a2a:selection')).names[reviewKeys[index]], '独立审查');` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 446 | `assert.equal(layout.has('ideation'), false, 'Explicit pane close must persist removal');` | 现行有效：保留移除、顺序、恢复失败只读、空布局和显式重开；T-096。 |
| 447 | `assert.ok(liveCredentials.has(sibling), 'Closing one pane keeps its sibling credential');` | 现行有效：保留移除、顺序、恢复失败只读、空布局和显式重开；T-096。 |
| 448 | `await assert.rejects(() => invoke(three, 'a2a:snapshot', threeKeys[0]));` | 现行有效：保留移除、顺序、恢复失败只读、空布局和显式重开；T-096。 |
| 455 | `assert.deepEqual(snapshots.map(value => value.launch.id), ['controller', 'worker'], 'Saved positions survive reload without explicit launch arguments');` | 现行有效：保留移除、顺序、恢复失败只读、空布局和显式重开；T-096。 |
| 456 | `assert.equal(snapshots[0].input_enabled, true); assert.equal(snapshots[1].input_enabled, false);` | 现行有效：保留移除、顺序、恢复失败只读、空布局和显式重开；T-096。 |
| 457 | `assert.equal(snapshots[1].window_id, undefined, 'Unrestored worker gets no input credential');` | 现行有效：保留移除、顺序、恢复失败只读、空布局和显式重开；T-096。 |
| 459 | `assert.equal(layout.size, 0);` | 现行有效：保留移除、顺序、恢复失败只读、空布局和显式重开；T-096。 |
| 464 | `assert.equal(layout.size, 0, 'All explicit pane closes persisted an empty set');` | 现行有效：保留移除、顺序、恢复失败只读、空布局和显式重开；T-096。 |
| 473 | `assert.equal(layout.size, 0, 'Explicitly closed final pane must stay absent when app reopens');` | 现行有效：保留移除、顺序、恢复失败只读、空布局和显式重开；T-096。 |
| 474 | `assert.equal(emptyKeys.length, 0, 'Saved empty layout must create no pane keys');` | 现行有效：保留移除、顺序、恢复失败只读、空布局和显式重开；T-096。 |
| 478 | `assert.deepEqual(Object.keys(bridge).sort(), [...expectedBridge].sort(), 'Empty preload keeps the complete interface');` | 现行有效：保留移除、顺序、恢复失败只读、空布局和显式重开；T-096。 |
| 479 | `assert.equal(bridge.paneKeys.length, 0, 'Preload must expose the saved empty pane set');` | 现行有效：保留移除、顺序、恢复失败只读、空布局和显式重开；T-096。 |
| 482 | `assert.ok(reopened.destroyed, 'Empty window can close normally');` | 现行有效：保留移除、顺序、恢复失败只读、空布局和显式重开；T-096。 |
| 485 | `assert.deepEqual(requests.slice(beforeReopen).map(row => row.input), [` | 过时：任务视图不再读项目终端布局；两次只读 task snapshot/layout；T-139。 |
| 492 | `assert.deepEqual(requests.slice(beforeReopen).map(row => row.input), [` | 删除旧 contract 分支，合并到同一 task snapshot/layout 检查；T-139。 |
| 496 | `} else assert.ok(requests.slice(beforeReopen).every(row => row.command === 'pane_layout'), 'Empty reopen must not select a worker or issue input credentials');` | 删除旧 legacy 分支；改为统一精确读请求检查；T-139。 |
| 497 | `await assert.rejects(() => run({ ...options, launch: [] }), /Distinct nonempty pane launches/);` | 现行有效：保留移除、顺序、恢复失败只读、空布局和显式重开；T-096。 |
| 500 | `assert.deepEqual([...layout.keys()], ['worker'], 'Explicit selection may reopen a closed pane');` | 现行有效：保留移除、顺序、恢复失败只读、空布局和显式重开；T-096。 |
| 509 | `await assert.doesNotReject(async () => { projects = await bridge.projects(); }, 'Projects must work without a pane key');` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 510 | `assert.deepEqual(JSON.parse(JSON.stringify(projects)), [{ project_id: fixtureProject }]);` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 511 | `assert.deepEqual(JSON.parse(JSON.stringify(await bridge.tasks(fixtureProject))), [fixtureSummary]);` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 512 | `assert.deepEqual(JSON.parse(JSON.stringify(await bridge.tasks('absent-project'))), []);` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 513 | `await assert.rejects(() => bridge.tasks('../invalid'), /invalid_id/);` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 514 | `assert.deepEqual(requests.slice(beforeCatalog).map(row => row.input), [` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 520 | `assert.deepEqual(JSON.parse(JSON.stringify(selected.task)), fixtureTask);` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 521 | `assert.deepEqual([...selected.paneKeys], [key(catalog)]);` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 522 | `assert.equal(requests.length, beforeSelection, 'Reading selection must stay local to this window');` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 524 | `assert.equal(cleared.task, null); assert.equal(cleared.paneKeys.length, 0);` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 525 | `assert.equal((await bridge.selection()).task, null);` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 527 | `assert.deepEqual(JSON.parse(JSON.stringify(restored.task)), fixtureTask);` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 528 | `assert.equal(restored.paneKeys.length, 1);` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 529 | `await assert.rejects(() => bridge.selectTask('absent-task'), /unknown_task/);` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 530 | `await assert.rejects(() => bridge.selectTask(''), /Invalid task/);` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 531 | `assert.deepEqual([...(await bridge.selection()).paneKeys], [...restored.paneKeys], 'Rejected task must preserve this window selection');` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 532 | `assert.equal(credentialNumber, beforeCredentials, 'Window catalog calls must not issue pane input credentials');` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 533 | `assert.equal(registrations.length, expectedHandlers.length);` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 540 | `assert.equal((await bridge.snapshot(freeKey)).launch.project, null);` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 543 | `await assert.rejects(() => bridge.newTerminal(), /请先选择任务/);` | 过时且非默认分支：无任务可新建未归属终端，保留正例；T-119。 |
| 544 | `assert.equal(requests.length, beforeNoTask, 'No task must not create a terminal');` | 同上，替换为无选择终端正例；T-119。 |
| 548 | `await assert.rejects(() => bridge.newTerminal(), /Task view is changing/);` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 550 | `assert.equal(created.paneKeys.length, selectedAgain.paneKeys.length + 1, 'New terminal must add one pane');` | 过时：从任务新建终端切到项目终端视图，只显示新终端；T-139。 |
| 553 | `assert.equal(shell.launch.role, 'shell'); assert.equal(shell.task, null); assert.equal(shell.input_enabled, true);` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 555 | `assert.equal(requests.at(-1).target, shell.launch.id);` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 556 | `assert.equal(requests.at(-1).input.sequence, 1);` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 560 | `await assert.rejects(() => bridge.snapshot(shellKey), /Shell project or launch mismatch/);` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 561 | `assert.equal(credentialNumber, beforeWrongProject, 'Foreign shell cannot issue a credential');` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 564 | `assert.equal(shellLayout.size, 0, 'Explicit shell close must remove its project layout');` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 565 | `await assert.rejects(() => bridge.input(shellKey, 'closed-shell'));` | 现行有效：保留原行为与独立哨兵；跨窗/全接口 sender、凭据、输出、序号、竞争/布局边界；T-091/T-096/T-107/T-139。 |
| 578 | `failedForContract = error instanceof assert.AssertionError && error.message === 'Unregistered pane key was accepted';` | 历史反例迁为当前代码 no-key 变异，仍须命中未注册 key 断言；T-150。 |
| 581 | `assert.ok(failedForContract, 'Known-bad must fail the pane-key admission assertion');` | 同上。 |
| 586 | `missingPanes = error instanceof assert.AssertionError && error.message.startsWith('Three selected launches must create three pane keys in one window');` | 历史单窗格反例迁为当前代码单窗格变异；T-091/T-150。 |
| 589 | `assert.ok(missingPanes, 'Single-pane tracer must fail the simultaneous pane-count assertion');` | 同上。 |
| 594 | `catch (error) { report.sidebar_known_bad = { revision, rejected: error instanceof assert.AssertionError && error.message.startsWith('IPC handler names must match'), error: String(error) }; }` | 仅旧名单历史红态：由当前全接口 sender/key 变异守护；T-150。 |
| 595 | `assert.equal(report.sidebar_known_bad?.rejected, true, 'Baseline must fail the new sidebar contract');` | 同上。 |
| 605 | `assert.notEqual(mutant, candidate);` | 现行有效：保留变异定位与聚焦断言（命令行可单独运行）；T-150。 |
| 607 | `catch (error) { report.close_mutant = { rejected: error instanceof assert.AssertionError && error.message.startsWith('Explicit pane close must persist removal'), error: String(error) }; }` | 现行有效：保留变异定位与聚焦断言（命令行可单独运行）；T-150。 |
| 608 | `assert.equal(report.close_mutant?.rejected, true, 'Close-without-removal mutant must fail the saved-layout assertion');` | 现行有效：保留变异定位与聚焦断言（命令行可单独运行）；T-150。 |
| 611 | `catch (error) { report.empty_layout_known_bad = { revision: emptyBadRevision, rejected: error instanceof assert.AssertionError && error.message.startsWith('Explicitly closed final pane must stay absent when app reopens'), error: String(error) }; }` | 历史空布局反例迁为当前代码空布局重开 worker 变异；T-096/T-150。 |
| 612 | `assert.equal(report.empty_layout_known_bad?.rejected, true, 'Previous frozen candidate must fail the explicit empty-layout contract');` | 同上。 |
| 616 | `assert.notEqual(windowMutant, candidate, 'Window-level pane-key mutation must change the selected implementation');` | 现行有效：保留变异定位与聚焦断言（命令行可单独运行）；T-150。 |
| 618 | `catch (error) { report.window_key_mutant = { rejected: error instanceof assert.AssertionError && error.message.includes('Projects must work without a pane key'), error: String(error) }; }` | 现行有效：保留变异定位与聚焦断言（命令行可单独运行）；T-150。 |
| 619 | `assert.equal(report.window_key_mutant?.rejected, true, 'A window list handler requiring a pane key must fail its no-key contract');` | 现行有效：保留变异定位与聚焦断言（命令行可单独运行）；T-150。 |
| 626 | `assert.notEqual(mutantSource, candidate);` | 保留通知变异；旧 transient 改为 ended 只读变异；T-110/T-139。 |
| 629 | `catch (error) { rejected = error instanceof assert.AssertionError && error.message.startsWith(expected); report[name + '_mutant'] = { rejected, error: String(error) }; }` | 同上。 |
| 630 | `assert.equal(rejected, true, name + ' mutant must fail its focused assertion');` | 同上。 |
