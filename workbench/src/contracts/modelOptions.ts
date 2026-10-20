// Derived from Synara, MIT License.
// Copyright (c) 2026 T3 Tools Inc.
// Copyright (c) 2026 Emanuele Di Pietro
// See ../../LICENSE.synara for the full permission notice.

import { Schema } from "effect";
import { TrimmedNonEmptyString } from "./baseSchemas.ts";
export const PI_THINKING_LEVEL_OPTIONS = [
  "off",
  "minimal",
  "low",
  "medium",
  "high",
  "xhigh",
  "max",
] as const;
export type PiThinkingLevel = (typeof PI_THINKING_LEVEL_OPTIONS)[number];
// `auto` is an OMP thinking sentinel (not an effort level): it maps to the
// `thinking` config option's Auto choice, which no model catalog emits as an
// effort but role selectors (`model:auto`) may pin.
export const OMP_THINKING_LEVEL_OPTIONS = [
  "off",
  "auto",
  "minimal",
  "low",
  "medium",
  "high",
  "xhigh",
  "max",
] as const;
export type OmpThinkingLevel = (typeof OMP_THINKING_LEVEL_OPTIONS)[number];
// Union of every Grok CLI ladder. Per-model capabilities pick a subset:
// grok-build keeps none/low/medium/high, Grok 4.5 drops none, Grok 4.6 adds xhigh.
export const GROK_REASONING_EFFORT_OPTIONS = ["none", "low", "medium", "high", "xhigh"] as const;
export type GrokReasoningEffort = (typeof GROK_REASONING_EFFORT_OPTIONS)[number];
export const CodexModelOptions = Schema.Struct({
  // Codex runtime discovery can expose early-access effort values outside the built-in enum.
  reasoningEffort: Schema.optional(TrimmedNonEmptyString),
  fastMode: Schema.optional(Schema.Boolean),
});
export type CodexModelOptions = typeof CodexModelOptions.Type;

export const ClaudeModelOptions = Schema.Struct({
  thinking: Schema.optional(Schema.Boolean),
  effort: Schema.optional(TrimmedNonEmptyString),
  fastMode: Schema.optional(Schema.Boolean),
  autoCompactWindow: Schema.optional(Schema.String),
  // Legacy persisted field. Normalization migrates this to autoCompactWindow.
  contextWindow: Schema.optional(Schema.String),
});
export type ClaudeModelOptions = typeof ClaudeModelOptions.Type;

export const AntigravityModelOptions = Schema.Struct({
  reasoningEffort: Schema.optional(TrimmedNonEmptyString),
});
export type AntigravityModelOptions = typeof AntigravityModelOptions.Type;

export const OpenCodeModelOptions = Schema.Struct({
  variant: Schema.optional(TrimmedNonEmptyString),
  agent: Schema.optional(TrimmedNonEmptyString),
});
export type OpenCodeModelOptions = typeof OpenCodeModelOptions.Type;

export const PiModelOptions = Schema.Struct({
  thinkingLevel: Schema.optional(Schema.Literals(PI_THINKING_LEVEL_OPTIONS)),
});
export type PiModelOptions = typeof PiModelOptions.Type;
export const OmpModelOptions = Schema.Struct({
  thinkingLevel: Schema.optional(Schema.Literals(OMP_THINKING_LEVEL_OPTIONS)),
});
export type OmpModelOptions = typeof OmpModelOptions.Type;

export const CursorModelOptions = Schema.Struct({
  reasoningEffort: Schema.optional(TrimmedNonEmptyString),
  fastMode: Schema.optional(Schema.Boolean),
  thinking: Schema.optional(Schema.Boolean),
  contextWindow: Schema.optional(Schema.String),
});
export type CursorModelOptions = typeof CursorModelOptions.Type;

export const GrokModelOptions = Schema.Struct({
  reasoningEffort: Schema.optional(Schema.Literals(GROK_REASONING_EFFORT_OPTIONS)),
});
export type GrokModelOptions = typeof GrokModelOptions.Type;

export const DroidModelOptions = Schema.Struct({
  reasoningEffort: Schema.optional(TrimmedNonEmptyString),
});
export type DroidModelOptions = typeof DroidModelOptions.Type;

export const DevinModelOptions = Schema.Struct({
  reasoningEffort: Schema.optional(TrimmedNonEmptyString),
  fastMode: Schema.optional(Schema.Boolean),
  thinking: Schema.optional(Schema.Boolean),
  contextWindow: Schema.optional(TrimmedNonEmptyString),
  // Devin's ACP command accepts a concrete model UID at process start. This
  // is populated from runtime discovery when an abstract effort/context
  // selection needs to resolve to a specific variant.
  modelVariant: Schema.optional(TrimmedNonEmptyString),
});
export type DevinModelOptions = typeof DevinModelOptions.Type;

export const DEFAULT_MODEL_BY_PROVIDER = {
  codex: "gpt-6-astra",
  claudeAgent: "claude-sonnet-5",
  cursor: "auto",
  devin: "adaptive",
  antigravity: "Gemini 3.5 Flash",
  grok: "grok-4.6",
  droid: "claude-opus-4-8",
  opencode: "openai/gpt-5",
};
