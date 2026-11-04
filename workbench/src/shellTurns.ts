// T-242: the turn states a terminal's Claude Code or Codex reported through its hook, kept per reporting process, and
// the process last seen in front. Only the front process's own state is shown, so a hook from another process (one that
// exited while its hook was still on the way) neither shows on the front one nor erases what the front one reported.
// Kept in memory only, so an ordinary terminal's turns stay out of the records (T-133).
export type ShellHookTurn = { cli: string; pid: number; state: "running" | "idle" | "waiting_user_answer" };

const processAlive = (pid: number) => {
  try { process.kill(pid, 0); return true; } catch (error: any) { return error.code === "EPERM"; }
};

export class ShellTurns {
  private byPid = new Map<number, ShellHookTurn>();
  private front: number | null = null;
  private alive: (pid: number) => boolean;
  constructor(alive = processAlive) { this.alive = alive; }
  note(turn: ShellHookTurn) { this.byPid.set(turn.pid, turn); this.prune(); }
  foreground(pid: number | null) { this.front = pid; this.prune(); }
  shown(): { cli: string; state: ShellHookTurn["state"] } | null {
    const turn = this.front === null ? undefined : this.byPid.get(this.front);
    return turn ? { cli: turn.cli, state: turn.state } : null;
  }
  get size() { return this.byPid.size; }
  // An exited process's state goes, so a later process given the same pid does not start with it.
  private prune() { for (const pid of this.byPid.keys()) if (pid !== this.front && !this.alive(pid)) this.byPid.delete(pid); }
}
