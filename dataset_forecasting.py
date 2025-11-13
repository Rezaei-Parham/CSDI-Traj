uint64
sys_next_process(void)
{
  int before_pid;
  uint64 uaddr; // user pointer to struct process_data

  if (argint(0, &before_pid) < 0)
    return -1;
  if (argaddr(1, &uaddr) < 0)
    return -1;

  struct proc *p;
  struct proc *best = 0;

  // Find the process with the smallest pid that is > before_pid
  // and is not UNUSED.
  for (p = proc; p < &proc[NPROC]; p++) {
    acquire(&p->lock);
    if (p->state != UNUSED && p->pid > before_pid) {
      if (best == 0 || p->pid < best->pid) {
        if (best != 0)
          release(&best->lock);
        best = p;
      } else {
        release(&p->lock);
      }
    } else {
      release(&p->lock);
    }
  }

  if (best == 0) {
    // Nothing found. Return 0 and do not touch user struct.
    return 0;
  }

  // We have best locked. Copy its info into a local struct.
  struct process_data_k {
    int pid;
    int parent_id;
    int heap_size;
    int state;
    char name[16];
  } kproc;

  kproc.pid = best->pid;
  kproc.state = best->state;
  kproc.parent_id = (best->parent) ? best->parent->pid : 0;
  kproc.heap_size = best->sz;  // total address space size in bytes

  // Copy process name
  safestrcpy(kproc.name, best->name, sizeof(kproc.name));

  release(&best->lock);

  // Copy to user space.
  struct proc *cur = myproc();
  if (copyout(cur->pagetable, uaddr, (char *)&kproc, sizeof(kproc)) < 0) {
    return -1;
  }

  return 1; // found and filled
}
