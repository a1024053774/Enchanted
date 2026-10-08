// Observation only. Original arguments, return values and exceptions propagate.
if (process.env.A2A_TIMING_ENABLE === "1") {
  const fs = require("node:fs");
  const { dlopen, ptr } = require("bun:ffi");
  const clock = dlopen("/usr/lib/libSystem.B.dylib", {
    clock_gettime: { args: ["int", "ptr"], returns: "int" },
  });
  const timespec = new BigInt64Array(2);
  const now = () => {
    if (clock.symbols.clock_gettime(4, ptr(timespec)) !== 0)
      throw new Error("CLOCK_MONOTONIC_RAW observation failed");
    return timespec[0] * 1000000000n + timespec[1];
  };
  const marks = [];
  const mark = (event, detail = {}) => marks.push({
    event, ns: now().toString(), pid: process.pid, ...detail,
  });
  mark("bun_preload_start");
  const util = require("node:util");
  const parseArgs = util.parseArgs;
  util.parseArgs = function (...args) {
    mark("parse_start");
    try { return Reflect.apply(parseArgs, this, args); }
    finally { mark("parse_end"); }
  };
  const sqlite = require("node:sqlite");
  const Database = sqlite.DatabaseSync;
  const paths = new WeakMap();
  const exec = Database.prototype.exec;
  Database.prototype.exec = function (sql, ...args) {
    const file = paths.get(this);
    const kind = file && file.includes("/locks/") ? "lock" : "state";
    const begin = kind === "lock" && sql === "BEGIN IMMEDIATE";
    if (begin) mark("lock_begin_start", { file });
    if (kind === "state" && sql.startsWith("PRAGMA busy_timeout=5000")) mark("state_init_start");
    try {
      const result = Reflect.apply(exec, this, [sql, ...args]);
      if (begin) mark("lock_begin_end", { result: "acquired" });
      return result;
    } catch (error) {
      if (begin) mark("lock_begin_end", { result: "threw", error: String(error) });
      throw error;
    } finally {
      if (kind === "state" && sql.startsWith("PRAGMA busy_timeout=5000")) mark("state_init_end");
    }
  };
  sqlite.DatabaseSync = new Proxy(Database, {
    construct(Target, args, NewTarget) {
      const file = String(args[0]);
      const kind = file.includes("/locks/") ? "lock" : "state";
      mark(kind + "_db_open_start", { file });
      const value = Reflect.construct(Target, args, NewTarget);
      paths.set(value, file);
      mark(kind + "_db_open_end");
      return value;
    },
  });
  const write = process.stdout.write;
  process.stdout.write = function (...args) {
    mark("stdout_write");
    const index = args.length - 1;
    if (typeof args[index] === "function") {
      const callback = args[index];
      args[index] = function (...callbackArgs) {
        mark("stdout_callback");
        return Reflect.apply(callback, this, callbackArgs);
      };
    }
    return Reflect.apply(write, this, args);
  };
  process.on("exit", (code) => {
    mark("bun_exit", { code });
    fs.appendFileSync(process.env.A2A_TIMING_MARKS,
      marks.map(value => JSON.stringify(value) + "\n").join(""), { mode: 0o600 });
  });
  mark("bun_preload_end");
}
