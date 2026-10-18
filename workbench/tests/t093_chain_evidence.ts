import assert from "node:assert/strict";
import { constants, openSync, closeSync, writeFileSync, fsyncSync, linkSync, unlinkSync, renameSync, lstatSync } from "node:fs";
import { randomUUID } from "node:crypto";
import { redactCredentials } from "../src/claudeLoginFacts.ts";

export function errorSummary(error:unknown) {
  const value=error as any;
  // Keep complete values until publication redacts them. Truncating a raw
  // message first could leave a credential prefix that an exact scan misses.
  return {type:value?.name??"Error",message:String(value?.message??error),code:value?.code??null,errno:value?.errno??null,path:value?.path??null,stack:typeof value?.stack==="string"?value.stack:null,
    ...(value?.daemon_response?{daemon_response:value.daemon_response}:{})};
}

export function assertDaemonOk(command:string,response:any) {
  if(response?.ok===true)return;
  const error=Object.assign(new Error(command+"_rejected: "+String(response?.error??"daemon_error_field_missing")),{
    daemon_response:{command,ok:response?.ok??null,error:response?.error??null,details:response?.details??null}
  });
  throw error;
}

export function exclusiveJson(path:string,value:unknown) {
  const temporary=path+".pending-"+randomUUID();
  const fd=openSync(temporary,constants.O_WRONLY|constants.O_CREAT|constants.O_EXCL|constants.O_NOFOLLOW,0o600);
  try {writeFileSync(fd,JSON.stringify(value)+"\n");fsyncSync(fd);}finally{closeSync(fd);}
  try{linkSync(temporary,path);}finally{unlinkSync(temporary);}
}

export class ChainEvidence {
  #identity:{dev:number;ino:number}|undefined;
  #sequence=0;
  path:string;
  #secrets:()=>readonly string[];
  constructor(path:string,secrets:()=>readonly string[]) {this.path=path;this.#secrets=secrets;}
  publish(value:any) {
    const secrets=this.#secrets();
    const encoded=redactCredentials(JSON.stringify({...value,checkpoint_sequence:this.#sequence+1},null,2),secrets)+"\n";
    // Independent guards do not use the production variant enumerator.
    for(const secret of secrets.filter(Boolean)){
      const base=Buffer.from(secret).toString("base64");
      for(const sample of [secret,JSON.stringify(secret).slice(1,-1),encodeURIComponent(secret),base,base.replace(/=+$/,""),Buffer.from(secret).toString("base64url")])
        assert(!encoded.includes(sample),"public_writer_must_remove_credentials");
    }
    const temporary=this.path+".pending-"+randomUUID();
    const fd=openSync(temporary,constants.O_WRONLY|constants.O_CREAT|constants.O_EXCL|constants.O_NOFOLLOW,0o600);
    try{writeFileSync(fd,encoded);fsyncSync(fd);}finally{closeSync(fd);}
    try{
      if(this.#identity){const current=lstatSync(this.path);assert(current.isFile()&&current.dev===this.#identity.dev&&current.ino===this.#identity.ino,"checkpoint_owner_changed");renameSync(temporary,this.path);}
      else linkSync(temporary,this.path);
    }finally{try{unlinkSync(temporary);}catch(error:any){if(error.code!=="ENOENT")throw error;}}
    const current=lstatSync(this.path);this.#identity={dev:current.dev,ino:current.ino};this.#sequence++;
    const published=JSON.parse(encoded);
    const event=JSON.stringify({sequence:this.#sequence,phase:published.phase,primary_failure:published.primary_failure??null,cleanup_failures:published.cleanup_failures??[],fixture_removed:published.fixture_removed??false})+"\n";
    const history=openSync(this.path+".events.jsonl",constants.O_WRONLY|constants.O_NOFOLLOW|(this.#sequence===1?constants.O_CREAT|constants.O_EXCL:constants.O_APPEND),0o600);
    try{writeFileSync(history,event);fsyncSync(history);}finally{closeSync(history);}
  }
}

export async function finishChain(result:any,writer:ChainEvidence,steps:{name:string;run:()=>Promise<void>|void}[],writers:()=>Promise<any>,remove:()=>boolean) {
  result.cleanup_errors??=[];result.fixture_removed=false;result.cleanup_pending=true;result.phase="cleanup_pending";result.status="INCOMPLETE";
  // If this durable publication fails, no cleanup operation may run.
  writer.publish(result);
  for(const step of steps){
    try{await step.run();}
    catch(error){result.cleanup_failures.push(step.name);result.cleanup_errors.push({step:step.name,...errorSummary(error)});}
    writer.publish(result);
  }
  try{result.writer_exit=await writers();}
  catch(error){result.writer_exit={all_exited:false};result.cleanup_failures.push("writer_exit_unconfirmed");result.cleanup_errors.push({step:"writer_exit_unconfirmed",...errorSummary(error)});}
  writer.publish(result);
  if(result.writer_exit.all_exited===true){
    try{result.fixture_removed=remove();if(!result.fixture_removed)result.cleanup_failures.push("fixture_remove_unconfirmed");}
    catch(error){result.cleanup_failures.push("fixture_remove_failed");result.cleanup_errors.push({step:"fixture_remove_failed",...errorSummary(error)});}
  }else result.cleanup_failures.push("fixture_remove_skipped_live_or_unconfirmed_writer");
  result.phase="complete";result.cleanup_pending=false;
  result.status=result.primary_failure||result.cleanup_failures.length||!result.fixture_removed?"INCOMPLETE":"PASS";
  writer.publish(result);
  return result;
}
