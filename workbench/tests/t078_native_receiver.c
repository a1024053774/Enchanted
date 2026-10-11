/* Deterministic terminal byte receiver, never a vendor CLI or model.
 * A native binary lets the production ps check verify the actual foreground
 * executable. Only a minimal Codex-shaped session/turn log is synthesized.
 * The harness requests Stop through numbered files; the inherited launch
 * capability stays in this process and its real hook CLI child environment.
 */
#define _DARWIN_C_SOURCE 1
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/select.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <termios.h>
#include <unistd.h>

static const char *session = "00000000-0078-4000-8000-000000000001";
static const char *home;
static void fail(const char *what) { perror(what); exit(2); }
static void path(char *out, const char *name) {
  if (snprintf(out, PATH_MAX, "%s/%s", home, name) >= PATH_MAX) {
    fprintf(stderr, "Fixture path is too long\n"); exit(2);
  }
}
static FILE *create(const char *name) {
  char file[PATH_MAX]; path(file, name);
  int fd = open(file, O_WRONLY | O_CREAT | O_EXCL, 0600);
  if (fd < 0) fail("create fixture file");
  FILE *stream = fdopen(fd, "w"); if (!stream) fail("fdopen"); return stream;
}
static void finish(FILE *stream) { if (fflush(stream) || fsync(fileno(stream)) || fclose(stream)) fail("flush fixture file"); }
static void run_child(const char *prefix, int fd, char *const argv[]) {
  char name[80];
  snprintf(name, sizeof name, "%s.stdout", prefix); FILE *out = create(name);
  snprintf(name, sizeof name, "%s.stderr", prefix); FILE *err = create(name);
  pid_t child = fork(); if (child < 0) fail("fork hook");
  if (!child) {
    if (dup2(fd, STDIN_FILENO) < 0 || dup2(fileno(out), STDOUT_FILENO) < 0 || dup2(fileno(err), STDERR_FILENO) < 0) fail("dup hook");
    close(fd);
    execv(argv[0], argv);
    fail("exec fixture child");
  }
  close(fd); int status;
  while (waitpid(child, &status, 0) < 0) { if (errno != EINTR) fail("wait hook"); }
  finish(out); finish(err);
  snprintf(name, sizeof name, "%s.exit.pending", prefix); FILE *result = create(name);
  fprintf(result, "%d\n", WIFEXITED(status) ? WEXITSTATUS(status) : 128 + WTERMSIG(status)); finish(result);
  char pending[PATH_MAX], completed[PATH_MAX]; path(pending, name);
  snprintf(name, sizeof name, "%s.exit", prefix); path(completed, name);
  if (rename(pending, completed)) fail("publish hook completion");
}
static void hook(unsigned n) {
  char name[80], input[PATH_MAX], prefix[40]; snprintf(name, sizeof name, "hook-%u.json", n); path(input, name);
  int fd = open(input, O_RDONLY); if (fd < 0) fail("open fixture hook");
  snprintf(prefix, sizeof prefix, "hook-%u", n);
  char *argv[] = {getenv("A2A_NODE"), getenv("A2A_CLI"), "--state", getenv("A2A_STATE"),
    "signal", "--launch", getenv("A2A_LAUNCH"), NULL};
  run_child(prefix, fd, argv);
}
static void client(unsigned n) {
  char script[PATH_MAX], number[20], prefix[40]; path(script, "worker-client.mjs");
  snprintf(number, sizeof number, "%u", n); snprintf(prefix, sizeof prefix, "client-%u", n);
  int fd = open("/dev/null", O_RDONLY); if (fd < 0) fail("open client stdin");
  char *argv[] = {getenv("A2A_NODE"), script, number, NULL};
  run_child(prefix, fd, argv);
}
int main(int argc, char **argv) {
  if (argc == 2 && !strcmp(argv[1], "--version")) { puts("codex-cli 0.162.1"); return 0; }
  home = getenv("CODEX_HOME"); if (!home) { fprintf(stderr, "Fixture home is required\n"); return 2; }
  char file[PATH_MAX]; path(file, "sessions"); if (mkdir(file, 0700)) fail("create sessions");
  char native_name[100]; snprintf(native_name, sizeof native_name, "sessions/rollout-%s.jsonl", session);
  FILE *native = create(native_name);
  fprintf(native, "{\"type\":\"session_meta\",\"payload\":{\"source\":\"cli\",\"id\":\"%s\"}}\n", session);
  if (fflush(native)) fail("flush native metadata");
  FILE *started = create("receiver-started.json");
  fprintf(started, "{\"pid\":%d,\"fixture\":true,\"model_turns\":0,\"native_session\":\"%s\"}\n", getpid(), session); finish(started);
  struct termios mode; if (tcgetattr(STDIN_FILENO, &mode)) fail("read terminal mode");
  cfmakeraw(&mode); if (tcsetattr(STDIN_FILENO, TCSANOW, &mode)) fail("set terminal mode");
  printf("T078_DETERMINISTIC_RECEIVER_READY\r\n\033[?2004h"); fflush(stdout);
  FILE *received = create("received.bin");
  unsigned turn = 0, hook_number = 1, client_number = 1; int pasting = 0, mouse_mode = 0; char tail[6] = {0};
  for (;;) {
    fd_set set; FD_ZERO(&set); FD_SET(STDIN_FILENO, &set); struct timeval delay = {0, 25000};
    int ready = select(STDIN_FILENO + 1, &set, NULL, NULL, &delay);
    if (ready < 0) { if (errno == EINTR) continue; fail("select terminal"); }
    if (ready) {
      unsigned char data[65536]; ssize_t count = read(STDIN_FILENO, data, sizeof data);
      if (count < 0) fail("read terminal"); if (!count) break;
      if (fwrite(data, 1, (size_t)count, received) != (size_t)count || fflush(received)) fail("save terminal bytes");
      for (ssize_t i = 0; i < count; i++) {
        memmove(tail, tail + 1, 5); tail[5] = (char)data[i];
        if (!memcmp(tail, "\033[200~", 6)) pasting = 1;
        if (!memcmp(tail, "\033[201~", 6)) pasting = 0;
        if (data[i] == '\r' && !pasting) {
          turn++;
          fprintf(native, "{\"type\":\"event_msg\",\"payload\":{\"type\":\"task_started\",\"turn_id\":\"turn-%u\"}}\n", turn);
          if (fflush(native)) fail("flush native turn");
          char name[80]; snprintf(name, sizeof name, "turn-%u.ready", turn); FILE *marker = create(name); finish(marker);
        }
      }
    }
    char name[80]; snprintf(name, sizeof name, "hook-%u.json", hook_number); path(file, name);
    if (!access(file, F_OK)) hook(hook_number++);
    else if (errno != ENOENT) fail("observe fixture hook");
    snprintf(name, sizeof name, "client-%u.request", client_number); path(file, name);
    if (!access(file, F_OK)) client(client_number++);
    else if (errno != ENOENT) fail("observe client request");
    if (!mouse_mode) {
      path(file, "mouse-mode.request");
      if (!access(file, F_OK)) {
        printf("\033[?1000h"); fflush(stdout); mouse_mode = 1;
        FILE *marker = create("mouse-mode.ready"); finish(marker);
      } else if (errno != ENOENT) fail("observe mouse mode request");
    }
  }
  finish(received); finish(native); return 0;
}
