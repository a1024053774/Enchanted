const { A2AGates } = await import("/Users/luckye/Documents/Code/synara/packages/a2a-gates/src/core.ts");
const gates = new A2AGates(process.env.T064_CRASH_ROOT!);
try {
  const db = (gates as any).db;
  console.log(JSON.stringify({ settings: gates.rolePermissionSettings(),
    inputs: db.prepare("SELECT data FROM user_inputs").all() }));
} finally { gates.close(); }
