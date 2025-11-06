#include "types.h"
#include "param.h"
#include "riscv.h"
#include "memlayout.h"
#include "spinlock.h"
#include "proc.h"
#include "defs.h"

// Print a simple process table from the kernel.
// No user buffer; prints straight to the console.
uint64
sys_topprint(void)
{
  // header like your screenshot
  printf("PID\tCommand\t\tSize of Process Memory\n");

  for(struct proc *p = proc; p < &proc[NPROC]; p++){
    int pid = 0;
    uint64 sz = 0;
    char name[16];

    acquire(&p->lock);
    if(p->state != UNUSED){
      pid = p->pid;
      sz  = p->sz;
      // copy name (p->name length is 16 incl. '\0')
      for(int i = 0; i < 16; i++){
        name[i] = p->name[i];
        if(p->name[i] == '\0') break;
      }
    }
    release(&p->lock);

    if(pid != 0){
      // kernel printf supports %d, %x, %p, %s (no %lu), so cast sz to int.
      // In xv6, sz is small enough that this is fine.
      printf("%d\t%s\t\t%d\n", pid, name, (int)sz);
    }
  }

  return 0;
}

#include "kernel/types.h"
#include "kernel/stat.h"
#include "user/user.h"

int
main(int argc, char **argv)
{
  if(topprint() < 0){
    fprintf(2, "top: syscall failed\n");
    exit(1);
  }
  exit(0);
}
