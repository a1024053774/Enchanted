// T-187 test double for agy and opencode in a project terminal: a native program (so the process's argv[0] and start
// environment read like the real ones) that reports turn states the way the real CLIs do (T-187 facts.md):
// agy only with AGY_CLI_OSC7501=on, opencode always; agy ends a turn with done then idle, opencode with clear then idle.
// One line of input is one step: request <role>, work, ask, perm, done, split, launch, exit.
// Build: cc -O2 -o <dir>/agy t187_fake_cli.c && ln <dir>/agy <dir>/opencode
#include <libgen.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static int reports;
static const char *app;

static void report(const char *fields) {
  if (!reports) return;
  printf("\033]7501;%s:app=%s\007", fields, app);
  fflush(stdout);
}

int main(int argc, char **argv) {
  int agy = strcmp(basename(argv[0]), "agy") == 0;
  app = agy ? "antigravity" : "opencode";
  const char *osc = getenv("AGY_CLI_OSC7501");
  reports = agy ? osc && strcmp(osc, "on") == 0 : 1;
  printf("%s fake ready\n", agy ? "agy" : "opencode");
  report("state=idle");
  char line[4096];
  while (fgets(line, sizeof line, stdin)) {
    line[strcspn(line, "\r\n")] = 0;
    if (!strcmp(line, "request executor") || !strcmp(line, "request ideation")) {
      report("state=working");
      // opencode names its session in the environment of the commands it runs (env-oc.txt); agy's commands keep the shim's.
      if (!agy) setenv("OPENCODE_SESSION_ID", "ses_t187fake", 1);
      char command[64];
      snprintf(command, sizeof command, "a2a request %s", line + 8);
      int status = system(command);
      printf("request exit %d\n", status);
      report(agy ? "state=done:msg=b2s=" : "state=clear:id=ses_t187fake");
      report("state=idle");
    } else if (!strcmp(line, "work")) report("state=working");
    else if (!strcmp(line, "ask")) report("state=blocked:kind=question:msg=5Y+q5LiA6aKY");
    else if (!strcmp(line, "perm")) report("state=blocked:kind=permission:msg=QXBwcm92ZQ==");
    else if (!strcmp(line, "done")) { report(agy ? "state=done:msg=b2s=" : "state=clear:id=ses_t187fake"); report("state=idle"); }
    else if (!strcmp(line, "split")) {
      // One report written in two pieces, some time apart: the terminal reads it in two chunks.
      if (reports) { printf("\033]7501;state=wor"); fflush(stdout); usleep(400000); printf("king:app=%s\007", app); fflush(stdout); }
    } else if (!strcmp(line, "launch")) {
      const char *out = getenv("T187_LAUNCH_OUT");
      FILE *file = out ? fopen(out, "w") : NULL;
      if (file) {
        for (int i = 0; i < argc; i++) fprintf(file, "argv\t%s\n", argv[i]);
        const char *content = getenv("OPENCODE_CONFIG_CONTENT"), *shim = getenv("A2A_SHIM");
        fprintf(file, "config\t%s\nshim\t%s\nosc\t%s\n", content ? content : "", shim ? shim : "", osc ? osc : "");
        fclose(file);
      }
      printf("launch written\n");
    } else if (!strcmp(line, "exit")) break;
    fflush(stdout);
  }
  return 0;
}
