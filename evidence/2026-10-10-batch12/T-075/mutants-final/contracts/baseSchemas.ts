// Derived from Synara, MIT License.
// Copyright (c) 2026 T3 Tools Inc.
// Copyright (c) 2026 Emanuele Di Pietro
// See ../../LICENSE.synara for the full permission notice.

import { Schema } from "/Users/luckye/Documents/Code/a2a/workbench/node_modules/effect/dist/index.js";

export const TrimmedString = Schema.Trim;
export const TrimmedNonEmptyString = TrimmedString.check(Schema.isNonEmpty());

export const NonNegativeInt = Schema.Int.check(Schema.isGreaterThanOrEqualTo(0));
/**
 * Construct a branded identifier. Enforces non-empty trimmed strings
 */
const makeEntityId = <Brand extends string>(brand: Brand) =>
  TrimmedNonEmptyString.pipe(Schema.brand(brand));

export const ThreadId = makeEntityId("ThreadId");
export type ThreadId = typeof ThreadId.Type;
export const ProjectId = makeEntityId("ProjectId");
export type ProjectId = typeof ProjectId.Type;
const PROVIDER_SLUG_MAX_CHARS = 64;
const PROVIDER_SLUG_PATTERN = /^[A-Za-z][A-Za-z0-9_-]*$/;
const ProviderSlug = TrimmedNonEmptyString.check(
  Schema.isMaxLength(PROVIDER_SLUG_MAX_CHARS),
  Schema.isPattern(PROVIDER_SLUG_PATTERN),
);

export const ProviderInstanceId = ProviderSlug;
export type ProviderInstanceId = typeof ProviderInstanceId.Type;

