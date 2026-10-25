/* T-174 stand-in CLI. "silent <flag>": writes nothing until <flag> exists (like a CLI blocked on a macOS privacy
   prompt), then one line. "normal": writes its screen at once, then idles without output, like a CLI at its prompt. */
#include <stdio.h>
#include <string.h>
#include <unistd.h>

int main(int argc, char **argv) {
  if (argc == 3 && strcmp(argv[1], "silent") == 0) {
    while (access(argv[2], F_OK) != 0) usleep(200000);
    printf("ready\n");
  } else if (argc == 2 && strcmp(argv[1], "normal") == 0) {
    printf("Stand-in CLI v1\n> ");
  } else return 2;
  fflush(stdout);
  sleep(600);
  return 0;
}
