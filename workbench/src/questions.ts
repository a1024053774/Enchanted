import { basename } from 'node:path';
import { isDeepStrictEqual } from 'node:util';
import { nativeSessionFile } from './paneRecovery.ts';
import { Refusal } from './gates/core.ts';

export type NativeQuestion = {
  id: string; cli: 'claude' | 'codex'; target: 'user' | 'controller'; session_id: string;
  turn: string; submission: string; tool_use_id: string; input_generation: number; blocking: boolean;
  questions: { id?: string; question: string; header?: string; options: { label: string; description?: string }[]; multiSelect: boolean }[];
  status: 'waiting' | 'sending' | 'answered' | 'cancelled' | 'unknown';
};
const requireField = (value: unknown, error: string) => { if (!value) throw new Refusal(error); };
const questionTool = (name: string) => ['AskUserQuestion', 'request_user_input', 'request_user_input_async'].includes(name);
export type QuestionBinding = Pick<NativeQuestion, 'session_id' | 'submission' | 'turn'>;

// The authenticated launch supplies the binding even when a hook omits its
// own association fields. Explicit foreign/old/child events are excluded first.
export function currentTurnBinding(pane: any): { session_id: string; submission: string; turn: string | null } | null {
  if (!pane.active || !pane.native) return null;
  return { session_id: pane.native, submission: pane.active.id,
    turn: pane.record.cli === 'Claude Code' ? pane.claudePromptId ?? null : pane.active.nativeTurn ?? null };
}
export function noncurrentHook(pane: any, value: any, received_at: string): boolean {
  const turn = pane.record.cli === 'Claude Code' ? pane.claudePromptId : pane.active?.nativeTurn;
  const claimed = pane.record.cli === 'Claude Code' ? value.prompt_id : value.turn_id;
  return Boolean(typeof value.session_id === 'string' && value.session_id.length > 0 && value.session_id !== pane.native ||
    typeof value.agent_id === 'string' && value.agent_id.length > 0 ||
    turn && typeof claimed === 'string' && claimed.length > 0 && claimed !== turn || pane.active?.at && Date.parse(received_at) < Date.parse(pane.active.at));
}

// One admission source for sidebar, answers (including every yielded write),
// and completion. Unknown is sticky for the submission; a later tool cannot
// repair missing evidence. A recorded native permission control clears only
// permission waiting, never an unknown hook.
export function currentTurnTrust(pane: any, events: any[]): 'verified' | 'unknown' | 'permission' {
  const native = pane.native ?? pane.native_session;
  const current = (data: any) => pane.active && data?.session_id === native && data.submission === pane.active.id;
  let permission = false;
  for (const event of events) {
    if (!current(event.data)) continue;
    if (event.type === 'native_question_unverified') return 'unknown';
    if (event.type === 'permission_wait') permission = true;
    if (event.type === 'permission_control_written') permission = false;
  }
  return permission ? 'permission' : 'verified';
}

// All hook kinds pass the same envelope checks before event-specific logic.
// Exclusion of explicit foreign/old/child identity precedes this function.
// Fresh Codex launches use the same strict root-file locator as recovery; a
// restored pane already holds that locator result. Collector scanning is unchanged.
export function validateHookEnvelope(pane: any, value: any): void {
  const claude = pane.record.cli === 'Claude Code';
  requireField(typeof value.session_id === 'string' && value.session_id.length > 0 && value.session_id === pane.native, 'hook_native_session_mismatch');
  requireField(!value.agent_id && value.cwd === pane.record.worktree && typeof value.transcript_path === 'string' &&
    (claude ? basename(value.transcript_path) === `${pane.native}.jsonl` :
      value.transcript_path === (pane.nativeFile ?? nativeSessionFile(pane.record, pane.native))), 'question_origin_unverified');
  if (claude) {
    requireField(typeof value.prompt_id === 'string' && value.prompt_id.length > 0 && value.prompt_id.length <= 128, 'claude_prompt_id_required');
    if (value.hook_event_name !== 'UserPromptSubmit' && !(value.hook_event_name === 'Stop' && !pane.claudePromptId)) requireField(pane.claudePromptId && value.prompt_id === pane.claudePromptId, 'question_turn_mismatch');
  } else {
    requireField(typeof value.turn_id === 'string' && value.turn_id.length > 0, 'hook_turn_id_required');
    if (value.hook_event_name !== 'UserPromptSubmit' && !(value.hook_event_name === 'Stop' && !pane.active?.nativeTurn)) requireField(pane.active?.nativeTurn &&
      value.turn_id === pane.active.nativeTurn && pane.turn === value.turn_id, 'question_turn_mismatch');
  }
  if (value.hook_event_name === 'PermissionRequest') requireField(typeof value.tool_name === 'string' && value.tool_name.trim() &&
    value.tool_input && typeof value.tool_input === 'object' && !Array.isArray(value.tool_input), 'permission_tool_fields_required');
  if (['PreToolUse', 'PostToolUse', 'PostToolUseFailure'].includes(value.hook_event_name)) {
    requireField(pane.active && !pane.failed && !pane.stopped && !pane.interrupted, 'question_turn_mismatch');
  }
}

// The caller has verified this binding. Null means a complete unrelated tool.
export function questionFromHook(pane: any, value: any, binding: QuestionBinding): NativeQuestion | null {
  const claude = pane.record.cli === 'Claude Code';
  requireField(typeof value.tool_use_id === 'string' && value.tool_use_id.length > 0, 'question_tool_id_required');
  // A missing name cannot establish that this is an unrelated tool. Validate
  // the common envelope before classifying; ingress records and rejects gaps.
  requireField(typeof value.tool_name === 'string' && value.tool_name.trim().length > 0, 'question_tool_name_required');
  requireField(value.tool_input && typeof value.tool_input === 'object' && !Array.isArray(value.tool_input), 'question_tool_input_required');
  if (!questionTool(value.tool_name)) return null;
  const questions = value.tool_input?.questions;
  requireField(Array.isArray(questions) && questions.length >= 1 && questions.length <= 4, 'question_fields_missing');
  const normalized = questions.map((q: any) => {
    if (!claude && value.tool_name === 'request_user_input_async') {
      requireField(typeof q.title === 'string' && q.title.trim() && (q.options === undefined ||
        Array.isArray(q.options) && q.options.every((o: any) => typeof o === 'string')), 'question_fields_missing');
      return { question: q.title, options: (q.options ?? []).map((label: string) => ({ label })), multiSelect: false };
    }
    requireField(typeof q.question === 'string' && q.question.trim() && Array.isArray(q.options) && q.options.length >= 2 &&
      q.options.length <= 4 && q.options.every((o: any) => typeof o.label === 'string' && o.label.trim() &&
      (o.description === undefined || typeof o.description === 'string')) && (!claude || typeof q.multiSelect === 'boolean'), 'question_fields_missing');
    requireField(claude || typeof q.id === 'string' && q.id.trim(), 'question_fields_missing');
    requireField(new Set(q.options.map((o: any) => o.label)).size === q.options.length, 'question_options_ambiguous');
    return { id: q.id, question: q.question, header: q.header, options: q.options.map((o: any) => ({ label: o.label, description: o.description })), multiSelect: q.multiSelect ?? false };
  });
  requireField(new Set(normalized.map((q: any) => q.question)).size === normalized.length, 'question_text_ambiguous');
  return { id: `${pane.record.id}:${value.tool_use_id}`, cli: claude ? 'claude' : 'codex',
    target: pane.record.role === 'worker' ? 'controller' : 'user', ...binding, tool_use_id: value.tool_use_id,
    input_generation: pane.inputGeneration, blocking: value.tool_name !== 'request_user_input_async', questions: normalized, status: 'waiting' };
}

// #28: Claude emits PermissionRequest as part of AskUserQuestion itself.
// Other tools remain permission waits. A claimed question must match the
// current unique pending question with complete, identical question content.
// Optional IDs are compared when supplied. No text or screen inference is used.
export function questionPermission(pane: any, value: any, questions: NativeQuestion[]): NativeQuestion | null {
  if (pane.record.cli !== 'Claude Code' || value.tool_name !== 'AskUserQuestion') return null;
  const pending = questions.filter(q => q.cli === 'claude' && ['waiting', 'sending'].includes(q.status) &&
    q.session_id === value.session_id && q.session_id === pane.native && q.submission === pane.active?.id &&
    q.turn === value.prompt_id && q.turn === pane.claudePromptId);
  requireField(pending.length === 1, 'question_permission_unverified');
  const question = pending[0];
  requireField(!Object.hasOwn(value, 'turn_id') || value.turn_id === question.turn, 'question_permission_mismatch');
  requireField(!Object.hasOwn(value, 'tool_use_id') || value.tool_use_id === question.tool_use_id, 'question_permission_mismatch');
  // #30: only complete question content is positive proof. The verified
  // permission input shape contains questions alone; unknown extra parameters
  // (at any level) cannot be silently discarded by normalizing another tool.
  requireField(Object.keys(value.tool_input).length === 1 && Object.hasOwn(value.tool_input, 'questions'),
    'question_permission_content_required');
  requireField(isDeepStrictEqual(JSON.parse(JSON.stringify(value.tool_input.questions)), question.questions),
    'question_permission_mismatch');
  return question;
}

// Pure event projection: sidebar and window reads never collect or persist facts.
export function projectQuestions(events: any[]): NativeQuestion[] {
  const questions = new Map<string, NativeQuestion>();
  for (const event of events) {
    if (event.type === 'native_question_opened') questions.set(event.data.id, { ...event.data, status: 'waiting' });
    const question = questions.get(event.data?.question);
    if (!question) continue;
    if (event.type === 'native_question_answer_intent' && question.status === 'waiting') question.status = 'sending';
    if (event.type === 'native_question_resolved' && ['waiting', 'sending'].includes(question.status)) question.status = event.data.status;
  }
  return [...questions.values()].map(question => {
    const trust = currentTurnTrust({ native: question.session_id, active: { id: question.submission } }, events);
    return ['waiting', 'sending'].includes(question.status) && trust !== 'verified' ? { ...question, status: 'unknown' as const } : question;
  });
}

export function questionState(pane: any, events: any[]): 'waiting_user_answer' | 'waiting_controller_answer' | 'unknown' | null {
  if (currentTurnTrust(pane, events) !== 'verified') return 'unknown';
  const questions = projectQuestions(events).filter(q => !['answered', 'cancelled'].includes(q.status) &&
    (!pane.active || q.submission === pane.active.id));
  if (!questions.length) return null;
  if (questions.length !== 1) return 'unknown';
  const question = questions[0];
  if (!question.blocking || question.status !== 'waiting' || question.session_id !== pane.native_session || question.submission !== pane.active?.id) return 'unknown';
  return question.target === 'controller' ? 'waiting_controller_answer' : 'waiting_user_answer';
}

// A terminal write is not confirmation. Only a later native resolution of
// this exact bound question and these exact answers can finish an in-flight
// answer without sending the remaining selection keys.
export function questionAnswerConfirmed(question: NativeQuestion, answers: string[], events: any[], after: number): boolean {
  const resolved = events.findLast(event => event.seq > after && event.type === 'native_question_resolved' &&
    event.data.question === question.id && event.data.session_id === question.session_id &&
    event.data.submission === question.submission && event.data.turn === question.turn);
  if (resolved?.data.status !== 'answered') return false;
  const response = typeof resolved.data.response === 'string' ? JSON.parse(resolved.data.response) : resolved.data.response;
  return question.questions.every((item, index) => question.cli === 'claude' ? response?.answers?.[item.question] === answers[index] :
    Array.isArray(response?.answers?.[item.id!]?.answers) && response.answers[item.id!].answers.length === 1 &&
      response.answers[item.id!].answers[0] === answers[index]);
}

export function nativeAnswerKeys(question: NativeQuestion, answers: string[]): string[] {
  requireField(question.blocking, 'question_answer_protocol_unverified');
  requireField(Array.isArray(answers) && answers.length === question.questions.length &&
    answers.every(a => typeof a === 'string' && a.trim() && a.length <= 4000 && !/[\x00-\x1f\x7f]/.test(a)), 'invalid_question_answer');
  const keys: string[] = [];
  for (let index = 0; index < answers.length; index++) {
    const item = question.questions[index];
    requireField(!item.multiSelect, 'question_multiselect_protocol_unverified');
    const choice = item.options.findIndex(option => option.label === answers[index]);
    for (let step = 0; step < (choice < 0 ? item.options.length : choice); step++) keys.push('\x1b[B');
    if (choice < 0) {
      if (question.cli === 'codex') keys.push('\t');
      keys.push('\x1b[200~' + answers[index] + '\x1b[201~');
    }
    keys.push('\r');
  }
  if (question.cli === 'claude') keys.push('\r'); // native review/submit tab
  return keys;
}
