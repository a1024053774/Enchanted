// T-249: the Git graph panel without a window. It runs the same code the panel does: the history and lanes from
// gitGraphModel.ts readGraph, git through gitHost.ts (argv, never a shell, reads with the no-lock flags), and a
// repository change through gitHost.ts gitAction (gitGraphModel.ts commandsFor), with the same read-only rule for
// the gate's task worktrees.
//
//   node workbench/app/panels/gitGraphCli.ts <repo> [--scope all|current] [--remotes] [--limit N] [--state DIR]
//     → {"rows": [{"hash", "parents", "refs", "head", "lane", "segments"}], "uncommitted": {"files", "lane", "segments"} | null, ...}
//   node workbench/app/panels/gitGraphCli.ts <repo> --action '<JSON>' [--values '<JSON>'] [--state DIR]
//     → runs one action ({"type":"createBranch","name":"x","hash":"<oid>"}, {"type":"deleteBranch","name":"x"}, …).
//       The action's own fields also fill the dialog values (name, message, …) unless --values gives them.
//       Exits non-zero, with the repository unchanged, when a name is not allowed.
//
// --state is the gate's state directory (default ~/Library/Application Support/a2a-orchestrator); a repository under
// its worktrees/ is read-only, as in the panel.
import { homedir } from 'node:os';
import { join, resolve } from 'node:path';
import { parseArgs } from 'node:util';
import { gitAction, gitRead } from '../gitHost.ts';
import { PAGE, readGraph } from './gitGraphModel.ts';

const { values, positionals } = parseArgs({ allowPositionals: true, options: {
  scope: { type: 'string', default: 'all' }, remotes: { type: 'boolean', default: false }, limit: { type: 'string' },
  state: { type: 'string' }, action: { type: 'string' }, values: { type: 'string' } } });

async function main() {
  if (positionals.length !== 1) throw new Error('用法：gitGraphCli.ts <仓库目录> [--scope all|current] [--remotes] [--limit N] | --action JSON');
  const repo = resolve(positionals[0]!);
  const state = values.state ?? join(homedir(), 'Library/Application Support/a2a-orchestrator');
  if (values.action !== undefined) {
    const action = JSON.parse(values.action);
    if (!action || typeof action !== 'object' || Array.isArray(action)) throw new Error('--action 要是一个 JSON 对象');
    const given = values.values === undefined ? {} : JSON.parse(values.values);
    const done = await gitAction(repo, state, action, { ...action, ...given });
    process.stdout.write(JSON.stringify(done) + '\n');
    return;
  }
  if (values.scope !== 'all' && values.scope !== 'current') throw new Error('--scope 只能是 all 或 current');
  const limit = values.limit === undefined ? PAGE : Number(values.limit);
  if (!Number.isSafeInteger(limit) || limit < 1) throw new Error('--limit 要是正整数');
  const graph = await readGraph(argv => gitRead(repo, argv), { all: values.scope === 'all', remotes: values.remotes, limit });
  const rows = graph.commits.map((commit, index) => ({ commit, row: graph.rows[index]! }));
  const uncommitted = rows.find(entry => entry.commit.uncommitted);
  process.stdout.write(JSON.stringify({
    rows: rows.filter(entry => !entry.commit.uncommitted).map(({ commit, row }) => ({
      hash: commit.hash, parents: commit.parents,
      refs: commit.refs.filter(ref => ref.kind !== 'detached' && (ref.kind !== 'remote' || values.remotes)).map(ref => ref.full),
      head: commit.head, lane: row.lane, segments: row.segments,
      subject: commit.subject, author: commit.author, time: commit.time })),
    uncommitted: uncommitted ? { files: graph.changes, staged: graph.staged, lane: uncommitted.row.lane, segments: uncommitted.row.segments,
      head: uncommitted.commit.parents[0] ?? null } : null,
    width: graph.width, more: graph.more, current: graph.ctx.current, head: graph.ctx.head,
  }) + '\n');
}

main().catch(error => {
  process.stderr.write((error instanceof Error ? error.message : String(error)) + '\n');
  process.exitCode = 1;
});
