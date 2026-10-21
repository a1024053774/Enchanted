import { randomUUID } from "node:crypto";
import { Refusal } from "./gates/core.ts";
import type { OrchestrationStore } from "./store.ts";

// T-119/T-121: a CLI the user starts in an ordinary project terminal asks for a
// controller role; it takes effect only after the user approves it in the UI.
// Role requests are append-only events; the current state is derived from them and
// from whether the terminal is still alive in this daemon process.
// The user's approval grants the role; it takes effect only when the asker confirms
// it received the answer, so a role is never active behind an agent's back.
export const requestRoles = ["ideation", "executor"] as const;
export type RequestRole = typeof requestRoles[number];
export type RequestState = "pending" | "granted" | "approved" | "rejected" | "ended";
export const confirmWindowMs = 15_000;
// cli is what the calling process reported about itself: shown to the user, never trusted.
export type RoleRequest = { id: string; launch: string; project: string; role: RequestRole; state: RequestState; cli: string | null;
  requested_at: string; decided_at: string | null; ended_reason: string | null };

const refuse = (condition: unknown, code: string) => { if (!condition) throw new Refusal(code); };

export class RoleRequests {
  private store: OrchestrationStore;
  private alive: (launch: string) => boolean;
  constructor(store: OrchestrationStore, alive: (launch: string) => boolean) {
    this.store = store;
    this.alive = alive;
  }

  all(): RoleRequest[] {
    const roleRequests = new Map<string, RoleRequest>();
    const rows = this.store.db.prepare(`SELECT time,type,launch,data FROM orchestration_events
      WHERE type IN ('role_requested','role_request_decided','role_request_confirmed','role_request_ended') ORDER BY seq`).all();
    for (const row of rows) {
      const data = JSON.parse(String(row.data));
      if (row.type === "role_requested") {
        roleRequests.set(data.role_request, { id: data.role_request, launch: String(row.launch), project: data.project, role: data.role, cli: data.cli,
          state: "pending", requested_at: String(row.time), decided_at: null, ended_reason: null });
        continue;
      }
      const roleRequest = roleRequests.get(data.role_request);
      if (!roleRequest || roleRequest.state === "ended" || roleRequest.state === "rejected") continue;
      if (row.type === "role_request_decided" && roleRequest.state === "pending") {
        roleRequest.state = data.approved ? "granted" : "rejected";
        roleRequest.decided_at = String(row.time);
        if (!data.approved) roleRequest.ended_reason = data.reason ?? null;
      }
      if (row.type === "role_request_confirmed" && roleRequest.state === "granted") roleRequest.state = "approved";
      if (row.type === "role_request_ended") { roleRequest.state = "ended"; roleRequest.ended_reason = data.reason; }
    }
    // A closed terminal or a restarted daemon ends every role request it held.
    for (const roleRequest of roleRequests.values()) {
      if (["pending", "granted", "approved"].includes(roleRequest.state) && !this.alive(roleRequest.launch)) {
        roleRequest.state = "ended"; roleRequest.ended_reason = "terminal_gone";
      }
    }
    return [...roleRequests.values()];
  }
  current(launch: string) {
    return this.all().filter(roleRequest => roleRequest.launch === launch && ["pending", "granted", "approved"].includes(roleRequest.state)).at(-1);
  }
  approved(launch: string) {
    const roleRequest = this.current(launch);
    return roleRequest?.state === "approved" ? roleRequest : undefined;
  }
  request(terminal: { id: string; project: string | null; task: string | null }, role: unknown, cli: unknown) {
    refuse(requestRoles.includes(role as RequestRole), "invalid_role");
    refuse(terminal.project, "project_terminal_required");
    refuse(this.alive(terminal.id), "terminal_gone");
    const held = this.current(terminal.id);
    refuse(!held, held?.state === "pending" ? "request_already_pending" : "role_already_held");
    refuse(!this.holder(terminal.project!, role as RequestRole), "role_taken");
    const roleRequest = randomUUID();
    this.store.event("role_requested", { role_request: roleRequest, role, project: terminal.project,
      cli: cli === "claude" || cli === "codex" ? cli : null }, terminal);
    return this.all().find(row => row.id === roleRequest)!;
  }
  decide(id: unknown, approved: unknown) {
    refuse(typeof approved === "boolean", "invalid_role_decision");
    const roleRequest = this.all().find(row => row.id === id);
    refuse(roleRequest, "unknown_role_request");
    refuse(roleRequest!.state === "pending", "request_not_pending");
    // Approval is checked again here: another terminal may hold the role by now.
    if (approved) refuse(!this.holder(roleRequest!.project, roleRequest!.role), "role_taken");
    this.store.event("role_request_decided", { role_request: roleRequest!.id, approved }, { id: roleRequest!.launch, task: null });
    // A grant nobody confirms in time is ended by an event, timed on this process's
    // monotonic clock rather than the wall clock.
    if (approved) setTimeout(() => {
      const granted = this.all().find(row => row.id === roleRequest!.id);
      if (granted?.state === "granted") this.store.event("role_request_ended", { role_request: granted.id, reason: "not_confirmed" }, { id: granted.launch, task: null });
    }, confirmWindowMs).unref();
    return this.all().find(row => row.id === roleRequest!.id)!;
  }
  confirm(launch: string, id: string) {
    const roleRequest = this.current(launch);
    if (!roleRequest || roleRequest.id !== id || roleRequest.state !== "granted") return undefined;
    this.store.event("role_request_confirmed", { role_request: roleRequest.id }, { id: launch, task: null });
    // One terminal per role and project: the role taking effect settles every other
    // request for it. Until then they stay pending, so an unconfirmed grant loses nobody's request.
    for (const other of this.all().filter(row => row.state === "pending" && row.project === roleRequest.project && row.role === roleRequest.role))
      this.store.event("role_request_decided", { role_request: other.id, approved: false, reason: "role_given_to_other" }, { id: other.launch, task: null });
    return this.all().find(row => row.id === roleRequest.id)!;
  }
  end(launch: string, reason: string) {
    const roleRequest = this.current(launch);
    if (!roleRequest) return undefined;
    this.store.event("role_request_ended", { role_request: roleRequest.id, reason }, { id: launch, task: null });
    return this.all().find(row => row.id === roleRequest.id)!;
  }
  // A request whose asker stopped waiting must not be approved later behind its back.
  withdraw(launch: string, id: string, reason: string) {
    const roleRequest = this.current(launch);
    if (!roleRequest || roleRequest.id !== id || roleRequest.state !== "pending") return undefined;
    this.store.event("role_request_ended", { role_request: roleRequest.id, reason }, { id: launch, task: null });
    return this.all().find(row => row.id === roleRequest.id)!;
  }
  private holder(project: string, role: RequestRole) {
    return this.all().find(roleRequest => roleRequest.project === project && roleRequest.role === role && (roleRequest.state === "granted" || roleRequest.state === "approved"));
  }
}
