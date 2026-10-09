import { readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
const { humanInterventions } = await import(pathToFileURL(process.argv[2]).href);
const events = JSON.parse(readFileSync(process.argv[3], 'utf8'));
const edit = events.find(e => e.type === 'human_intervention' && e.details.form === 'action' && e.details.message_id);
if (!edit) throw new Error('Missing real managed edit input');
const result = humanInterventions(events, edit.task);
if (result.filter(e => e.eventId === edit.details.event_id && e.messageId === edit.details.message_id).length !== 1)
  throw new Error('Managed edit target lost in intervention projection');
for (const bad of ['', 42]) {
  let rejected = false;
  try { humanInterventions([{...edit, details: {...edit.details, message_id: bad}}], edit.task); }
  catch { rejected = true; }
  if (!rejected) throw new Error('Invalid action message key accepted');
}
console.log(JSON.stringify({status:'PASS', real_event:edit, projection:result}));
