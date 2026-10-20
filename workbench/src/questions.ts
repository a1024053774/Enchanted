import { basename } from 'node:path';
import { Refusal } from './gates/core.ts';

export type NativeQuestion = {
  id: string; cli: 'claude' | 'codex'; target: 'user' | 'controller'; session_id: string;
  turn: string; submission: string; tool_use_id: string; input_generation: number; blocking: boolean;
  questions: { id?: string; question: string; header?: string; options: { label: string; description?: string }[]; multiSelect: boolean }[];
  status: 'waiting' | 'sending' | 'answered' | 'cancelled' | 'unknown';
};
const requireField = (value: unknown, error: string) => { if (!value) throw new Refusal(error); };
export const questionTool = (name: string) => ['AskUserQuestion', 'request_user_input', 'request_user_input_async'].includes(name);

// Called only at authenticated hook ingress. A child inherits hook credentials;
// session_id alone therefore cannot establish root ownership.
export function questionFromHook(pane: any, value: any): NativeQuestion {
  const claude = pane.record.cli === 'Claude Code';
  requireField(!value.agent_id && value.cwd === pane.record.worktree && typeof value.transcript_path === 'string' &&
    (claude ? basename(value.transcript_path) === `${pane.native}.jsonl` : value.transcript_path === pane.nativeFile), 'question_origin_unverified');
  requireField(pane.active && !pane.failed && !pane.stopped && !pane.interrupted &&
    (claude ? pane.claudePromptId && value.prompt_id === pane.claudePromptId :
      pane.active.nativeTurn && value.turn_id === pane.active.nativeTurn && pane.turn === value.turn_id), 'question_turn_mismatch');
  requireField(typeof value.tool_use_id === 'string' && value.tool_use_id.length > 0, 'question_tool_id_required');
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
    target: pane.record.role === 'worker' ? 'controller' : 'user', session_id: pane.native,
    turn: claude ? pane.claudePromptId : pane.turn, submission: pane.active.id, tool_use_id: value.tool_use_id,
    input_generation: pane.inputGeneration, blocking: value.tool_name !== 'request_user_input_async', questions: normalized, status: 'waiting' };
}

// Pure event projection: sidebar and window reads never collect or persist facts.
export function projectQuestions(events: any[]): NativeQuestion[] {
  const questions = new Map<string, NativeQuestion>();
  for (const event of events) {
    if (event.type === 'native_question_opened') questions.set(event.data.id, { ...event.data, status: 'waiting' });
    const question = questions.get(event.data?.question);
    if (!question) continue;
    if (event.type === 'native_question_answer_intent') question.status = 'sending';
    if (event.type === 'native_question_resolved') question.status = event.data.status;
  }
  return [...questions.values()];
}

export function questionState(pane: any, events: any[]): 'waiting_user_answer' | 'waiting_controller_answer' | 'unknown' | null {
  const questions = projectQuestions(events).filter(q => !['answered', 'cancelled'].includes(q.status));
  if (!questions.length) return events.findLast(e => ['native_question_unverified','native_question_opened','native_question_resolved'].includes(e.type))?.type === 'native_question_unverified' ? 'unknown' : null;
  if (questions.length !== 1) return 'unknown';
  const question = questions[0];
  if (!question.blocking || question.status !== 'waiting' || question.session_id !== pane.native_session || question.submission !== pane.active?.id) return 'unknown';
  return question.target === 'controller' ? 'waiting_controller_answer' : 'waiting_user_answer';
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
