#include "kernel/types.h"
#include "user/user.h"

int
main(int argc, char *argv[])
{
  struct process_data p;
  int before = 0;

  while (1) {
    int r = next_process(before, &p);
    if (r == 0) {
      break;
    }
    printf("pid=%d parent=%d size=%d state=%d name=%s\n",
           p.pid, p.parent_id, p.heap_size, p.state, p.name);
    before = p.pid;
  }

  exit(0);
}
