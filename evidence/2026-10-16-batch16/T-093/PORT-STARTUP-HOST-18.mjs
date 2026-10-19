import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import net from 'node:net';
import {EventEmitter} from 'node:events';
import {Readable,Writable,PassThrough} from 'node:stream';
import {stripTypeScriptTypes} from 'node:module';
import {randomUUID} from 'node:crypto';
import * as vm from 'node:vm';
import * as facts from '/Users/luckye/Documents/Code/a2a-wt-t093/workbench/src/claudeLoginFacts.ts';
const original=fs.readFileSync('/Users/luckye/Documents/Code/a2a-wt-t093/workbench/src/claudeForwarder.ts','utf8');
const nonce=randomUUID().replaceAll('-',''),configured='configured-'+nonce+'.invalid',wrong='other-'+nonce+'.invalid';
const journalRoot=fs.mkdtempSync('/private/tmp/t093-independent-host18-');
const checks=[];
async function exercise(name,{drift=false,lookupDrift=false,mutant=false}={}){
 let source=original;
 if(drift)source=source.replace('    const headers = Object.fromEntries','    this.#upstream.hostname = '+JSON.stringify(wrong)+';\n    const headers = Object.fromEntries');
 if(mutant){const altered=source.replace('if (this.#upstream.hostname !== this.#hostname)','if (false)').replace('if (hostname !== this.#hostname)','if (false)');assert.notEqual(altered,source);source=altered;}
 const wire=[];let handler,status;
 const server=new EventEmitter();server.listen=(_port,_host,ready)=>queueMicrotask(ready);server.address=()=>({port:49123});server.close=done=>done();
 const send=(url,options,respond)=>{
   const entry={target:url.hostname,started:false};wire.push(entry);
   const stream=new PassThrough();stream.resume();stream.setTimeout=()=>stream;
   let denied=false;
   options.lookup(lookupDrift?wrong:url.hostname,{},(error,address,family)=>{
      if(error){denied=true;queueMicrotask(()=>stream.emit('error',error));return;}
      assert.equal(address,'203.0.113.91');assert.equal(family,4);entry.started=true;
   });
   stream.on('finish',()=>{if(denied)return;const response=Readable.from(['{}']);response.statusCode=200;response.headers={};respond(response);});
   return stream;
 };
 const ctx=vm.createContext({URL,Buffer,setTimeout,clearTimeout});
 const imports={'node:http':{createServer:callback=>{handler=callback;return server},request:send},'node:https':{request:send},'node:fs':fs,'node:path':path,'node:net':net,'./gates/core.ts':{Refusal:class extends Error{}},'./claudeLoginFacts.ts':facts};
 const module=new vm.SourceTextModule(stripTypeScriptTypes(source),{context:ctx});
 await module.link(async spec=>new vm.SyntheticModule(Object.keys(imports[spec]),function(){for(const [key,value] of Object.entries(imports[spec]))this.setExport(key,value);},{context:ctx}));
 await module.evaluate();
 const token='synthetic-'+randomUUID();
 const relay=await module.namespace.ClaudeForwarder.start({directory:path.join(journalRoot,name),upstream_url:'https://'+configured,upstream_address:'203.0.113.91',port:0,access_token:token,secrets:[token]});
 const req=Readable.from(['{"sentinel":"'+nonce+'"}']);req.method='POST';req.url='/v1/messages';req.headers={authorization:'Bearer '+token,host:wrong};
 const response=new Writable({write(_data,_enc,done){done();}});response.headersSent=false;response.writeHead=code=>{status=code;response.headersSent=true;return response};
 const ended=new Promise((resolve,reject)=>{response.once('finish',resolve);response.once('error',reject)});
 handler(req,response);await ended;await relay.close();
 const records=fs.readFileSync(path.join(journalRoot,name,'requests.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
 assert.deepEqual(records.map(row=>row.kind),['request','outcome']);
 if(drift||lookupDrift){
    assert.equal(wire.filter(row=>row.started).length,0,'unconfigured destination must not start transport');
    assert.equal(status,502,'host drift must be rejected');
    assert.equal(records[1].error,'upstream_host_mismatch');
 }else{assert.equal(wire.length,1);assert.equal(wire[0].target,configured,'incoming Host must not replace configured target');assert.equal(status,200);}
 return {configured,wrong,wire,status,recorded_error:records[1].error};
}
for(const [name,args] of [['fresh_configured_incoming_host_ignored',{}],['fresh_wrong_target',{drift:true}],['fresh_wrong_lookup',{lookupDrift:true}]]){
 try{checks.push({case:name,status:'PASS',detail:await exercise(name,args)})}
 catch(error){checks.push({case:name,status:'FAIL',error:error.message})}
}
try{await exercise('host_guard_removed_mutant',{drift:true,mutant:true});checks.push({case:'host_guard_removed_mutant',status:'FAIL',error:'mutant accepted'});}
catch(error){assert.match(error.message,/host drift must be rejected|unconfigured destination must not start transport/);checks.push({case:'host_guard_removed_mutant',status:'PASS',rejected_by_business_assertion:error.message});}
const result={candidate:'e5b8329e4f7d0c8104b7e666c346531357612372',scope:'L1 actual forwarding handler; supplied transport only, no network',nonce,journalRoot,checks,status:checks.every(row=>row.status==='PASS')?'PASS':'FAIL'};
fs.writeFileSync(new URL('./host-result.json',import.meta.url),JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({status:result.status,checks:checks.length}));process.exitCode=result.status==='PASS'?0:2;
