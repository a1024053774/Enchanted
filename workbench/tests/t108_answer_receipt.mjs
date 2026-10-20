// Read the actual first window_answer receipt. DOM removal is not a receipt:
// the native hook can remove the form while that request is still failing.
export async function firstAnswerReceipt(db, after, launch, timeout = 25000) {
  const deadline = Date.now() + timeout;
  do {
    const events = db.prepare('SELECT seq,launch,type,data FROM orchestration_events WHERE seq>? ORDER BY seq')
      .all(after).map(row => ({ ...row, data: JSON.parse(row.data) }));
    const first = events.find(event => event.type === 'request_received' && event.data.input?.command === 'window_answer');
    if (first) {
      const terminal = events.find(event => ['request_result', 'request_rejected'].includes(event.type) && event.data.id === first.data.id);
      if (terminal) {
        const admission = events.find(event => event.type === 'window_request_admitted' && event.launch === launch &&
          event.data.command === 'window_answer' && event.data.request_id === first.data.input.request_id &&
          event.data.sequence === first.data.input.sequence);
        if (terminal.type !== 'request_result' || terminal.data.ok !== true || !admission)
          throw new Error('First window_answer failed: ' + JSON.stringify({ first, terminal, admission }));
        return { transport_id: first.data.id, request_id: first.data.input.request_id, sequence: first.data.input.sequence,
          received_seq: first.seq, terminal_seq: terminal.seq, final_receipt: terminal.data };
      }
    }
    await new Promise(resolve => setTimeout(resolve, 25));
  } while (Date.now() < deadline);
  throw new Error('First window_answer final receipt timed out');
}
