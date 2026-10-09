import { readFileSync, writeFileSync } from 'node:fs';
import { ClientOrchestrationCommand } from '/Users/luckye/Documents/Code/synara/packages/contracts/src/orchestration.ts';
import { Schema } from '/Users/luckye/Documents/Code/synara/apps/server/node_modules/effect/dist/index.js';
const [thread, output]=process.argv.slice(2);
const path='/Users/luckye/Documents/Code/synara/apps/web/src/components/BranchToolbar.tsx';
const source=readFileSync(path,'utf8');const token='type: "thread.session.stop"';
const calls=[];let index=0;
for(let position=source.indexOf(token);position!==-1;position=source.indexOf(token,position+token.length)) {
 const first=source.lastIndexOf('{',position),last=source.indexOf('}',position)+1;
 const expression=source.slice(first,last);
 const command=new Function('newCommandId','activeThreadId','Date',`return (${expression});`)(
  ()=>`00000000-0000-4000-8000-${String(++index).padStart(12,'0')}`,thread,
  class extends Date {constructor(){super('2026-10-09T19:30:00.000Z');}});
 calls.push({path,line:source.slice(0,position).split('\n').length,expression,
  command:Schema.decodeUnknownSync(ClientOrchestrationCommand)(command)});
}
if(calls.length!==2)throw new Error('Expected the two known workspace-derived stop constructors');
writeFileSync(output,JSON.stringify(calls,null,2)+'\n');
