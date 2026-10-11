// Derived from Synara, MIT License.
// Copyright (c) 2026 T3 Tools Inc.
// Copyright (c) 2026 Emanuele Di Pietro
// See ../../LICENSE.synara for the full permission notice.

import { Effect, Schema, SchemaTransformation } from "/Users/luckye/Documents/Code/a2a/workbench/node_modules/effect/dist/index.js";
import {
  AntigravityModelOptions,
  ClaudeModelOptions,
  CodexModelOptions,
  CursorModelOptions,
  DevinModelOptions,
  DroidModelOptions,
  GrokModelOptions,
  OpenCodeModelOptions,
  OmpModelOptions,
  PiModelOptions,
  DEFAULT_MODEL_BY_PROVIDER,
} from "./modelOptions.ts";
import { ProviderInstanceId, TrimmedNonEmptyString } from "./baseSchemas.ts";
export const ProviderKind = Schema.Literals([
  "codex",
  "claudeAgent",
  "cursor",
  "antigravity",
  "grok",
  "droid",
  "opencode",
  "pi",
  "devin",
  "omp",
]);
export type ProviderKind = typeof ProviderKind.Type;

/**
 * Providers that no longer exist as `ProviderKind` members but may survive in
 * persisted data. Renamed providers map to their successor; removed providers
 * map to the runtime that hosted their sessions. Add an entry here whenever a
 * provider is renamed or removed so persisted payloads keep decoding.
 */
export const LEGACY_PROVIDER_MIGRATIONS: Readonly<Record<string, ProviderKind>> = {
  gemini: "antigravity",
  kilo: "opencode",
};

const ProviderInstanceIdForDriver = (_provider: ProviderKind) =>
  Schema.optional(ProviderInstanceId);

const isProviderKindValue = Schema.is(ProviderKind);

function inferProviderFromInstanceId(instanceId: string): ProviderKind | undefined {
  if (isProviderKindValue(instanceId)) {
    return instanceId;
  }

  const lowerInstanceId = instanceId.toLowerCase();
  if (lowerInstanceId.startsWith("claude")) {
    return "claudeAgent";
  }
  if (lowerInstanceId.startsWith("codex")) {
    return "codex";
  }
  if (lowerInstanceId.startsWith("cursor")) {
    return "cursor";
  }
  if (lowerInstanceId.startsWith("antigravity") || lowerInstanceId.startsWith("gemini")) {
    return "antigravity";
  }
  if (lowerInstanceId.startsWith("grok")) {
    return "grok";
  }
  if (lowerInstanceId.startsWith("droid")) {
    return "droid";
  }
  if (lowerInstanceId.startsWith("kilo")) {
    return "opencode";
  }
  if (lowerInstanceId.startsWith("opencode") || lowerInstanceId.startsWith("open_code")) {
    return "opencode";
  }
  if (lowerInstanceId.startsWith("omp")) {
    return "omp";
  }
  if (lowerInstanceId.startsWith("pi")) {
    return "pi";
  }
  if (lowerInstanceId.startsWith("devin")) {
    return "devin";
  }
  return undefined;
}

function inferProviderFromModel(model: string): ProviderKind {
  const lowerModel = model.toLowerCase();
  if (
    lowerModel.includes("claude") ||
    lowerModel.includes("sonnet") ||
    lowerModel.includes("opus") ||
    lowerModel.includes("haiku")
  ) {
    return "claudeAgent";
  }
  if (lowerModel.includes("gemini")) {
    return "antigravity";
  }
  if (lowerModel.includes("grok")) {
    return "grok";
  }
  if (lowerModel.includes("devin")) {
    return "devin";
  }
  if (lowerModel.includes("opencode") || lowerModel.includes("open_code")) {
    return "opencode";
  }
  if (lowerModel.includes("kilo")) {
    return "opencode";
  }
  if (lowerModel.includes("cursor")) {
    return "cursor";
  }
  if (lowerModel.startsWith("pi/") || lowerModel.includes("/pi/")) {
    return "pi";
  }
  return "codex";
}

function inferProviderForModelSelection(input: {
  readonly provider?: unknown;
  readonly instanceId?: unknown;
  readonly model?: unknown;
}): ProviderKind | undefined {
  if (isProviderKindValue(input.provider)) {
    return input.provider;
  }
  if (typeof input.provider === "string") {
    const migrated = LEGACY_PROVIDER_MIGRATIONS[input.provider];
    if (migrated) {
      return migrated;
    }
  }
  if (typeof input.instanceId === "string") {
    const provider = inferProviderFromInstanceId(input.instanceId);
    if (provider) {
      return provider;
    }
  }
  return typeof input.model === "string" ? inferProviderFromModel(input.model) : undefined;
}

function defaultModelForProvider(provider: ProviderKind): string {
  // OMP has no static default model; an empty model fails the per-provider
  // schema below instead of inventing one.
  if (provider === "omp") return "";
  return provider === "pi" ? "openai/gpt-5.5" : DEFAULT_MODEL_BY_PROVIDER[provider];
}

export const CodexModelSelection = Schema.Struct({
  provider: Schema.Literal("codex"),
  instanceId: ProviderInstanceIdForDriver("codex"),
  model: TrimmedNonEmptyString,
  options: Schema.optional(CodexModelOptions),
});
export type CodexModelSelection = typeof CodexModelSelection.Type;

export const ClaudeModelSelection = Schema.Struct({
  provider: Schema.Literal("claudeAgent"),
  instanceId: ProviderInstanceIdForDriver("claudeAgent"),
  model: TrimmedNonEmptyString,
  options: Schema.optional(ClaudeModelOptions),
  supportsAutoMode: Schema.optional(Schema.Boolean),
});
export type ClaudeModelSelection = typeof ClaudeModelSelection.Type;

export const CursorModelSelection = Schema.Struct({
  provider: Schema.Literal("cursor"),
  instanceId: ProviderInstanceIdForDriver("cursor"),
  model: TrimmedNonEmptyString,
  options: Schema.optional(CursorModelOptions),
});
export type CursorModelSelection = typeof CursorModelSelection.Type;

export const AntigravityModelSelection = Schema.Struct({
  provider: Schema.Literal("antigravity"),
  instanceId: ProviderInstanceIdForDriver("antigravity"),
  model: TrimmedNonEmptyString,
  options: Schema.optional(AntigravityModelOptions),
});
export type AntigravityModelSelection = typeof AntigravityModelSelection.Type;

export const GrokModelSelection = Schema.Struct({
  provider: Schema.Literal("grok"),
  instanceId: ProviderInstanceIdForDriver("grok"),
  model: TrimmedNonEmptyString,
  options: Schema.optional(GrokModelOptions),
});
export type GrokModelSelection = typeof GrokModelSelection.Type;

export const DroidModelSelection = Schema.Struct({
  provider: Schema.Literal("droid"),
  instanceId: ProviderInstanceIdForDriver("droid"),
  model: TrimmedNonEmptyString,
  options: Schema.optional(DroidModelOptions),
});
export type DroidModelSelection = typeof DroidModelSelection.Type;

export const OpenCodeModelSelection = Schema.Struct({
  provider: Schema.Literal("opencode"),
  instanceId: ProviderInstanceIdForDriver("opencode"),
  model: TrimmedNonEmptyString,
  options: Schema.optional(OpenCodeModelOptions),
});
export type OpenCodeModelSelection = typeof OpenCodeModelSelection.Type;

export const PiModelSelection = Schema.Struct({
  provider: Schema.Literal("pi"),
  instanceId: ProviderInstanceIdForDriver("pi"),
  model: TrimmedNonEmptyString,
  options: Schema.optional(PiModelOptions),
});
export type PiModelSelection = typeof PiModelSelection.Type;
export const OmpModelSelection = Schema.Struct({
  provider: Schema.Literal("omp"),
  instanceId: ProviderInstanceIdForDriver("omp"),
  model: TrimmedNonEmptyString,
  options: Schema.optional(OmpModelOptions),
});
export type OmpModelSelection = typeof OmpModelSelection.Type;

export const DevinModelSelection = Schema.Struct({
  provider: Schema.Literal("devin"),
  instanceId: ProviderInstanceIdForDriver("devin"),
  model: TrimmedNonEmptyString,
  options: Schema.optional(DevinModelOptions),
});
export type DevinModelSelection = typeof DevinModelSelection.Type;

const ModelSelectionByProvider = Schema.Union([
  CodexModelSelection,
  ClaudeModelSelection,
  CursorModelSelection,
  DevinModelSelection,
  AntigravityModelSelection,
  GrokModelSelection,
  DroidModelSelection,
  OpenCodeModelSelection,
  PiModelSelection,
  OmpModelSelection,
]);

// Keep persisted inputs loose so malformed or mixed legacy drafts reach the
// transform; the discriminated target union remains the canonical contract.
const ModelSelectionJsonValue: Schema.Codec<unknown, unknown> = Schema.Json.pipe(
  Schema.decodeTo(
    Schema.Unknown,
    SchemaTransformation.transform({
      decode: (value): unknown => value,
      encode: (value): Schema.Json => value as Schema.Json,
    }),
  ),
);

const ModelSelectionSource = Schema.Struct({
  provider: Schema.optional(ModelSelectionJsonValue),
  instanceId: Schema.optional(ModelSelectionJsonValue),
  model: Schema.optional(ModelSelectionJsonValue),
  options: Schema.optional(ModelSelectionJsonValue),
  supportsAutoMode: Schema.optional(ModelSelectionJsonValue),
});

export const ModelSelection: Schema.Codec<typeof ModelSelectionByProvider.Type, unknown> =
  ModelSelectionSource.pipe(
    Schema.decodeTo(
      ModelSelectionByProvider,
      SchemaTransformation.transformOrFail({
        decode: (raw) => {
          const provider = inferProviderForModelSelection(raw) ?? "codex";
          const model =
            typeof raw.model === "string" && raw.model.trim().length > 0
              ? raw.model
              : defaultModelForProvider(provider);
          const instanceId =
            typeof raw.instanceId === "string" && raw.instanceId.trim().length > 0
              ? raw.instanceId.trim()
              : provider;
          const base: Record<string, unknown> = {
            provider,
            instanceId,
            model,
          };
          if (raw.options !== undefined) {
            base.options = raw.options;
          }
          if (raw.supportsAutoMode !== undefined) {
            base.supportsAutoMode = raw.supportsAutoMode;
          }
          return Effect.succeed(base as typeof ModelSelectionByProvider.Encoded);
        },
        encode: (value) => Effect.succeed(value as typeof ModelSelectionSource.Encoded),
      }),
    ),
  );
export type ModelSelection = typeof ModelSelection.Type;

