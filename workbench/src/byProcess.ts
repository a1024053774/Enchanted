// T-242, T-246: what a terminal's Claude Code or Codex reported through its hook (a turn state, a native session), kept
// per reporting process, and the process last seen in front. Only the front process's own report is shown, so a report
// from another process (a CLI that exited while its hook was on the way, or one run inside the front one, such as
// `claude -p` from its Bash tool) neither shows on the front one nor replaces what the front one reported. A process is
// its pid and start time: a report that arrived before the front process started came from an earlier process given
// the same pid, also across a daemon restart that rebuilds the reports from the records.
export type Front = { pid: number; started: number }; // started: milliseconds since the epoch

const processAlive = (pid: number) => {
  try { process.kill(pid, 0); return true; } catch (error: any) { return error.code === "EPERM"; }
};

export class ByProcess<T> {
  private byPid = new Map<number, { value: T; at: number }>();
  private front: Front | null = null;
  private alive: (pid: number) => boolean;
  constructor(alive = processAlive) { this.alive = alive; }
  // at: when the report arrived (milliseconds since the epoch).
  note(pid: number, value: T, at = Date.now()) { this.byPid.set(pid, { value, at }); this.prune(); }
  foreground(front: Front | null) { this.front = front; this.prune(); }
  get(pid: number): T | undefined { return this.byPid.get(pid)?.value; }
  shown(): T | null {
    const report = this.front && this.byPid.get(this.front.pid);
    return report && report.at >= this.front!.started ? report.value : null;
  }
  get size() { return this.byPid.size; }
  // An exited process's report goes, and so does an earlier process's under the front pid.
  private prune() {
    for (const [pid, report] of this.byPid)
      if (pid === this.front?.pid ? report.at < this.front.started : !this.alive(pid)) this.byPid.delete(pid);
  }
}
