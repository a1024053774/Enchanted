/* Native fixture CLI, zero model calls. The daemon checks this real foreground
 * executable. Minimal Codex session metadata permits the ordinary managed-pane
 * path; all input is captured verbatim, independently of the daemon's records. */
#define _DARWIN_C_SOURCE 1
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/select.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <termios.h>
#include <unistd.h>
static const char *home;
static void fail(const char *name) { perror(name); exit(2); }
static void path(char *out, const char *name) {
  if (snprintf(out, PATH_MAX, "%s/%s", home, name) >= PATH_MAX) exit(2);
}
static FILE *create(const char *name) {
  char file[PATH_MAX]; path(file, name);
  int fd = open(file, O_WRONLY | O_CREAT | O_EXCL, 0600);
  if (fd < 0) fail(name);
  FILE *stream = fdopen(fd, "w"); if (!stream) fail("fdopen"); return stream;
}
int main(int argc, char **argv) {
  if (argc == 2 && !strcmp(argv[1], "--version")) { puts("T145 fixture receiver 1 (no model)"); return 0; }
  home = getenv("CODEX_HOME"); if (!home) return 2;
  char file[PATH_MAX], cwd[PATH_MAX]; path(file, "sessions");
  if (mkdir(file, 0700) || !getcwd(cwd, sizeof cwd)) fail("sessions/cwd");
  FILE *native = create("sessions/rollout-00000000-0145-4000-8000-000000000001.jsonl");
  fputs("{\"type\":\"session_meta\",\"payload\":{\"source\":\"cli\",\"id\":\"00000000-0145-4000-8000-000000000001\",\"cwd\":\"", native);
  for (const char *p = cwd; *p; p++) { if (*p == '"' || *p == '\\') fputc('\\', native); fputc(*p, native); }
  fputs("\"}}\n", native); if (fclose(native)) fail("native log");
  struct termios mode; if (tcgetattr(0, &mode)) fail("tcgetattr");
  cfmakeraw(&mode); if (tcsetattr(0, TCSANOW, &mode)) fail("tcsetattr");
  FILE *received = create("received.bin");
  /* Exercise the existing startup path, without changing production readiness. */
  printf("› 1. Open restricted\r\n\x1b[?2004h"); fflush(stdout);
  int enabled = 0;
  for (;;) {
    fd_set set; FD_ZERO(&set); FD_SET(0, &set); struct timeval delay = {0, 25000};
    int ready = select(1, &set, NULL, NULL, &delay);
    if (ready < 0) { if (errno == EINTR) continue; fail("select"); }
    if (ready) {
      unsigned char data[65536]; ssize_t count = read(0, data, sizeof data);
      if (count < 0) fail("read"); if (!count) break;
      if (fwrite(data, 1, (size_t)count, received) != (size_t)count || fflush(received)) fail("save bytes");
    }
    if (!enabled) {
      path(file, "enable-mouse");
      if (!access(file, F_OK)) {
        /* Any-motion + SGR, plus focus mode (the existing renderer intercepts
         * focus mode; that contract remains in force). */
        printf("\x1b[?1003;1006;1004hT145_MOUSE_READY\r\n"); fflush(stdout);
        struct winsize size; if (ioctl(0, TIOCGWINSZ, &size)) fail("terminal size");
        FILE *marker = create("mouse-ready");
        fprintf(marker, "{\"cols\":%u,\"rows\":%u}\n", size.ws_col, size.ws_row);
        fclose(marker); enabled = 1;
      } else if (errno != ENOENT) fail("enable marker");
    }
  }
  return fclose(received) ? 2 : 0;
}
