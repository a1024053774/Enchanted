// T-184: the CLIs Enchanted's project-terminal shims wrap (terminal/bin), and how a running one shows it came through
// its shim. The fact is the process's own argv: the shim always adds these launch arguments. A CLI started by its real
// path or another alias lacks them: no plugin, no hooks, so no turn states or role records. New CLIs join here.
export const shimWiring: Record<string, (argv: string[]) => boolean> = {
  claude: argv => argv.some((arg, index) => arg === "--plugin-dir" && (argv[index + 1] ?? "").endsWith("/plugin/enchanted-a2a")),
  // The hook commands name the a2a shim through the terminal's environment, unexpanded in the argument itself.
  codex: argv => argv.some(arg => arg.includes('$A2A_TERMINAL_BIN/a2a')),
};
