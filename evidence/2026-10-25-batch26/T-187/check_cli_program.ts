// T-187 审查第二轮 F1：npm 安装的 CLI 在进程表里是 `node <path>/<cli>`。期望来自审查发现与 ticket（嵌套时取最近的 CLI）。
// 失败方式：经 node 运行的 CLI 认不出；非运行时程序的第二个参数被误认（vim agy）；没登记的程序被认成 CLI；嵌套时没取最近的。
// 用法：node <本文件> <workbench/src/terminalClis.ts 的路径>
const { cliProgram, commandCli } = await import(process.argv[2]);
const cases: [string, unknown, unknown][] = [
  ["node 运行的 claude", cliProgram(["/opt/homebrew/bin/node", "/opt/homebrew/lib/node_modules/@anthropic-ai/claude-code/bin/claude", "--plugin-dir", "x"]), "claude"],
  ["原生 opencode", cliProgram(["/Users/u/.opencode/bin/opencode", "--standalone"]), "opencode"],
  ["vim agy 不算", cliProgram(["/usr/bin/vim", "agy"]), undefined],
  ["没登记的程序", cliProgram(["/bin/sleep", "30"]), undefined],
  ["嵌套：node 运行的 claude 在 opencode 里，取最近的 claude",
    commandCli({ CLAUDECODE: "1", OPENCODE_SESSION_ID: "s" }, () => [["/bin/zsh", "-c", "a2a"], ["node", "/x/bin/claude"], ["/y/opencode"], ["/bin/zsh"]]), "claude"],
  ["嵌套：opencode 在 node 运行的 claude 里，取最近的 opencode",
    commandCli({ CLAUDECODE: "1", OPENCODE_SESSION_ID: "s" }, () => [["/bin/zsh"], ["/y/opencode", "--standalone"], ["node", "/x/bin/claude"]]), "opencode"],
];
let failed = 0;
for (const [name, got, want] of cases) { const ok = got === want; failed += ok ? 0 : 1; console.log(`${ok ? "PASS" : "FAIL"} ${name}: ${String(got)}`); }
console.log(failed ? `INCOMPLETE ${failed}/${cases.length}` : `PASS ${cases.length}/${cases.length}`);
process.exit(failed ? 1 : 0);
