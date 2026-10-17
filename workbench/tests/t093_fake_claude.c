/* Deterministic native PTY fixture. Never invokes a vendor CLI or model. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>
#include <termios.h>
#include <limits.h>

static int peer(const char *script, const char *text, int turn) {
    char number[16]; snprintf(number, sizeof number, "%d", turn);
    pid_t child = fork();
    if (child == 0) { execl("/usr/bin/python3", "python3", "-B", script, text, number, NULL); _exit(127); }
    int status; if (child < 0 || waitpid(child, &status, 0) < 0 || !WIFEXITED(status)) return 125;
    return WEXITSTATUS(status);
}
int main(int argc, char **argv) {
    if (argc == 2 && !strcmp(argv[1], "--version")) { puts("2.1.302 (Claude Code)"); return 0; }
    if (argc >= 3 && !strcmp(argv[1], "auth") && !strcmp(argv[2], "status")) { puts("{\"loggedIn\":true,\"authMethod\":\"claude.ai\"}"); return 0; }
    const char *settings = NULL;
    for (int i=1; i+1<argc; i++) if (!strcmp(argv[i], "--settings")) settings=argv[i+1];
    if (!settings) return 3;
    setenv("T093_FIXTURE_SETTINGS", settings, 1);
    char script[PATH_MAX]; snprintf(script, sizeof script, "%s", argv[0]);
    char *slash = strrchr(script, '/'); if (!slash) return 4;
    strcpy(slash+1, "fake-login-peer.py");
    struct termios mode; if (tcgetattr(0, &mode)) return 5; cfmakeraw(&mode); tcsetattr(0, TCSANOW, &mode);
    if (peer(script, "", 0)) return 6;
    puts("fixture-ready"); fflush(stdout);
    char line[131072]; size_t used=0; int turn=0; char c;
    while (read(0, &c, 1)==1) {
        if (c=='\r' || c=='\n') {
            line[used]='\0';
            char *start=line; if (!strncmp(start,"\033[200~",6)) start+=6;
            size_t length=strlen(start); if (length>=6 && !strcmp(start+length-6,"\033[201~")) start[length-6]='\0';
            if (peer(script, start, ++turn)) return 7;
            printf("fixture-turn-%d-complete\n", turn); fflush(stdout); used=0;
        } else if (used+1<sizeof line) line[used++]=c; else return 8;
    }
    return 0;
}
