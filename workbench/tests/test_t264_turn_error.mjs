// T-264: a Codex turn that ends on an account error (task_complete with `error`, no Stop) is shown as 回合出错结束,
// not 运行中. Expected values come from the real record shape in
// evidence/2026-11-09-batch35/T-264/controller/terra-a5-quota-error.json, not from the implementation.
// Usage: node tests/test_t264_turn_error.mjs [sidebar module]
import assert from 'node:assert/strict';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
const { agentState, aggregate, stateLabels } = await import(process.argv[2] ? pathToFileURL(resolve(process.argv[2])).href : new URL('../src/sidebar.ts', import.meta.url).href);

const repo = '/work/tree';
const root = 'sessions/rollout-native.jsonl', helper = 'sessions/rollout-helper.jsonl';
const record = (file, payload, type = 'event_msg') => ({ type: 'native_record', data: { file, record: { type, payload } } });
const meta = [record(root, { id: 'native', source: 'cli', cwd: repo }, 'session_meta'),
  record(helper, { id: 'helper', source: { subagent: { parent_thread_id: 'native' } }, cwd: repo }, 'session_meta')];
const started = turn => record(root, { type: 'task_started', turn_id: turn, root_turn_id: turn });
const quota = { message: 'Your workspace is out of credits. Add credits to continue.', codex_error_info: 'usage_limit_exceeded' };
const complete = (turn, error, file = root) => record(file, { type: 'task_complete', turn_id: turn, root_turn_id: turn, ...(error ? { error } : {}) });
const pane = (turn = 't2') => ({ lifecycle: 'running', state: 'busy', native_session: 'native', turn, active: { id: 'sub', nativeTurn: turn } });
const state = (p, events) => agentState(p, events, repo);
const checks = [];
const check = (name, actual, expected) => { assert.equal(actual, expected, name); checks.push(name); };

check('quota_error_on_current_turn', state(pane(), [...meta, started('t2'), complete('t2', quota)]), 'turn_error');
check('label_names_the_error_end', stateLabels.turn_error, '回合出错结束');
check('normal_task_complete_stays_running_until_stop', state(pane(), [...meta, started('t2'), complete('t2')]), 'running');
check('working_turn_without_complete', state(pane(), [...meta, started('t2')]), 'running');
check('error_on_old_turn_then_new_turn', state(pane(), [...meta, started('t1'), complete('t1', quota), started('t2')]), 'running');
check('auxiliary_log_error_ignored', state(pane(), [...meta, started('t2'), complete('t2', quota, helper)]), 'running');
check('error_for_other_turn_id_ignored', state(pane(), [...meta, started('t2'), complete('t9', quota)]), 'running');
check('after_user_release_pane_idle', state({ ...pane(), state: 'idle', active: null }, [...meta, started('t2'), complete('t2', quota)]), 'idle');
check('foreign_session_root_unknown', state({ ...pane(), native_session: 'other' }, [...meta, started('t2'), complete('t2', quota)]), 'unknown');
check('aggregate_surfaces_error_over_running', aggregate(['running', 'turn_error', 'idle']), 'turn_error');
check('aggregate_user_question_first', aggregate(['turn_error', 'waiting_user_answer']), 'waiting_user_answer');
console.log(JSON.stringify({ status: 'PASS', checks }));
