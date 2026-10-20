// Compile and execute the exact renderer prompt used by the real Electron driver.
// Expected bytes come from the terminal bracketed-paste/Enter protocol.
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync } from 'node:fs';
import vm from 'node:vm';
const summary=process.argv[2];assert(summary);
const source=readFileSync(new URL('./t108_questions_driver.mjs',import.meta.url),'utf8');
const part=source.split("request.command==='prompt'")[1].split("request.command==='answer'")[0];
const template=part.slice(part.indexOf('executeJavaScript(')+'executeJavaScript('.length,part.lastIndexOf(');'));
const script=new Function('JSON','return '+template)(JSON);
const knownBad=script.replace(JSON.stringify('\r'),'\'\r\'');
assert.notEqual(knownBad,script);assert.throws(()=>new vm.Script(knownBad),SyntaxError);
const received=[];
await new vm.Script(script).runInNewContext({window:{a2a:{input:async(...args)=>received.push(args)}},
  document:{querySelector:()=>({dataset:{paneKey:'fixture-key'}})},setTimeout:callback=>callback()});
assert.deepEqual(received,[['fixture-key','\x1b[200~Please ask the region question.\x1b[201~'],['fixture-key','\r']]);
const result={status:'PASS',model_calls:0,vendor_calls:0,checks:['old_literal_CR_rejected_by_parser','actual_driver_prompt_parses','exact_bracketed_paste_and_enter_bytes']};
writeFileSync(summary,JSON.stringify(result,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(result));
