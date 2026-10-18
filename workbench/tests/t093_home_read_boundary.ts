// Only an existing public AGENTS.md is a data-read target. No auth is opened.
import { constants, openSync, closeSync, readSync, lstatSync, realpathSync, readdirSync } from "node:fs";
import { dirname } from "node:path";

export function observeHomeReadBoundary(home:string, target:string, entry:string) {
  const denied=(action:()=>void)=>{
    try { action(); return {denied:false,code:null}; }
    catch(error:any) {
      if(!["EPERM","EACCES"].includes(error.code))throw error;
      return {denied:true,code:error.code};
    }
  };
  const metadata=[home,dirname(target)].map(path=>({path,is_directory:lstatSync(path).isDirectory()}));
  const resolved=realpathSync(entry);
  let bytesRead=0;
  const content=denied(()=>{
    const fd=openSync(target,constants.O_RDONLY|constants.O_NOFOLLOW);
    try {bytesRead=readSync(fd,Buffer.alloc(1),0,1,null);}finally{closeSync(fd);}
  });
  const enumeration=denied(()=>{readdirSync(dirname(target));});
  return {target,metadata,entry_resolved:resolved===entry,content:{...content,bytes_read:bytesRead},ancestor_directory_entries:enumeration};
}
