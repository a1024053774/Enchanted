// The actual F process checks its OS boundary, then serves via the product.
import { constants, existsSync, fstatSync, lstatSync, openSync, closeSync, unlinkSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { randomUUID } from "node:crypto";
import { createConnection, createServer } from "node:net";
import { spawnSync } from "node:child_process";
import { runForwarder } from "../src/claudeForwarderProcess.ts";
import { observeHomeReadBoundary } from "./t093_home_read_boundary.ts";
import { fileURLToPath } from "node:url";
const sessionPath = process.argv[2], session = JSON.parse(readFileSync(sessionPath,"utf8"));
const fixture = JSON.parse(readFileSync(join(session.private_root,"fixture.json"),"utf8"));
const directory = session.forwarder_directory;
const save=(name:string,value:unknown)=>writeFileSync(join(directory,name),JSON.stringify(value)+"\n",{flag:"wx",mode:0o600});
const boot=JSON.parse(readFileSync(join(session.private_root,"bootstrap/F.json"),"utf8"));
save("host.json",{pid:process.pid,ppid:process.ppid,pgrp:boot.pgrp,profile:"F"});
function attempt(home:string) {
  const path=join(home,".a2a-t093-deny-"+randomUUID().replaceAll("-",""));
  const value:any={path,exclusive_create:true,created:false,deleted:false,denied:false};
  try {
    const fd=openSync(path,constants.O_WRONLY|constants.O_CREAT|constants.O_EXCL|constants.O_NOFOLLOW,0o600);
    value.created=true;
    let own;try{own=fstatSync(fd);}finally{closeSync(fd);}
    const now=lstatSync(path);
    if(now.ino!==own.ino||now.dev!==own.dev)throw new Error("exclusive_file_owner_changed");
    unlinkSync(path);value.deleted=true;
  } catch(error:any) {value.errno=error.errno;value.denied=!value.created&&["EPERM","EACCES"].includes(error.code);}
  value.absent_after=!existsSync(path);return value;
}
const home=attempt(session.real_home), outside=attempt(fixture.root);
const homeReadBoundary=observeHomeReadBoundary(session.real_home,fixture.read_boundary_target,fileURLToPath(import.meta.url));
const until=Date.now()+15000;
while(!existsSync(join(fixture.root,"U/ready.json"))) {if(Date.now()>until)throw new Error("upstream_start_deadline");await new Promise(r=>setTimeout(r,30));}
const unconfigured=await new Promise<any>(resolve=>{
 const socket=createConnection({host:"127.0.0.1",port:fixture.other_port});
 socket.setTimeout(1000,()=>{socket.destroy();resolve({denied:false,code:"TIMEOUT"});});
 socket.once("error",error=>resolve({denied:["EPERM","EACCES"].includes((error as any).code),code:(error as any).code}));
 socket.once("connect",()=>{socket.destroy();resolve({denied:false,code:null});});
});
const otherBind=await new Promise<any>(resolve=>{const server=createServer();server.once("error",error=>resolve({denied:["EPERM","EACCES"].includes((error as any).code),code:(error as any).code}));server.listen(fixture.bind_probe_port,"127.0.0.1",()=>server.close(()=>resolve({denied:false,code:null})));});
const fork=spawnSync("/usr/bin/true",[],{stdio:"ignore"});
save("guards.json",{pid:process.pid,ppid:process.ppid,pgrp:boot.pgrp,profile:"F",real_home_write:home,home_read_boundary:homeReadBoundary,outside_records_write:outside,unconfigured_upstream:unconfigured,other_listener:otherBind,fork:{denied:["EPERM","EACCES"].includes((fork.error as any)?.code),code:(fork.error as any)?.code??null}});
await runForwarder(sessionPath);
