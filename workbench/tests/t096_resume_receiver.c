/* T-078-style controlled native receiver. No model, hooks or tool execution.
 * Record actual argv; refuse nonexistent resume targets; never replace a session.
 */
#define _DARWIN_C_SOURCE 1
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <termios.h>
#include <unistd.h>
#include <limits.h>
static void string(FILE *f, const char *s) {
  fputc('"', f);
  for (const unsigned char *p=(const unsigned char *)s; *p; p++) {
    if (*p=='"' || *p=='\\') { fputc('\\',f); fputc(*p,f); }
    else if (*p<32) fprintf(f,"\\u%04x",*p); else fputc(*p,f);
  }
  fputc('"',f);
}
int main(int argc, char **argv) {
  if (argc==2 && !strcmp(argv[1],"--version")) { puts("codex-cli 0.162.1"); return 0; }
  const char *home=getenv("CODEX_HOME"), *session=getenv("A2A_SESSION");
  if (!home || !session) return 2;
  int resumed=argc>2 && !strcmp(argv[argc-2],"resume");
  if (resumed && strcmp(argv[argc-1],session)) return 3;
  char directory[PATH_MAX], file[PATH_MAX], cwd[PATH_MAX];
  if (!getcwd(cwd,sizeof cwd)) return 4;
  snprintf(directory,sizeof directory,"%s/sessions",home); mkdir(directory,0700);
  snprintf(file,sizeof file,"%s/sessions/rollout-%s.jsonl",home,session);
  FILE *native=fopen(file,resumed?"r":"wx"); if (!native) return 5;
  if (!resumed) {
    fputs("{\"type\":\"session_meta\",\"payload\":{\"source\":\"cli\",\"id\":",native);
    string(native,session); fputs(",\"cwd\":",native); string(native,cwd); fputs("}}\n",native);
  }
  fclose(native);
  snprintf(file,sizeof file,"%s/receiver-%d.json",home,getpid());
  FILE *receipt=fopen(file,"wx"); if (!receipt) return 6;
  fprintf(receipt,"{\"pid\":%d,\"resumed\":%s,\"native_session\":",getpid(),resumed?"true":"false");
  string(receipt,session); fputs(",\"argv\":[",receipt);
  for (int i=0;i<argc;i++) { if(i) fputc(',',receipt); string(receipt,argv[i]); }
  fputs("],\"model_turns\":0}\n",receipt); fclose(receipt);
  struct termios mode; if (tcgetattr(0,&mode)) return 7;
  cfmakeraw(&mode); if (tcsetattr(0,TCSANOW,&mode)) return 8;
  puts("T096_RECEIVER_READY"); fflush(stdout);
  char bytes[4096]; while(read(0,bytes,sizeof bytes)>0) {}
  return 0;
}
