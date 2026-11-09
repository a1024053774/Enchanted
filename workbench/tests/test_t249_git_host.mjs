// Supplemental boundary checks: real Git, the production host/model, independent Git/file expectations.
// Failure cases: a read mutates refs/files, dirty HEAD changes lanes, quoted paths break diff;
// pathspecs leak another file in root/normal/dirty diffs; unborn details lose staged/unstaged/untracked files.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync, symlinkSync } from 'node:fs';
import { randomUUID } from 'node:crypto';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { gitRead, gitAction } from '../app/gitHost.ts';
import { readGraph, fileArgs, joinFiles, diffArgs, diffRows } from '../app/panels/gitGraphModel.ts';

Object.assign(process.env, { GIT_AUTHOR_NAME: 'T', GIT_AUTHOR_EMAIL: 't@example.invalid',
  GIT_COMMITTER_NAME: 'T', GIT_COMMITTER_EMAIL: 't@example.invalid' });
const git = (repo, ...args) => execFileSync('git', ['-C', repo, ...args], { encoding: 'utf8',
  env: { ...process.env, GIT_AUTHOR_NAME: 'T', GIT_AUTHOR_EMAIL: 't@example.invalid',
    GIT_COMMITTER_NAME: 'T', GIT_COMMITTER_EMAIL: 't@example.invalid' } });
function fixture(t) {
  const root = mkdtempSync(join(tmpdir(), 't249-host-'));
  t.after(() => rmSync(root, { recursive: true }));
  const repo = join(root, 'state/worktrees/project/repo');
  mkdirSync(repo, { recursive: true });
  git(repo, 'init', '-q', '-b', 'main');
  return { root, repo, state: join(root, 'state') };
}
function commit(repo, name = 'a.txt', value = 'first\n') {
  writeFileSync(join(repo, name), value);
  git(repo, 'add', '--', name); git(repo, 'commit', '-qm', 'fixture');
  return git(repo, 'rev-parse', 'HEAD').trim();
}
function files(root) {
  return Object.fromEntries(readdirSync(root, { recursive: true, withFileTypes: true }).filter(e => e.isFile())
    .map(e => { const p = join(e.parentPath, e.name); return [p, readFileSync(p)]; }));
}

function metadata(repo) {
  const dirs = ['--absolute-git-dir', '--git-common-dir'].map(option =>
    git(repo, 'rev-parse', '--path-format=absolute', option).trim());
  return Object.fromEntries(dirs.map(dir => [dir, files(dir)]));
}

for (const hasHead of [false, true]) {
  test(`untracked content diff reads literal files without Git writes (HEAD=${hasHead})`, async t => {
    const fixtureRepo = fixture(t);
    let { repo } = fixtureRepo;
    if (hasHead) {
      commit(repo);
      const linked = join(fixtureRepo.root, 'linked');
      git(repo, 'worktree', 'add', '-q', '--detach', linked, 'HEAD');
      repo = linked; // Real separate git-dir and common-dir, not a guessed .git directory.
    }
    const names = ['untracked.txt', 'file*.txt', 'file[1].txt', ':(glob)*.txt', '-leading.txt', '-'];
    for (const name of names) writeFileSync(join(repo, name), `SELECTED-${randomUUID()}\n第二行\n`);
    writeFileSync(join(repo, 'other.txt'), 'OTHER-FILE-SENTINEL\n');
    const before = metadata(repo);
    const graph = await readGraph(a => gitRead(repo, a), { all: true, remotes: false, limit: 300 });
    const c = graph.commits[0], args = await fileArgs(c, a => gitRead(repo, a));
    for (const name of names) {
      const result = await gitRead(repo, diffArgs(c, name, args.base, '?'));
      assert.equal(result.code, 0, result.stderr);
      const content = readFileSync(join(repo, name), 'utf8');
      assert.ok(result.stdout.includes('+' + content.split('\n')[0]), `untracked content missing: HEAD=${hasHead} ${name}`);
      assert.ok(!result.stdout.includes('OTHER-FILE-SENTINEL'));
      const oracle = (() => {
        try { return git(repo, 'diff', '--no-index', '--no-color', '--no-ext-diff', '--no-textconv', '--', '/dev/null', './' + name); }
        catch (error) { assert.equal(error.status, 1); assert.equal(String(error.stderr), ''); return String(error.stdout); }
      })();
      assert.equal(result.stdout, oracle);
    }
    assert.deepEqual(metadata(repo), before, 'untracked reads changed real git-dir/common-dir paths or bytes');
  });
}

test('untracked empty and binary files keep Git semantics', async t => {
  const { repo } = fixture(t);
  writeFileSync(join(repo, 'empty.txt'), '');
  writeFileSync(join(repo, 'binary.bin'), Buffer.from([0, 1, 2, 255, 10]));
  const before = metadata(repo);
  const graph = await readGraph(a => gitRead(repo, a), { all: true, remotes: false, limit: 300 });
  for (const name of ['empty.txt', 'binary.bin']) {
    const result = await gitRead(repo, diffArgs(graph.commits[0], name, undefined, '?'));
    assert.equal(result.code, 0, result.stderr);
    assert.equal(diffRows(result.stdout), null, 'non-text file manufactured text hunks');
    let expected;
    try { expected = git(repo, 'diff', '--no-index', '--no-color', '--no-ext-diff', '--no-textconv', '--', '/dev/null', './' + name); }
    catch (error) { assert.equal(error.status, 1); assert.equal(String(error.stderr), ''); expected = String(error.stdout); }
    assert.equal(result.stdout, expected);
    if (name === 'binary.bin') assert.match(result.stdout, /Binary files .* differ/);
  }
  assert.deepEqual(metadata(repo), before);
});

test('no-index boundary rejects every extra option and operand', async t => {
  const { repo, root } = fixture(t); commit(repo);
  writeFileSync(join(repo, 'new.txt'), 'NEW\n');
  const before = metadata(repo), contents = files(root);
  const base = ['diff', '--no-index', '--no-color', '--no-ext-diff', '--no-textconv'];
  const attacks = [
    ...['--output', '--out', '--o'].map(flag => [...base, `${flag}=${join(root, 'written')}`, '--', '/dev/null', './new.txt']),
    [...base, '--output', join(root, 'written'), '--', '/dev/null', './new.txt'],
    [...base, '--', '/dev/null', './new.txt', './a.txt'],
    [...base, '--', './a.txt', './new.txt'],
    ['diff', '--no-index', '--', '/dev/null', './new.txt'],
    [...base, '--ext-diff', '--', '/dev/null', './new.txt'],
    [...base, '--textconv', '--', '/dev/null', './new.txt'],
  ];
  for (const argv of attacks) await assert.rejects(gitRead(repo, argv), /不允许/, JSON.stringify(argv));
  assert.deepEqual(metadata(repo), before);
  assert.deepEqual(files(root), contents, 'rejected options wrote a file');
});

test('no-index boundary rejects directories and paths outside repository files', async t => {
  const { repo, root } = fixture(t); commit(repo);
  writeFileSync(join(root, 'outside.txt'), 'OUTSIDE\n');
  writeFileSync(join(repo, 'new.txt'), 'NEW\n');
  mkdirSync(join(repo, 'directory'));
  symlinkSync(join(root, 'outside.txt'), join(repo, 'escaped.txt'));
  symlinkSync(root, join(repo, 'escaped-dir'));
  symlinkSync(join(repo, 'new.txt'), join(repo, 'inside-link'));
  symlinkSync(join(repo, '.git'), join(repo, 'metadata-link'));
  const before = metadata(repo);
  const base = ['diff', '--no-index', '--no-color', '--no-ext-diff', '--no-textconv', '--', '/dev/null'];
  for (const path of ['./escaped-dir/outside.txt', '-', 'new.txt', join(root, 'outside.txt'), './../../../outside.txt', './directory', './',
    './escaped.txt', './escaped-dir/outside.txt', './inside-link', './.git/config', './metadata-link/config', './missing']) {
    await assert.rejects(gitRead(repo, [...base, path]), undefined, `unsafe path accepted: ${path}`);
  }
  await assert.rejects(gitRead(root, [...base, './outside.txt']), /仓库根目录/);
  assert.deepEqual(metadata(repo), before);
});

for (const attack of ['symbolic-ref', 'log-output', 'show-output', 'cat-file-filters', 'hash-object-write', 'hash-object-other-file']) {
  test(`read boundary rejects ${attack} and preserves Git metadata`, async t => {
    const { repo, root } = fixture(t); const head = commit(repo);
    git(repo, 'branch', 'other'); const before = files(join(repo, '.git'));
    const argv = {
      'symbolic-ref': ['symbolic-ref', 'HEAD', 'refs/heads/other'],
      'log-output': ['log', `--out=${join(root, 'written')}`],
      'show-output': ['show', head, `--out=${join(root, 'written')}`],
      'cat-file-filters': ['cat-file', '--filters', 'HEAD:a.txt'],
      'hash-object-write': ['hash-object', '-w', '-t', 'tree', '/dev/null'],
      'hash-object-other-file': ['hash-object', '-t', 'blob', 'a.txt'],
    }[attack];
    let refused = false;
    try { await gitRead(repo, argv); } catch { refused = true; }
    assert.deepEqual(files(join(repo, '.git')), before, 'read changed Git metadata');
    assert.equal(refused, true, 'unsafe read accepted');
  });
}

test('unborn single-file diff works before the first commit', async t => {
  const { repo } = fixture(t);
  writeFileSync(join(repo, 'first.txt'), 'first\n'); git(repo, 'add', 'first.txt');
  const graph = await readGraph(a => gitRead(repo, a), { all: true, remotes: false, limit: 300 });
  const c = graph.commits[0], argv = await fileArgs(c, a => gitRead(repo, a));
  const diff = await gitRead(repo, diffArgs(c, 'first.txt', argv.base));
  const empty = git(repo, 'hash-object', '-t', 'tree', '/dev/null').trim();
  assert.equal(diff.code, 0, diff.stderr);
  assert.equal(diff.stdout, git(repo, '--literal-pathspecs', 'diff', '--no-color', '--no-ext-diff', '--no-textconv', empty, '--', 'first.txt'));
});
test('managed write action is rejected without metadata changes', async t => {
  const { repo, state } = fixture(t); const head = commit(repo); const before = files(join(repo, '.git'));
  await assert.rejects(gitAction(repo, state, { type: 'createBranch', hash: head }, { name: 'forbidden' }), /只读/);
  assert.deepEqual(files(join(repo, '.git')), before);
});
test('uncommitted row stays in HEAD lane even beneath another branch', async t => {
  const { repo } = fixture(t); const head = commit(repo);
  git(repo, 'checkout', '-qb', 'ahead'); commit(repo, 'b.txt'); git(repo, 'checkout', '-q', 'main');
  writeFileSync(join(repo, 'a.txt'), 'dirty\n');
  const graph = await readGraph(a => gitRead(repo, a), { all: true, remotes: false, limit: 300 });
  const headIndex = graph.commits.findIndex(c => c.hash === head);
  assert.equal(graph.rows[0].lane, graph.rows[headIndex].lane);
  assert.ok(graph.rows[headIndex].segments.some(s => s[5] && s[2] === graph.rows[0].lane && s[3] === .5));
});
test('Chinese and tab-containing file names survive details and diff', async t => {
  const { repo } = fixture(t); commit(repo);
  const names = ['中文.txt', 'tab\tname.txt'];
  for (const name of names) commit(repo, name, 'sentinel-added-line\n');
  const graph = await readGraph(a => gitRead(repo, a), { all: true, remotes: false, limit: 300 });
  for (const c of graph.history.slice(0, 2)) {
    const argv = await fileArgs(c, a => gitRead(repo, a));
    const status = await gitRead(repo, argv.status), numstat = await gitRead(repo, argv.numstat);
    const changed = joinFiles(status.stdout, numstat.stdout);
    const expected = git(repo, 'diff-tree', '--no-commit-id', '-r', '--name-only', '-z', c.hash).split('\0').filter(Boolean);
    assert.deepEqual(changed.map(f => f.path), expected);
    const diff = await gitRead(repo, diffArgs(c, expected[0]));
    assert.equal(diff.code, 0); assert.ok(diff.stdout.includes('+sentinel-added-line'));
  }
});
test('current branch of an unborn repository is an empty graph', async t => {
  const { repo } = fixture(t);
  const graph = await readGraph(a => gitRead(repo, a), { all: false, remotes: false, limit: 300 });
  assert.deepEqual(graph.history, []); assert.equal(graph.ctx.head, null);
});

for (const kind of ['root', 'normal', 'uncommitted']) {
  for (const [selected, other] of [['file*.txt', 'file-other.txt'], ['file[1].txt', 'file1.txt'], [':(glob)*.txt', 'other.txt']]) {
    test(`literal single-file diff: ${kind} ${selected}`, async t => {
      const { repo } = fixture(t);
      const writePair = phase => {
        writeFileSync(join(repo, selected), `SELECTED-${phase}\n`);
        writeFileSync(join(repo, other), `OTHER-FILE-SENTINEL-${phase}\n`);
      };
      writePair('root'); git(repo, 'add', '--all'); git(repo, 'commit', '-qm', 'root');
      if (kind !== 'root') writePair(kind);
      if (kind === 'normal') { git(repo, 'add', '--all'); git(repo, 'commit', '-qm', 'normal'); }
      const graph = await readGraph(a => gitRead(repo, a), { all: true, remotes: false, limit: 300 });
      const c = graph.commits[0];
      const argv = await fileArgs(c, a => gitRead(repo, a));
      const result = await gitRead(repo, diffArgs(c, selected, argv.base));
      // Independent oracle: Git's global literal-pathspecs mode, with range read directly from Git.
      const range = kind === 'root' ? ['show', '--format=', git(repo, 'rev-parse', 'HEAD').trim()]
        : ['diff', ...(kind === 'normal' ? git(repo, 'rev-list', '--parents', '-n1', 'HEAD').trim().split(' ').reverse() : ['HEAD'])];
      const expected = git(repo, '--literal-pathspecs', ...range, '--no-color', '--no-ext-diff', '--no-textconv', '--', selected);
      assert.equal(result.code, 0, result.stderr);
      assert.ok(result.stdout.includes(`+SELECTED-${kind}`), 'selected content missing');
      assert.ok(!result.stdout.includes('OTHER-FILE-SENTINEL'), 'another file leaked into the selected diff');
      assert.equal(result.stdout, expected);
    });
  }
}

for (const hasHead of [false, true]) {
  test(`uncommitted details include staged, unstaged and untracked files (HEAD=${hasHead})`, async t => {
    const { repo } = fixture(t);
    if (hasHead) commit(repo);
    writeFileSync(join(repo, 'staged.txt'), 'staged\n');
    writeFileSync(join(repo, 'mixed.txt'), 'in-index\n');
    git(repo, 'add', 'staged.txt', 'mixed.txt');
    writeFileSync(join(repo, 'mixed.txt'), 'working-tree\nsecond-line\n');
    writeFileSync(join(repo, 'unstaged.txt'), 'only-working-tree\n');
    git(repo, 'add', '-N', 'unstaged.txt');
    writeFileSync(join(repo, 'untracked.txt'), 'untracked\n');
    const before = files(join(repo, '.git'));
    const graph = await readGraph(a => gitRead(repo, a), { all: true, remotes: false, limit: 300 });
    const c = graph.commits[0];
    assert.equal(Boolean(graph.ctx.head), hasHead);
    assert.equal(c.uncommitted, true);
    const argv = await fileArgs(c, a => gitRead(repo, a));
    const [status, numstat, untracked] = await Promise.all([
      gitRead(repo, argv.status), gitRead(repo, argv.numstat), gitRead(repo, ['ls-files', '--others', '--exclude-standard', '-z']),
    ]);
    assert.equal(status.code, 0, status.stderr);
    assert.equal(numstat.code, 0, numstat.stderr);
    assert.equal(untracked.code, 0, untracked.stderr);
    const changed = joinFiles(status.stdout, numstat.stdout);
    const listed = [...changed.map(f => f.path), ...untracked.stdout.split('\0').filter(Boolean)];
    const expectedPaths = git(repo, '--no-optional-locks', 'status', '--porcelain=v1', '-z', '--no-renames', '--untracked-files=all')
      .split('\0').filter(Boolean).map(entry => entry.slice(3)).sort();
    assert.deepEqual(listed.sort(), expectedPaths);
    const baseline = hasHead ? git(repo, 'rev-parse', 'HEAD').trim() : git(repo, 'hash-object', '-t', 'tree', '/dev/null').trim();
    for (const f of changed) {
      const expectedStats = git(repo, '--literal-pathspecs', 'diff', '--numstat', '-z', baseline, '--', f.path).split('\t');
      assert.deepEqual([f.add, f.del], expectedStats.slice(0, 2).map(Number));
      const diff = await gitRead(repo, diffArgs(c, f.path, argv.base));
      assert.equal(diff.code, 0, diff.stderr);
      assert.equal(diff.stdout, git(repo, '--literal-pathspecs', 'diff', '--no-color', '--no-ext-diff', '--no-textconv', baseline, '--', f.path));
    }
    assert.deepEqual(files(join(repo, '.git')), before, 'reading details wrote Git metadata');
  });
}
