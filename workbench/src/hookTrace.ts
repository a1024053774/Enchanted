import { randomUUID } from "node:crypto";
import { appendFileSync, mkdirSync, realpathSync, renameSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";

// Opt-in P1 diagnostics. Never capture environment variables or credentials.
export class HookTrace {
  directory: string; launch: string; started: number;
  static start(state: string, launch: string, stdin: Buffer): HookTrace | undefined {
    const requested=process.env.A2A_HOOK_TRACE_DIR;
    if (!requested) return undefined;
    const root=dirname(realpathSync(state)), trace=realpathSync(requested);
    if (!root.startsWith("/private/tmp/t078-2-") || trace!==join(root,"hooks") || process.env.A2A_LAUNCH!==launch) throw new Error("invalid_hook_trace_binding");
    return new HookTrace(trace,launch,stdin);
  }
  constructor(root: string, launch: string, stdin: Buffer) {
    this.directory=join(root,randomUUID());this.launch=launch;this.started=Date.now();
    mkdirSync(this.directory,{mode:0o700});
    writeFileSync(join(this.directory,"stdin.bin"),stdin,{flag:"wx",mode:0o600});
    for(const n of ["stdout.bin","stderr.bin"])writeFileSync(join(this.directory,n),"",{flag:"wx",mode:0o600});
    writeFileSync(join(this.directory,"started.json"),JSON.stringify({launch,pid:process.pid,started_at:new Date(this.started).toISOString()}),{flag:"wx",mode:0o600});
  }
  stdout(bytes: string) { appendFileSync(join(this.directory,"stdout.bin"),bytes); }
  stderr(bytes: string) { appendFileSync(join(this.directory,"stderr.bin"),bytes); }
  finish(code: number) {
    writeFileSync(join(this.directory,"finished.tmp"),JSON.stringify({launch:this.launch,pid:process.pid,exit_code:code,
      finished_at:new Date().toISOString(),duration_ms:Date.now()-this.started}),{flag:"wx",mode:0o600});
    renameSync(join(this.directory,"finished.tmp"),join(this.directory,"finished.json"));
    return code;
  }
}
