import {readFileSync} from 'node:fs';
import {pathToFileURL} from 'node:url';
const {humanInterventions}=await import(pathToFileURL(process.argv[2]).href);
const fixture=JSON.parse(readFileSync(process.argv[3],'utf8'));
const event=fixture.event;
const result=humanInterventions([...fixture.events,event],fixture.task);
if(result.filter(v=>v.eventId===event.details.event_id && v.messageId==='' && v.attemptId===fixture.attempt).length!==1)
  throw new Error('Structured answer lost or duplicated');
if(event.details.request_id!==fixture.request || event.details.channel!=='ws-rpc')
  throw new Error('Derived answer lacks authoritative request/channel');
for(const [name,patch] of [
 ['missing-request',{request_id:undefined}],['null-request',{request_id:null}],
 ['empty-request',{request_id:''}],['wrong-request',{request_id:42}],
 ['message-answer-missing-message',{channel:'thread-message'}],
 ['panel-answer-missing-message',{channel:'issue-panel'}],
 ['missing-channel',{channel:undefined}],['wrong-message',{message_id:42}],
]){
  let refused=false;
  try{humanInterventions([{...event,details:{...event.details,...patch}}],fixture.task);}catch{refused=true;}
  if(!refused) throw new Error('Invalid answer accepted: '+name);
}
let refused=false;
try{humanInterventions([{...event,attempt:'unrelated-attempt'}],fixture.task);}catch{refused=true;}
if(!refused) throw new Error('Attempt binding bypassed');
for(const channel of ['thread-message','issue-panel',undefined]){
  const withMessage={...event,details:{...event.details,channel,message_id:'external-message-sentinel'}};
  if(humanInterventions([withMessage],fixture.task)[0]?.messageId!=='external-message-sentinel')
    throw new Error('Message answer rejected');
}
console.log(JSON.stringify({status:'PASS',event,projection:result,negative_cases:9,message_answer_cases:3}));
