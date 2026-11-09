// T-265 contract: real createReview + dispatch, real filesystem; only native
// process creation and terminal draining are replaced. No CLI/sandbox claim here.
// Failure modes: inline long OR short materials; truncated Unicode/verification;
// cross-review reuse; overwrite; partial write dispatched; missing role/agy command;
// changed candidate identity, checkout read-only handling, or result protocol.
import assert from 'node:assert/strict';
import test from 'node:test';
import fs from 'node:fs';
import { join, resolve } from 'node:path';
import { randomUUID } from 'node:crypto';
import { registerHooks, syncBuiltinESMExports } from 'node:module';

// Run the same behavioral assertions against small known-bad implementations.
// This loader never writes production files and every replacement must match once.
const mutants = {
  'inline-again': ['await this.dispatch(pane, `审查材料已保存', 'await this.dispatch(pane, `${pane.record.role_text}\\n\\n${prompt}\\n审查材料已保存'],
  'truncate-materials': ['`${pane.record.role_text}\\n\\n${prompt}`, { encoding:', '`${pane.record.role_text}\\n\\n${prompt}`.slice(0, 1024), { encoding:'],
  'overwrite-materials': ['{ encoding: "utf8", flag: "wx", mode: 0o600 }', '{ encoding: "utf8", flag: "w", mode: 0o600 }'],
  'omit-agy-command': ['if (pane.record.cli === "agy") {', 'if (false) {'],
};
if (process.env.T265_MUTANT) {
  const mutation = mutants[process.env.T265_MUTANT];
  assert.ok(mutation, 'unknown mutant');
  registerHooks({ load(url, context, nextLoad) {
    const result = nextLoad(url, context);
    if (url.endsWith('/src/panes.ts')) {
      const source = String(result.source), [before, after] = mutation;
      assert.equal(source.split(before).length, 2, 'mutant must change exactly one site');
      return { ...result, source: source.replace(before, after) };
    }
    return result;
  } });
}
const { Panes } = await import('../src/panes.ts');
const { saveReviewResult, readReviewResult } = await import('../src/reviewResult.ts');
const fixtureBase = process.env.A2A_REQUEST_DIR || resolve('evidence/2026-11-09-batch35/T-265/worker');
fs.mkdirSync(fixtureBase, { recursive: true });

function harness(t, { cli = 'Codex', role = `角色指令-${randomUUID()}：只读审查，使用 review_submit。` } = {}) {
  const root = fs.mkdtempSync(join(fixtureBase, 't265-materials-'));
  t.after(() => {
    // createReview makes this fixture checkout read-only for agy/opencode.
    fs.chmodSync(join(root, 'review'), 0o700);
    fs.rmSync(root, { recursive: true, force: true });
  });
  const requests = join(root, '请求 目录'); fs.mkdirSync(requests);
  const workspace = join(root, 'review'); fs.mkdirSync(workspace);
  const readonlyFile = join(workspace, 'sentinel.txt'); fs.writeFileSync(readonlyFile, 'read only');
  const copy = join(root, 'candidate'); fs.mkdirSync(copy);
  const review = { review_id: randomUUID(), session_id: randomUUID(), thread_id: randomUUID(),
    candidate_workspace: copy, workspace, candidate_commit: 'b'.repeat(40),
    attempt: { attempt_id: randomUUID(), session_id: 'worker-session', thread_id: 'worker-thread',
      workspace: 'worker-workspace', fence: 4, spec_rev: 7, runtime_identity: { launch: 'worker-launch' }, extra_directories: [] } };
  const template = { schema: 1, command: 'review_submit', request_id: 'review-' + review.review_id, task: 'project+T-265',
    attempt: review.attempt.attempt_id, session: review.session_id, fence: 4, spec_rev: 7,
    review_id: review.review_id, candidate_commit: review.candidate_commit,
    review_requirements: { completion_conditions_sufficiency: true,
      mutation_checks: { min: 2, max: 5, workspace: copy, report_section: '完成条件与变异检查' } } };
  const pane = { record: { id: randomUUID(), role: 'reviewer', cli, role_text: role, request_dir: requests },
    reports: ['agy', 'opencode'].includes(cli), queue: [], failed: null, stopped: false };
  const sent = [], launches = [];
  const host = {
    config: { reviewer_role_card: 'reviewer.md', reviewer_role_card_revision: 'fixture-revision' },
    async createPane(...args) { launches.push(args); }, get: id => { assert.equal(id, review.thread_id); return pane; },
    launchRecord: id => { assert.equal(id, 'worker-launch'); return { model_requested: 'worker-model', effort_requested: 'high' }; },
    store: { register: (launch, text) => ({ launch, text }), event() {} }, parentLaunch: { getStore() {} },
    dispatch: Panes.prototype.dispatch,
    async drain(p) { for (const item of p.queue.splice(0)) sent.push(item); },
  };
  const task = { card: { executor: { cli } } };
  return { root, requests, readonlyFile, copy, review, template, pane, sent, launches, role,
    run: prompt => Panes.prototype.createReview.call(host, task, review, prompt, template) };
}

function materialFromEntry(h) {
  assert.equal(h.sent.length, 1, 'one review entry dispatched');
  const entry = h.sent[0].text;
  assert.ok(entry.length < 4096, `native review entry must be short, got ${entry.length} characters`);
  assert.ok(!entry.includes(h.role), 'short materials must not retain an inline path either');
  const files = fs.readdirSync(h.requests).filter(name => name !== 'review-template.json');
  assert.equal(files.length, 1, 'one complete material file per launch');
  const path = join(h.requests, files[0]);
  assert.ok(entry.includes(path), 'entry points to this launch material');
  assert.match(entry, /先.*读/);
  assert.match(entry, /完整/);
  assert.equal(fs.statSync(path).mode & 0o777, 0o600, 'private material file');
  return { path, bytes: fs.readFileSync(path), entry };
}

test('long diff AND verification stay complete while native entry stays short', async t => {
  const h = harness(t);
  const prompt = `任务卡：${randomUUID()}\n候选改动：\n${'diff 中文🧭 e\u0301\r\n'.repeat(55000)}\n机械验收：\n${'verification 长结果\n'.repeat(50000)}\n上一轮问题清单：${randomUUID()}\n提交结论：review_submit\nEND-${randomUUID()}`;
  assert.ok(prompt.length > 1048576, 'fixture reproduces native limit');
  await h.run(prompt);
  const material = materialFromEntry(h);
  assert.equal(Buffer.compare(material.bytes, Buffer.from(`${h.role}\n\n${prompt}`, 'utf8')), 0, 'all input bytes preserved');
  assert.ok(!material.entry.includes('verification 长结果'), 'verification must not remain inline');
  assert.deepEqual(JSON.parse(fs.readFileSync(join(h.requests, 'review-template.json'), 'utf8')), h.template);
  const [, attempt, , review] = h.launches[0];
  assert.equal(review, h.review); assert.equal(attempt.session_id, h.review.session_id);
  assert.equal(attempt.workspace, h.copy); assert.deepEqual(attempt.extra_directories, []);
});

test('short Unicode materials follow the same file path and two launches stay isolated', async t => {
  const a = harness(t, { cli: 'Claude Code' }), b = harness(t, { cli: 'opencode' });
  const prompts = ['短材料\n中文 🧑🏽‍💻 café e\u0301\r\n' + randomUUID(), '另一次审查\n' + randomUUID()];
  await Promise.all([a.run(prompts[0]), b.run(prompts[1])]);
  const first = materialFromEntry(a), second = materialFromEntry(b);
  assert.notEqual(first.path, second.path);
  assert.ok(!first.entry.includes(second.path) && !second.entry.includes(first.path));
  assert.deepEqual(first.bytes, Buffer.from(`${a.role}\n\n${prompts[0]}`));
  assert.deepEqual(second.bytes, Buffer.from(`${b.role}\n\n${prompts[1]}`));
});

test('an existing material is never overwritten or dispatched', async t => {
  const h = harness(t), original = Buffer.from('earlier evidence\n完整现场🧭');
  fs.writeFileSync(join(h.requests, 'review-materials.md'), original, { flag: 'wx' });
  await assert.rejects(h.run('new review'), { code: 'EEXIST' });
  assert.deepEqual(fs.readFileSync(join(h.requests, 'review-materials.md')), original);
  assert.equal(h.sent.length, 0, 'existing evidence failure must not dispatch');
});

test('a partial material write failure preserves failure evidence and dispatches nothing', async t => {
  const h = harness(t), write = fs.writeFileSync;
  t.mock.method(fs, 'writeFileSync', (path, data, options) => {
    if (String(path).endsWith('review-materials.md')) {
      write(path, Buffer.from(data).subarray(0, 19), options);
      throw Object.assign(new Error('injected full disk after partial write'), { code: 'ENOSPC' });
    }
    return write(path, data, options);
  });
  syncBuiltinESMExports();
  try {
    await assert.rejects(h.run('complete input must not be partially dispatched'), { code: 'ENOSPC' });
    assert.equal(h.sent.length, 0, 'write failure must not dispatch');
    assert.equal(fs.readFileSync(join(h.requests, 'review-materials.md')).length, 19);
  } finally { t.mock.restoreAll(); syncBuiltinESMExports(); }
});

test('agy keeps its command and read-only checkout; result identity and validation stay intact', async t => {
  const h = harness(t, { cli: 'agy' }), prompt = '完整材料\n提交结论：用 review_submit 工具';
  await h.run(prompt);
  const material = materialFromEntry(h).bytes.toString('utf8');
  assert.ok(material.startsWith(`${h.role}\n\n${prompt}\n\n`), 'role and original prompt preserved');
  assert.match(material, /本会话没有 review_submit 工具/);
  const quote = x => "'" + x.replaceAll("'", "'\\''") + "'";
  const serverPath = resolve('workbench/src/reviewResult.ts');
  assert.ok(material.includes(`ELECTRON_RUN_AS_NODE=1 ${[process.execPath, serverPath, 'submit', h.requests].map(quote).join(' ')} <文件路径>`), 'agy submits via its own launch command');
  assert.equal(fs.statSync(h.readonlyFile).mode & 0o222, 0, 'checkout stays read-only');
  assert.equal(saveReviewResult(h.requests, { verdict: '通过', findings: [], report: {} }).ok, false);
  assert.equal(readReviewResult(h.requests), null);
  const fields = { verdict: '可合并', findings: [], report: { '完成条件与变异检查': 'isolated protocol fixture' } };
  assert.equal(saveReviewResult(h.requests, fields).ok, true);
  assert.deepEqual(JSON.parse(readReviewResult(h.requests)), { ...h.template, ...fields });
});
