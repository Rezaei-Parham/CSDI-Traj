#include "kernel/types.h"
#include "kernel/stat.h"
#include "user/user.h"
#include "kernel/param.h"   // for NPROC if you want the constant
#define MAXP NPROC   // or just pick 64 if you don't want to include param.h

int
read_all_processes(struct process_data procs[], int maxp)
{
  struct process_data tmp;
  int n = 0;
  int before = 0;

  while (1) {
    int r = next_process(before, &tmp);
    if (r == 0) {
      // no more processes
      break;
    }
    if (n < maxp) {
      procs[n++] = tmp;    // struct copy
    }
    before = tmp.pid;      // next time ask for pid > this one
  }
  return n;   // number of valid entries
}

void
print_indent(int level)
{
  for (int i = 0; i < level; i++)
    printf("  ");  // 2 spaces per level
}

char*
state_string(int s)
{
  // keep this consistent with kernel enum procstate order
  switch (s) {
  case 0: return "unused";
  case 1: return "sleep";
  case 2: return "runnable";
  case 3: return "running";
  case 4: return "zombie";
  default: return "unknown";
  }
}

void
print_proc_line(struct process_data *p, int level)
{
  print_indent(level);
  printf("%d (%d) sz=%d state=%s name=%s\n",
         p->pid, p->parent_id, p->heap_size,
         state_string(p->state), p->name);
}

void
print_tree(int root_pid, struct process_data procs[], int nprocs, int level)
{
  // Find root struct
  struct process_data *root = 0;
  for (int i = 0; i < nprocs; i++) {
    if (procs[i].pid == root_pid) {
      root = &procs[i];
      break;
    }
  }
  if (root == 0)
    return;  // nothing to print

  print_proc_line(root, level);

  // Print all children (processes whose parent_id == root_pid)
  for (int i = 0; i < nprocs; i++) {
    if (procs[i].parent_id == root_pid) {
      print_tree(procs[i].pid, procs, nprocs, level + 1);
    }
  }
}
int
find_root_pid(struct process_data procs[], int nprocs)
{
  // Try PID 1
  for (int i = 0; i < nprocs; i++) {
    if (procs[i].pid == 1)
      return 1;
  }
  // fallback: smallest pid
  int best = procs[0].pid;
  for (int i = 1; i < nprocs; i++) {
    if (procs[i].pid < best)
      best = procs[i].pid;
  }
  return best;
}

int
main(int argc, char *argv[])
{
  struct process_data procs[MAXP];
  int nprocs = read_all_processes(procs, MAXP);

  printf("Process tree (pid (ppid) size state name):\n");

  int root_pid = find_root_pid(procs, nprocs);
  print_tree(root_pid, procs, nprocs, 0);

  exit(0);
}

// user/ptree_test.c
#include "kernel/types.h"
#include "kernel/stat.h"
#include "user/user.h"

void
child_work(const char *name)
{
  // Give the process a recognizable name
  printf("%s: pid=%d\n", name, getpid());
  sleep(1000);   // sleep so pstree can see us
  exit(0);
}

int
main(int argc, char *argv[])
{
  // First child
  int pid = fork();
  if (pid == 0) {
    child_work("childA");
  }

  // Second child
  pid = fork();
  if (pid == 0) {
    // This child forks its own child
    int gpid = fork();
    if (gpid == 0) {
      child_work("grandchildB");
    }
    child_work("childB");
  }

  // Parent now execs pstree to show the tree
  char *args[] = { "pstree", 0 };
  exec("pstree", args);

  // If exec fails:
  printf("exec pstree failed\n");
  exit(1);
}
