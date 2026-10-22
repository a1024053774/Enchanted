#!/bin/zsh
# T-126 candidate 1 unit evidence: run from workbench/. The credential test runs on the candidate, then on five
# known-bad copies of src/desktopCredentials.ts that this script makes in a temporary directory.
E=../evidence/2026-10-22-batch20/T-126/candidate-1/unit
M=$(mktemp -d)
node --experimental-strip-types tests/test_t126_desktop_credentials.ts $E/credentials-green.json > $E/credentials-green.log 2>&1; print "credentials-green exit=$?" >> $E/exits.txt
python3 - $M <<'PY'
import sys
src = open('src/desktopCredentials.ts').read()
mutants = {
  # The isolated credential folder inside the data directory.
  'credentials-in-data-dir': ('return explicitState ? `${state}-credentials`', 'return explicitState ? `${state}/credentials`'),
  # Old credential files are left in the data directory.
  'old-credentials-kept': ('  for (const name of readdirSync(state)) if (credentialName.test(name)) unlinkSync(join(state, name));\n', ''),
  # Cleanup happens only on the start that moves the credential, so an interrupted migration never finishes.
  'cleanup-only-on-first-move': ('    saveDesktopConnection(directory, moved);\n  }\n  for (const name of readdirSync(state)) if (credentialName.test(name)) unlinkSync(join(state, name));\n  if (existsSync(old)) unlinkSync(old);\n',
    '    saveDesktopConnection(directory, moved);\n    for (const name of readdirSync(state)) if (credentialName.test(name)) unlinkSync(join(state, name));\n    if (existsSync(old)) unlinkSync(old);\n  }\n'),
  'moved-world-readable': ('writeFileSync(moved, readFileSync(current), { flag: "wx", mode: 0o600 });', 'writeFileSync(moved, readFileSync(current), { flag: "wx", mode: 0o644 });'),
  # A descriptor may name a credential in any directory.
  'descriptor-any-directory': ('dirname(credential) !== directory || !credentialName.test(credential.slice(directory.length + 1))', '!credentialName.test(credential.split("/").pop()!)'),
}
for name, (old, new) in mutants.items():
    assert src.count(old) == 1, name
    open(f'{sys.argv[1]}/{name}.ts', 'w').write(src.replace(old, new))
PY
for m in credentials-in-data-dir old-credentials-kept cleanup-only-on-first-move moved-world-readable descriptor-any-directory; do
  node --experimental-strip-types tests/test_t126_desktop_credentials.ts $E/credentials-$m.json $M/$m.ts > $E/credentials-$m.log 2>&1; print "credentials-$m exit=$?" >> $E/exits.txt
done
# Regressions: transport and relay suites (the transport gained requestAt).
O=$(mktemp -d)
for t in test_relay_core test_t078_controller_relay test_t078_relay_role; do
  node --experimental-strip-types tests/$t.ts $O/$t > $E/$t.log 2>&1; print "$t exit=$?" >> $E/exits.txt
done
