// T-187 test double for agy and opencode in a project terminal: a native program (so the process's argv[0] and start
// environment read like the real ones) that reports turn states the way the real CLIs do (T-187 facts.md):
// agy only with AGY_CLI_OSC7501=on, opencode always; agy ends a turn with done then idle, opencode with clear then idle.
// One line of input is one step: request <role>, work, ask, perm, done, split, prefix, launch, leave, exit.
// leave: the CLI ends by itself a few seconds later, after the terminal looked at the line just typed.
// opencode first asks the terminal whether it supports the reports (a bare `?`, oc-01); the terminal does not answer.
// Started by the backend as a managed worker or reviewer (agy with --dangerously-skip-permissions, opencode with
// --standalone --auto; T-187 ready_rev 2), it is managed_main below.
// Build: cc -O2 -o <dir>/agy t187_fake_cli.c && ln <dir>/agy <dir>/opencode
#include <libgen.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <termios.h>
#include <unistd.h>

static int reports;
static const char *app;

static void report(const char *fields) {
  if (!reports) return;
  printf("\033]7501;%s:app=%s\007", fields, app);
  fflush(stdout);
}

// A managed session. agy first reports the sign-in check and then asks to trust the folder as agy 1.4.7 draws it
// (facts.md, agy-01/02); Enter answers with the choice drawn as selected, which is "Yes" unless the file
// $HOME/.t187-trust-no exists. Each pasted task (bracketed paste, then Enter) is one turn: working, the helper
// t187_fake_worker.py next to this program does the task, then the turn's end. The terminal is raw: the line
// discipline would cut a long pasted line.
static int managed_main(int agy, const char *self) {
  char helper[PATH_MAX], command[PATH_MAX * 2 + 64], cwd[PATH_MAX];
  char resolved[PATH_MAX];
  if (!realpath(self, resolved) || !getcwd(cwd, sizeof cwd)) return 2;
  snprintf(helper, sizeof helper, "%s/t187_fake_worker.py", dirname(resolved));
  struct termios raw;
  tcgetattr(0, &raw); cfmakeraw(&raw); tcsetattr(0, TCSANOW, &raw);
  char c;
  if (agy) {
    report("state=blocked:kind=auth:msg=U2lnbiBpbiByZXF1aXJlZA==");
    char marker[PATH_MAX];
    snprintf(marker, sizeof marker, "%s/.t187-trust-no", getenv("HOME"));
    int no = access(marker, F_OK) == 0;
    printf("Accessing workspace:\r\n\r\n%s\r\n\r\nDo you trust the contents of this project?\r\n\r\n"
           "Antigravity CLI requires permission to read, edit, and execute files here.\r\n\r\n%s Yes, I trust this folder\r\n%s No, exit\r\n",
           cwd, no ? " " : ">", no ? ">" : " ");
    report("state=blocked:kind=permission:msg=VHJ1c3QgdGhpcyBmb2xkZXI/");
    while (read(0, &c, 1) == 1 && c != '\r') ;
    if (no) return 1;
    snprintf(command, sizeof command, "/usr/bin/python3 -I '%s' trust '%s'", helper, cwd);
    if (system(command) != 0) return 1;
  }
  report("state=idle");
  for (;;) {
    size_t size = 0, capacity = 65536;
    char *text = malloc(capacity);
    // The paste ends with ESC [ 201 ~; the Enter after it submits.
    while (read(0, &c, 1) == 1) {
      if (size + 1 >= capacity) text = realloc(text, capacity *= 2);
      text[size++] = c;
      if (size >= 6 && !memcmp(text + size - 6, "\033[201~", 6)) break;
    }
    if (size < 6) return 0;
    while (read(0, &c, 1) == 1 && c != '\r') ;
    char prompt[] = "/tmp/t187-prompt-XXXXXX";
    int fd = mkstemp(prompt);
    write(fd, text, size); close(fd); free(text);
    report("state=working");
    snprintf(command, sizeof command, "/usr/bin/python3 -I '%s' work '%s' >/dev/null 2>&1", helper, prompt);
    int status = system(command);
    printf("turn done %d\r\n", status);
    unlink(prompt);
    report(agy ? "state=done:msg=b2s=" : "state=clear:id=ses_t187fake");
    report("state=idle");
  }
}

int main(int argc, char **argv) {
  int agy = strcmp(basename(argv[0]), "agy") == 0;
  app = agy ? "antigravity" : "opencode";
  const char *osc = getenv("AGY_CLI_OSC7501");
  reports = agy ? osc && strcmp(osc, "on") == 0 : 1;
  if (argc == 2 && !strcmp(argv[1], "--version")) { printf(agy ? "1.4.7-t187fake\n" : "opencode v2.1.4-t187fake\n"); return 0; }
  for (int i = 1; i < argc; i++)
    if (!strcmp(argv[i], agy ? "--dangerously-skip-permissions" : "--auto")) return managed_main(agy, argv[0]);
  printf("%s fake ready\n", agy ? "agy" : "opencode");
  if (!agy) { printf("\033]7501;?\007"); fflush(stdout); }
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
    } else if (!strcmp(line, "prefix")) {
      // A report cut inside its opening sequence.
      if (reports) { printf("\033]75"); fflush(stdout); usleep(400000); printf("01;state=working:app=%s\007", app); fflush(stdout); }
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
    } else if (!strcmp(line, "leave")) { sleep(3); break; }
    else if (!strcmp(line, "exit")) break;
    fflush(stdout);
  }
  return 0;
}
