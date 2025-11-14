#include "kernel/types.h"
#include "kernel/stat.h"
#include "kernel/param.h"   // for NPROC
#include "user/user.h"

#define MAXP NPROC   // max number of processes we’ll store

// --------- Helpers for tree view using next_process ----------

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
  // Keep this consistent with kernel enum procstate order.
  // Adjust if your enum differs.
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
  if (nprocs == 0)
    return -1;

  // Try PID 1 (init)
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

// ------------------ main: top / top -t -----------------------

int
main(int argc, char **argv)
{
  int tree = 0;

  if (argc == 1) {
    // just "top"  → flat view via syscall
    tree = 0;
  } else if (argc == 2) {
    if (!strcmp(argv[1], "-t") || !strcmp(argv[1], "--tree")) {
      tree = 1;
    } else {
      printf("usage: top [-t|--tree]\n");
      exit(1);
    }
  } else {
    printf("usage: top [-t|--tree]\n");
    exit(1);
  }

  if (!tree) {
    // Old behavior: call kernel top() syscall that prints flat listing
    if (top() < 0) {
      fprintf(2, "syscall failed (my top syscall)\n");
    }
  } else {
    // New behavior: user-space tree using next_process()
    struct process_data procs[MAXP];
    int nprocs = read_all_processes(procs, MAXP);

    if (nprocs <= 0) {
      printf("no processes\n");
      exit(0);
    }

    printf("Process tree (pid (ppid) size state name):\n");

    int root_pid = find_root_pid(procs, nprocs);
    if (root_pid < 0) {
      printf("no root process\n");
      exit(0);
    }

    print_tree(root_pid, procs, nprocs, 0);
  }

  exit(0);
}
