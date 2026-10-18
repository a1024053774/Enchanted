// Actual C cleanup callback with supplied signal/receipt timing; no process or network access.
// Failure modes: receipt precedes process exit; EPERM persists; group stays alive;
// receipt is absent; another query error occurs; EPERM is mistaken for ESRCH.
import assert from "node:assert/strict";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { stripTypeScriptTypes } from "node:module";
import { join } from "node:path";
import { randomInt } from "node:crypto";
import { finishChain } from "./t093_chain_evidence.ts";

const output=process.argv[2],source=process.argv[3]??new URL("./test_t093_login_chain.ts",import.meta.url);
assert(!existsSync(output),"preserve earlier evidence");
const text=readFileSync(source,"utf8"),start=text.indexOf("  const gone="),end=text.indexOf("  const steps=",start);
const stepStart=text.indexOf('    {name:"upstream_shutdown_unconfirmed",',end),stepEnd=text.indexOf('\n    {name:',stepStart+1);
assert(start>=0&&end>start&&stepStart>end&&stepEnd>stepStart,"actual_shutdown_callback_required");
const code=stripTypeScriptTypes(text.slice(start,end))+"return ("+text.slice(stepStart,stepEnd).trim().replace(/,$/,"")+");";
const instantiate=new Function("process","existsSync","writeFileSync","file","wait","root","testServices","join",code);
const checks:any[]=[];
for(const sample of [
  {name:"receipt_before_exit_permission_window",signals:["EPERM","EPERM","ESRCH"],receipt:true,pass:true,queries:3},
  {name:"receipt_before_exit_alive_window",signals:["alive","ESRCH"],receipt:true,pass:true,queries:2},
  {name:"already_exited",signals:["ESRCH"],receipt:true,pass:true,queries:1},
  {name:"permanent_permission_denial",signals:["EPERM"],receipt:true,pass:false,error:"upstream_exit_unconfirmed"},
  {name:"group_still_alive",signals:["alive"],receipt:true,pass:false,error:"upstream_exit_unconfirmed"},
  {name:"missing_endpoint_receipt",signals:["ESRCH"],receipt:false,pass:false,error:"fixture_file_deadline",queries:0},
  {name:"unexpected_query_error",signals:["EINVAL"],receipt:true,pass:false,error:"EINVAL",queries:1},
]){
  let queries=0,elapsed=0,absenceObserved=false,removed=false;
  const group=randomInt(100000,900000),root="/private/tmp/t093-supplied-shutdown-"+group;
  const observations:string[]=[],publications:any[]=[],calls:string[]=[];
  const result:any={status:"INCOMPLETE",primary_failure:"missing_raw_request_must_be_detected",cleanup_failures:[]};
  try{
    const step=instantiate({kill:(identity:number,signal:number)=>{
      assert.equal(identity,-group,"probe_must_target_registered_group");assert.equal(signal,0,"probe_must_be_read_only");
      const value=sample.signals[Math.min(queries++,sample.signals.length-1)];observations.push(value);
      if(value==="alive")return true;
      if(value==="ESRCH")absenceObserved=true;
      throw Object.assign(new Error(value),{code:value});
    }},()=>false,(path:string,value:string,options:any)=>{
      assert.equal(path,join(root,"U/stop"));assert.equal(value,"\n");assert.equal(options.flag,"wx");calls.push("stop");
    },async(path:string)=>{
      assert.equal(path,join(root,"U/closed.json"));calls.push("closed");
      if(!sample.receipt)throw new Error("fixture_file_deadline");return {pgrp:group};
    },async(test:()=>boolean,name:string,timeout:number)=>{
      assert.equal(timeout,5000,"original_exit_deadline_must_remain");
      while(!test()){elapsed+=1000;if(elapsed>timeout)throw new Error(name);}
    },root,{U:{pgrp:group}},join);
    const writer:any={publish:(value:any)=>publications.push(structuredClone(value))};
    await finishChain(result,writer,[step],async()=>({all_exited:absenceObserved}),()=>{removed=true;return true;});
    assert.equal(result.primary_failure,"missing_raw_request_must_be_detected","cleanup_must_preserve_business_failure");
    assert.equal(publications[0].phase,"cleanup_pending","primary_must_precede_shutdown");
    assert.equal(publications[0].primary_failure,result.primary_failure);
    assert.equal(result.status,"INCOMPLETE","mutation_must_not_become_PASS");
    assert.deepEqual(calls,["stop","closed"],"endpoint_receipt_must_be_required");
    if(sample.pass){
      assert.deepEqual(result.cleanup_failures,[],"transient_query_denial_must_wait_for_ESRCH");
      assert(absenceObserved&&removed,"receipt_and_ESRCH_both_required_before_removal");
    }else{
      assert(result.cleanup_failures.includes("upstream_shutdown_unconfirmed"),"unconfirmed_shutdown_must_fail");
      assert.equal(result.cleanup_errors[0].message,sample.error,"shutdown_failure_must_remain_specific");
      assert.equal(removed,false,"unconfirmed_writer_must_block_removal");
    }
    if(sample.queries!==undefined)assert.equal(queries,sample.queries,"query_must_continue_until_ESRCH");
    checks.push({name:sample.name,status:"PASS",observations,elapsed,cleanup_failures:result.cleanup_failures});
  }catch(error){checks.push({name:sample.name,status:"FAIL",business_failure:(error as Error).message.split("\n")[0],observations});}
}
const status=checks.every(row=>row.status==="PASS")?"PASS":"FAIL";
writeFileSync(output,JSON.stringify({status,scope:"actual C shutdown callback and finishChain with supplied signal/receipt timing; no OS queries/services/auth",checks},null,2)+"\n",{flag:"wx",mode:0o600});
console.log(JSON.stringify({status,checks:checks.length}));process.exitCode=status==="PASS"?0:2;
