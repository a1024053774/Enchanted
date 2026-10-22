// Derived from Synara, MIT License.
// Copyright (c) 2026 T3 Tools Inc.
// Copyright (c) 2026 Emanuele Di Pietro
// See ../../LICENSE.synara for the full permission notice.

import { Schema } from "effect";
import { NonNegativeInt, ProjectId, ThreadId, TrimmedNonEmptyString } from "./baseSchemas.ts";

// T-123: a task id is `<project>+<name>`, each part a gate id.
export const taskIdPattern = /^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\+[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$/;

export const A2AMemberRole = Schema.Literals(["controller", "worker", "reviewer", "monitor"]);
export type A2AMemberRole = typeof A2AMemberRole.Type;

export const A2ATaskMembership = Schema.Struct({
  taskId: TrimmedNonEmptyString.check(Schema.isPattern(taskIdPattern)),
  projectId: ProjectId,
  title: TrimmedNonEmptyString.check(Schema.isMaxLength(240)),
  revision: NonNegativeInt,
  members: Schema.Array(
    Schema.Struct({
      threadId: ThreadId,
      role: A2AMemberRole,
      endedAt: Schema.optional(Schema.String),
    }),
  ),
});
export type A2ATaskMembership = typeof A2ATaskMembership.Type;
