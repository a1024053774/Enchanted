// Isolated serialization boundary: no listen, DNS, auth source or upstream.
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { randomUUID } from "node:crypto";
import { ClaudeForwarder } from "../src/claudeForwarder.ts";
const root=mkdtempSync("/private/tmp/t093-journal-unit-");
const secret="synthetic-method-"+randomUUID(),numberSecret="1234567890123456";
let relay:any;
try{
 relay=new (ClaudeForwarder as any)({directory:join(root,"journal"),upstream_url:"http://127.0.0.1:9",upstream_address:"127.0.0.1",port:0,access_token:secret,secrets:[secret,numberSecret]});
 relay.record({kind:"request",sequence:1,method:secret,path:"/v1/messages",body_bytes_declared:Number(numberSecret)});
 const bytes=readFileSync(relay.ledger,"utf8");
 const exposed=[secret,numberSecret].filter(value=>bytes.includes(value)).length;
 let parseable=true;try{JSON.parse(bytes.trim());}catch{parseable=false;}
 const report={status:exposed===0&&parseable?"PASS":"INCOMPLETE",scope:"actual journal serialization only; no listening socket, auth source or network",credential_values_exposed:exposed,parseable_json:parseable};
 writeFileSync(process.argv[2],JSON.stringify(report,null,2)+"\n",{flag:"wx"});
 console.log(JSON.stringify(report));process.exitCode=report.status==="PASS"?0:2;
}finally{await relay?.close();rmSync(root,{recursive:true});}
