// kernel/get_pcb_times.c

#include <linux/kernel.h>
#include <linux/syscalls.h>
#include <linux/sched.h>     // for current, task_struct
#include <linux/uaccess.h>   // for copy_to_user

struct pcb_times {
    u64 enter_ns;
    u64 exit_ns;
};

/*
 * get_pcb_times(struct pcb_times __user *uinfo)
 *
 * Copies the last measured syscall's entry/exit timestamps
 * from the current process's task_struct into user space.
 */
SYSCALL_DEFINE1(get_pcb_times, struct pcb_times __user *, uinfo)
{
    struct pcb_times t;

    t.enter_ns = current->last_sys_enter_ns;
    t.exit_ns  = current->last_sys_exit_ns;

    if (copy_to_user(uinfo, &t, sizeof(t)))
        return -EFAULT;

    return 0;
}
