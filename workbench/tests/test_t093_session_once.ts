// Synthetic ownership unit. No daemon, OS profile, network or auth source.
import assert from "node:assert/strict";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, realpathSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { randomUUID } from "node:crypto";
import { ClaudeLogin } from "../src/claudeLogin.ts";
const root=realpathSync(mkdtempSync('/private/tmp/t093-once-')),privateRoot=realpathSync(mkdtempSync('/private/tmp/a2a-claude-login-once-'));
const previous={...process.env};
const upstreamPort=Number(process.argv[3]??443);
try{
 for(const path of ['repo','state','audit','F','D'])mkdirSync(join(root,path));
 for(const path of ['home/.claude','tmp','shell','metadata'])mkdirSync(join(privateRoot,path),{recursive:true});
 const exe=join(root,'version-status');writeFileSync(exe,"#!/bin/sh\nif [ \"$1\" = \"--version\" ]; then printf '2.1.304 (Claude Code)\\n'; else printf '{\"loggedIn\":true}\\n'; fi\n",{mode:0o700});
 const input:any={schema:1,authentication:'normal-login',version:'2.1.304',launch:randomUUID(),task:'unit',state:join(root,'state'),executable:exe};
 const session={schema:1,c_root_pid:process.pid,repo:join(root,'repo'),deadline:Date.now()/1000+60,auth_original_reads:1,manifest:input,private_root:privateRoot,real_home:'/synthetic-home',forward_port:52101,upstream_port:upstreamPort,audit_directory:join(root,'audit'),forwarder_directory:join(root,'F'),metadata_directory:join(root,'D'),profiles:{C:'not-applied-in-this-unit'}};
 const save=(path:string,value:unknown)=>writeFileSync(path,JSON.stringify(value),{mode:0o600});
 save(join(privateRoot,'session.json'),session);save(join(privateRoot,'services.json'),{F:{pid:100001,bootstrap_exit:0},D:{pid:100002,bootstrap_exit:0}});
 save(join(root,'F/ready.json'),{pid:100001,url:'http://127.0.0.1:52101'});save(join(root,'D/ready.json'),{pid:100002});save(join(privateRoot,'metadata/before.json'),{});
 save(join(privateRoot,'home/.claude/.credentials.json'),{claudeAiOauth:{accessToken:'synthetic-once-'+randomUUID()}});
 process.env.A2A_CLAUDE_LOGIN_SESSION=join(privateRoot,'session.json');process.env.A2A_PROFILE_PROCESS_LOG=join(root,'audit/processes.jsonl');process.env.NODE_OPTIONS='';
 const result=await Promise.allSettled([ClaudeLogin.prepare(input,join(root,'repo')),ClaudeLogin.prepare(input,join(root,'repo'))]);
 assert.equal(result.filter(x=>x.status==='fulfilled').length,1,'exactly_one_start_must_consume_prepared_session');
 const rejected=result.find(x=>x.status==='rejected') as PromiseRejectedResult;
 assert.equal(rejected.reason.code,'prepared_login_already_consumed');assert.equal(existsSync(join(root,'D/abort')),false,'loser_must_not_clean_up_winner_resources');
 assert.equal(readFileSync(join(privateRoot,'consumed'),'utf8'),input.launch);
 mkdirSync(join(root,'audit/forwarder/journal'),{recursive:true});writeFileSync(join(root,'audit/forwarder/journal/requests.jsonl'),'');save(join(root,'F/preflight-counters.json'),{received:0,forwarded:0,journal_failure:null});
 const owner=(result.find(x=>x.status==='fulfilled') as PromiseFulfilledResult<ClaudeLogin>).value;
 await owner.preflight({argv:['cli','/synthetic-home/injected']});
 const initial=JSON.parse(readFileSync(join(root,'audit/preflight.json'),'utf8'));
 assert.equal(initial.phase,'before_cli_input');assert.equal(initial.counts.model_requests,0);assert.equal(initial.credential_scan.hits,0);assert.equal(initial.inventory.comparison_pending,true);assert.equal(initial.launch_home_references.length,1);
 assert.deepEqual(initial.network_boundary,{os_host_filter:false,os_remote_ports:[upstreamPort],application_host_lock:true},'facts_must_disclose_actual_profile_port');
 writeFileSync(process.argv[2],JSON.stringify({status:'PASS',scope:'synthetic ownership/preflight only; fake PID and counter files, no service or OS evidence',upstream_port:upstreamPort,checks:['exactly one concurrent prepare succeeds','second prepare fails before acquiring or cleaning shared resources','input-before checkpoint records counts, references, scan and pending inventory','facts disclose no OS host filter, actual TCP port and application host lock']},null,2)+'\n',{flag:'wx'});
 console.log('{"status":"PASS","checks":4}');
}finally{
 process.env=previous;rmSync(privateRoot,{recursive:true});rmSync(root,{recursive:true});
}
