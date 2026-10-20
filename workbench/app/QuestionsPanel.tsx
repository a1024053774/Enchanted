import { useState } from 'react';
import type { NativeQuestion } from '../src/questions.ts';
import './questions.css';

export function QuestionsPanel({ questions, enabled, send }: {
  questions: NativeQuestion[]; enabled: boolean; send: (question: string, answers: string[]) => Promise<unknown>;
}) {
  return <div className="questions-panel" aria-label="原生提问">{questions.filter(q => !['answered','cancelled'].includes(q.status)).map(question =>
    <Question key={question.id} question={question} enabled={enabled} send={send} />)}</div>;
}
function Question({ question, enabled, send }: { question: NativeQuestion; enabled: boolean;
  send: (question: string, answers: string[]) => Promise<unknown> }) {
  const [answers, setAnswers] = useState<string[]>(question.questions.map(() => ''));
  const [sending, setSending] = useState(false), [submitted, setSubmitted] = useState(false), [error, setError] = useState('');
  const supported = question.blocking && question.questions.every(q => !q.multiSelect);
  const writable = enabled && supported && question.status === 'waiting' && !sending && !submitted;
  return <form className="native-question" data-question-id={question.id} onSubmit={event => {
    event.preventDefault(); setSending(true); setError('');
    void send(question.id, answers).then(() => setSubmitted(true), reason => setError(String(reason))).finally(() => setSending(false));
  }}>
    <div className="question-heading"><strong>{question.status === 'unknown' ? '问题状态未知' : !question.blocking ? '异步提问 · 阻塞状态未知' : question.target === 'controller' ? '等待主控回答' : '等待用户回答'}</strong>
      <span>{question.cli === 'claude' ? 'Claude Code' : 'Codex'} · 当前窗格</span></div>
    {question.questions.map((item, index) => <fieldset key={index} disabled={!writable}>
      <legend>{item.question}</legend>
      <div className="question-options">{item.options.map(option => <button type="button" key={option.label}
        aria-pressed={answers[index] === option.label} onClick={() => setAnswers(values => values.map((v, i) => i === index ? option.label : v))}>
        {option.label}{option.description && <small>{option.description}</small>}</button>)}</div>
      <label>补充或其他答复<input value={answers[index]} maxLength={4000} onChange={event =>
        setAnswers(values => values.map((v, i) => i === index ? event.target.value : v))} /></label>
    </fieldset>)}
    {!supported && <p>此类提问的写回方式尚未验证，请在原生窗格作答。</p>}
    {question.status !== 'waiting' || submitted ? <p role="status">{question.status === 'sending' || submitted && question.status !== 'unknown' ? '答复已送入窗格，等待原生确认。' : '问题状态未知，请核对原生窗格。'}</p> : null}
    {error && <p role="alert">{error}</p>}
    <button disabled={!writable || answers.some(value => !value.trim())}>发送答复到窗格</button>
  </form>;
}
