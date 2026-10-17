import { randomUUID } from "node:crypto";
import { closeSync, constants, fstatSync, openSync, readFileSync, realpathSync, writeFileSync } from "node:fs";
import { isAbsolute } from "node:path";

export type OperatorIdentity = { kind: "operator"; state: string; epoch: string; token: string };

function credentialPath() {
  const path = process.env.A2A_OPERATOR_CREDENTIAL;
  if (!path || !isAbsolute(path)) throw new Error("absolute_operator_credential_path_required");
  return path;
}

// Only the process starting a daemon creates its bootstrap credential. The
// socket never issues this credential, and role strings cannot select it.
export function createOperatorCredential(root: string): string {
  const path = credentialPath();
  const credential: OperatorIdentity = { kind: "operator", state: realpathSync(root), epoch: randomUUID(), token: randomUUID() };
  writeFileSync(path, JSON.stringify(credential) + "\n", { flag: "wx", mode: 0o600 });
  return path;
}

export function readOperatorCredential(root: string): OperatorIdentity | undefined {
  if (!process.env.A2A_OPERATOR_CREDENTIAL) return undefined;
  const fd = openSync(credentialPath(), constants.O_RDONLY | constants.O_NOFOLLOW);
  try {
    const stat = fstatSync(fd);
    if (!stat.isFile() || (stat.mode & 0o077) !== 0 || stat.uid !== process.getuid!()) {
      throw new Error("private_operator_credential_required");
    }
    const value = JSON.parse(readFileSync(fd, "utf8"));
    if (value.kind !== "operator" || value.state !== realpathSync(root) ||
        typeof value.epoch !== "string" || !value.epoch || typeof value.token !== "string" || !value.token) {
      throw new Error("invalid_operator_credential");
    }
    return value;
  } finally { closeSync(fd); }
}
