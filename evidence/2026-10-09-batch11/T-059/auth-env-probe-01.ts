// No SDK query, provider startup, login, or model request occurs in this probe.
import { join } from "node:path";
import { mkdirSync, writeFileSync } from "node:fs";

const fork = process.env.T059_FORK!;
const root = process.env.T059_PROBE_ROOT!;
const { buildClaudeInstanceProcessEnv } = await import(
  join(fork, "apps/server/src/provider/claudeEnvironment.ts")
);
const { resolveClaudeCredentialsPaths } = await import(
  join(fork, "apps/server/src/provider/claudeProcessEnv.ts")
);
for (const name of ["os-home", "provider-home", "config", "secure-storage"])
  mkdirSync(join(root, name), { recursive: true, mode: 0o700 });

// All inherited and explicit credential values are synthetic sentinels.
const baseEnvironment = {
  HOME: join(root, "os-home"),
  ANTHROPIC_API_KEY: "ambient-synthetic-key",
  CLAUDE_CODE_OAUTH_TOKEN: "ambient-synthetic-token",
  CLAUDE_CONFIG_DIR: join(root, "ambient-config"),
};
const cases = [
  { label: "explicit-empty-home", selected: undefined },
  {
    label: "explicit-api-key",
    selected: {
      ANTHROPIC_API_KEY: "selected-synthetic-key",
      CLAUDE_CONFIG_DIR: join(root, "config"),
      CLAUDE_SECURESTORAGE_CONFIG_DIR: join(root, "secure-storage"),
    },
  },
  {
    label: "explicit-oauth-token-technical-only",
    selected: { CLAUDE_CODE_OAUTH_TOKEN: "selected-synthetic-token" },
  },
];
const result = cases.map(({ label, selected }) => {
  const env = buildClaudeInstanceProcessEnv(join(root, "provider-home"), selected, {
    baseEnvironment,
    homeDir: join(root, "os-home"),
    isolationRootDir: join(root, "native-home"),
    platform: "darwin",
  });
  const paths = resolveClaudeCredentialsPaths({ env, homeDir: env.HOME });
  if (!paths.every((path: string) => path.startsWith(root + "/")))
    throw new Error("Credential lookup escaped the owned probe root");
  if (label === "explicit-empty-home" && (env.ANTHROPIC_API_KEY || env.CLAUDE_CODE_OAUTH_TOKEN))
    throw new Error("Ambient credentials crossed the explicit account boundary");
  if (label === "explicit-api-key" && env.ANTHROPIC_API_KEY !== "selected-synthetic-key")
    throw new Error("Explicit API key was removed");
  return {
    label,
    HOME: env.HOME,
    CLAUDE_CONFIG_DIR: env.CLAUDE_CONFIG_DIR ?? null,
    CLAUDE_SECURESTORAGE_CONFIG_DIR: env.CLAUDE_SECURESTORAGE_CONFIG_DIR ?? null,
    explicit_api_key_present: env.ANTHROPIC_API_KEY === "selected-synthetic-key",
    explicit_oauth_token_present: env.CLAUDE_CODE_OAUTH_TOKEN === "selected-synthetic-token",
    ambient_key_present: env.ANTHROPIC_API_KEY === "ambient-synthetic-key",
    credential_file_lookup_paths: paths,
  };
});
writeFileSync(process.env.T059_PROBE_OUTPUT!, JSON.stringify({
  status: "PASS",
  proves: "Application environment construction with synthetic credentials only",
  does_not_prove: "CLI login, Keychain access, real authentication, or model behavior",
  real_model_turns: 0,
  sdk_query_calls: 0,
  cases: result,
}, null, 2) + "\n", { flag: "wx", mode: 0o600 });
console.log("PASS: synthetic environment probe; model turns = 0");
