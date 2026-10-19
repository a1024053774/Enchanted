// Actual forwarder HTTP handler, supplied transport only; no sockets/DNS/CLI/auth source.
import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import { mkdtempSync, readFileSync, rmSync, writeFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { PassThrough, Readable, Writable } from 'node:stream';
import { stripTypeScriptTypes } from 'node:module';
import * as vm from 'node:vm';
import { randomUUID } from 'node:crypto';
import { isIP } from 'node:net';
import * as facts from '../src/claudeLoginFacts.ts';

const output=process.argv[2],source=readFileSync(process.argv[3]??new URL('../src/claudeForwarder.ts',import.meta.url),'utf8');
assert(!existsSync(output),'preserve earlier result');
const checks:any[]=[];
for(const kind of ['configured','incoming_host_ignored','non_configured_target','lookup_hostname_mismatch','redirect_not_followed']){
 const root=mkdtempSync('/private/tmp/t093-host-unit-'),token='synthetic-host-'+randomUUID(),wire:any[]=[];
 let relay:any,handler:any,observedStatus:number|undefined;
 try{
  let text=source;
  if(kind==='non_configured_target'){
   // Supply a wrong attempted target at the real pre-connect boundary. The
   // configured hostname captured during construction must remain unchanged.
   const anchor='    const headers = Object.fromEntries';
   assert.equal(text.split(anchor).length,2,'one_actual_transport_boundary_required');
   text=text.replace(anchor,'    this.#upstream.hostname = "127.0.0.2";\n'+anchor);
  }
  const server:any=new EventEmitter();server.listen=(_p:any,_h:any,ready:any)=>queueMicrotask(ready);server.address=()=>({port:57119});server.close=(done:any)=>done();
  const send=(url:URL,options:any,respond:any)=>{
   const connection={hostname:url.hostname,host_header_present:Object.hasOwn(options.headers,'host'),path:options.path,started:false};wire.push(connection);
   const client:any=new PassThrough();client.resume();client.setTimeout=()=>client;
   let lookupError:any;
   // Drive the supplied lookup, but never resolve or open a real connection.
   // Node bypasses lookup for literal IPs; the pre-transport host guard must cover them.
   if(isIP(url.hostname))connection.started=true;
   else options.lookup(kind==='lookup_hostname_mismatch'?'other.fixture.invalid':url.hostname,{},(error:any,address:string,family:number)=>{
    if(error){lookupError=error;queueMicrotask(()=>client.emit('error',error));return;}
    assert.equal(address,'127.0.0.1');assert.equal(family,4);connection.started=true;
   });
   client.on('finish',()=>{
    if(lookupError)return;
    const response:any=Readable.from([Buffer.from('{}')]);response.statusCode=kind==='redirect_not_followed'?302:200;
    response.headers=kind==='redirect_not_followed'?{location:'https://other.fixture.invalid/v1/messages'}:{};
    respond(response);
   });return client;
  };
  const context=vm.createContext({URL,Buffer,setTimeout,clearTimeout});
  const exports:any={
   'node:http':{createServer:(callback:any)=>{handler=callback;return server;},request:send},
   'node:https':{request:send},'node:fs':await import('node:fs'),'node:path':await import('node:path'),'node:net':await import('node:net'),
   './gates/core.ts':{Refusal:class extends Error{code:string;constructor(code:string){super(code);this.code=code;}}},'./claudeLoginFacts.ts':facts,
  };
  const module=new vm.SourceTextModule(stripTypeScriptTypes(text),{context});
  await module.link(async name=>{const values=exports[name];assert(values,'unexpected dependency');return new vm.SyntheticModule(Object.keys(values),function(){for(const key of Object.keys(values))this.setExport(key,values[key]);},{context});});
  await module.evaluate();
  relay=await (module.namespace as any).ClaudeForwarder.start({directory:join(root,'journal'),upstream_url:'https://configured.fixture.invalid/',upstream_address:'127.0.0.1',port:0,access_token:token,secrets:[token]});
  const body=Buffer.from('{"messages":[]}'),request:any=Readable.from([body]);
  request.method='POST';request.url='/v1/messages';request.headers={authorization:'Bearer '+token,'content-length':String(body.length),host:kind==='incoming_host_ignored'?'incoming.fixture.invalid':'configured.fixture.invalid'};
  const response:any=new Writable({write(_data,_encoding,done){done();}});
  response.headersSent=false;response.writeHead=(status:number)=>{observedStatus=status;response.headersSent=true;return response;};
  const finished=new Promise<void>((resolve,reject)=>{response.once('finish',resolve);response.once('error',reject);});
  handler(request,response);await finished;await relay.close();relay=null;
  const rows=readFileSync(join(root,'journal/requests.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
  assert.deepEqual(rows.map(row=>row.kind),['request','outcome'],'request_and_outcome_must_be_recorded');
  if(kind==='non_configured_target'||kind==='lookup_hostname_mismatch'){
   assert.equal(wire.filter(row=>row.started).length,0,'non_configured_host_must_not_connect');
   assert.equal(observedStatus,502);assert.equal(rows[1].error,'upstream_host_mismatch','host_denial_must_be_journaled');
  }else{
   assert.equal(wire.length,1,'redirect_must_not_start_another_connection');
   assert.equal(wire[0].hostname,'configured.fixture.invalid','only_configured_host_may_connect');
   assert.equal(wire[0].host_header_present,false,'incoming_Host_must_not_control_target');
   assert.equal(rows[1].status,kind==='redirect_not_followed'?302:200);assert.equal(rows[1].error,null);
  }
  assert.equal(facts.credentialHits(JSON.stringify(rows),[token]),0,'journal_must_not_include_credentials');
  checks.push({case:kind,status:'PASS',transport_calls:wire.length,connections_started:wire.filter(row=>row.started).length,recorded_error:rows[1].error});
 }catch(error){checks.push({case:kind,status:'FAIL',business_failure:(error as Error).message.split('\n')[0]});}
 finally{if(relay)await relay.close();rmSync(root,{recursive:true});}
}
const status=checks.every(row=>row.status==='PASS')?'PASS':'FAIL';
writeFileSync(output,JSON.stringify({status,scope:'actual forwarding handler with supplied network transport; no OS or real network proof',checks},null,2)+'\n',{flag:'wx',mode:0o600});
console.log(JSON.stringify({status,checks:checks.length}));process.exitCode=status==='PASS'?0:2;
