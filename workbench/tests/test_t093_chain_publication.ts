import assert from "node:assert/strict";
import { existsSync, readFileSync, writeFileSync, mkdtempSync, rmSync } from "node:fs";
import { join } from "node:path";
import { randomUUID } from "node:crypto";
const output=process.argv[2],mode=process.argv[3]??"candidate";
assert(!existsSync(output));const checks:any[]=[];
async function check(name:string,run:()=>unknown|Promise<unknown>){try{const value=await run();checks.push({name,status:"PASS",detail:value});}catch(error){checks.push({name,status:"FAIL",business_failure:(error as Error).message.split("\n")[0]});}}
if(mode==="legacy"){
 await check("primary exists before root deletion",()=>{
  const source=readFileSync(process.argv[4]??new URL("./test_t093_login_chain.ts",import.meta.url),"utf8");
  const start=source.indexOf("  rmSync(root,{recursive:true});"),end=source.indexOf("  console.log(",start);
  assert(start>=0&&end>start,"legacy_cleanup_tail_required");
  let published:any;let before=false;
  const remove=()=>{before=published?.primary_failure==="business_probe";throw Object.assign(new Error("synthetic ENOTEMPTY"),{code:"ENOTEMPTY",errno:66});};
  try{new Function("rmSync","existsSync","result","root","redactCredentials","secrets","writeFileSync","output","let removed=false;"+source.slice(start,end))(remove,()=>true,{primary_failure:"business_probe"},"synthetic root",(value:any)=>value,[],(_path:any,value:string)=>{published=JSON.parse(value);},"synthetic output");}catch{}
  assert(before,"primary_JSON_must_exist_before_any_cleanup");return {published_before_cleanup:before};
 });
}else{
 const {ChainEvidence,finishChain,errorSummary}=await import("./t093_chain_evidence.ts");
 for(const kind of ["remove_error","writer_alive","success","step_error"]){
  await check(kind,async()=>{
   const directory=mkdtempSync("/private/tmp/t093-evidence-unit-"),root=join(directory,"fixture"),target=join(directory,"result.json");
   const secret='synthetic-publication/"\\-'+randomUUID();writeFileSync(root,"owned fixture");
   let calls=0;const result:any={status:"INCOMPLETE",primary_failure:kind==="success"?null:"business_probe",error_summary:errorSummary(new Error("x".repeat(15990)+secret)),cleanup_failures:[],fixture_removed:false};
   const writer=new ChainEvidence(target,()=>[secret]);
   const prior=()=>assert.equal(JSON.parse(readFileSync(target,"utf8")).primary_failure,result.primary_failure,"primary_JSON_must_exist_before_any_cleanup");
   try{
    await finishChain(result,writer,[{name:"stop_probe",run:async()=>{prior();if(kind==="step_error")throw new Error("secondary probe");}}],async()=>({all_exited:kind!=="writer_alive"}),()=>{prior();calls++;if(kind==="remove_error")throw Object.assign(new Error("synthetic ENOTEMPTY"),{code:"ENOTEMPTY",errno:66,path:root});rmSync(root);return true;});
    const saved=JSON.parse(readFileSync(target,"utf8"));assert(!readFileSync(target,"utf8").includes(secret));assert(!saved.error_summary.message.includes('synthetic-publication'),"message_must_be_redacted_before_truncation");
    assert.equal(saved.primary_failure,result.primary_failure);assert.equal(saved.cleanup_pending,false);
    if(kind==="success")assert.equal(saved.status,"PASS");else assert.equal(saved.status,"INCOMPLETE");
    if(kind==="remove_error")assert(saved.cleanup_failures.includes("fixture_remove_failed")&&saved.cleanup_errors.some((v:any)=>v.code==="ENOTEMPTY"));
    if(kind==="writer_alive")assert.equal(calls,0,"live_writer_must_prevent_deletion");
    if(kind==="step_error")assert(saved.cleanup_failures.includes("stop_probe"));
    return {primary_preserved:true,remove_calls:calls,status:saved.status};
   }finally{rmSync(directory,{recursive:true});}
  });
 }
 await check("existing evidence is preserved",()=>{
  const directory=mkdtempSync("/private/tmp/t093-evidence-owner-"),target=join(directory,"result.json");writeFileSync(target,'{"prior":"keep"}');
  try{assert.throws(()=>new ChainEvidence(target,()=>["synthetic-private"]).publish({primary_failure:"new"}));assert.equal(readFileSync(target,"utf8"),'{"prior":"keep"}');return {prior_preserved:true};}finally{rmSync(directory,{recursive:true});}
 });
}
const status=checks.every(v=>v.status==="PASS")?"PASS":"FAIL";
writeFileSync(output,JSON.stringify({status,scope:"local synthetic evidence writer and cleanup callbacks; no OS profile/real service/auth",checks},null,2)+"\n",{flag:"wx",mode:0o600});
console.log(JSON.stringify({status,checks:checks.length}));process.exitCode=status==="PASS"?0:2;
