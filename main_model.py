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

// kernel/time_info_syscall.c

#include <linux/kernel.h>
#include <linux/syscalls.h>
#include <linux/ktime.h>
#include <linux/uaccess.h>
#include <linux/sched.h>

struct time_info {
    u64 now_ns;    /* current time */
    u64 enter_ns;  /* last measured syscall entry */
    u64 exit_ns;   /* last measured syscall exit */
};

SYSCALL_DEFINE1(time_info, struct time_info __user *, uinfo)
{
    struct time_info info;

    info.now_ns   = ktime_get_ns();
    info.enter_ns = current->last_sys_enter_ns;
    info.exit_ns  = current->last_sys_exit_ns;

    if (copy_to_user(uinfo, &info, sizeof(info)))
        return -EFAULT;

    return 0;
}

#define _GNU_SOURCE
#include <stdio.h>
#include <stdint.h>
#include <unistd.h>
#include <sys/syscall.h>
#include <fcntl.h>

#define __NR_time_info 460
#define __NR_my_custom 461

struct time_info {
    uint64_t now_ns;
    uint64_t enter_ns;
    uint64_t exit_ns;
};

static void measure_one(const char *name, void (*do_syscall)(void))
{
    struct time_info before, after;

    /* time before */
    syscall(__NR_time_info, &before);
    uint64_t t_user_before = before.now_ns;

    /* the syscall under test */
    do_syscall();

    /* time after */
    syscall(__NR_time_info, &after);
    uint64_t t_user_after   = after.now_ns;
    uint64_t t_kernel_enter = after.enter_ns;
    uint64_t t_kernel_exit  = after.exit_ns;

    printf("\n=== %s ===\n", name);
    printf("User->Kernel  : %lld ns\n",
           (long long)(t_kernel_enter - t_user_before));
    printf("Kernel body   : %lld ns\n",
           (long long)(t_kernel_exit - t_kernel_enter));
    printf("Kernel->User  : %lld ns\n",
           (long long)(t_user_after - t_kernel_exit));
    printf("Total         : %lld ns\n",
           (long long)(t_user_after - t_user_before));
}

/* wrappers */

static void do_getpid(void) {
    (void)getpid();
}

static int rw_fd_r = -1, rw_fd_w = -1;

static void do_read(void) {
    char buf[8];
    (void)read(rw_fd_r, buf, sizeof(buf));
}

static void do_write(void) {
    const char buf[8] = "1234567";
    (void)write(rw_fd_w, buf, sizeof(buf));
}

static void do_custom(void) {
    (void)syscall(__NR_my_custom);
}

int main(void)
{
    rw_fd_r = open("/dev/zero", O_RDONLY);
    rw_fd_w = open("/dev/null", O_WRONLY);
    if (rw_fd_r < 0 || rw_fd_w < 0) {
        perror("open");
        return 1;
    }

    measure_one("getpid",  do_getpid);
    measure_one("read",    do_read);
    measure_one("write",   do_write);
    measure_one("my_custom", do_custom);

    close(rw_fd_r);
    close(rw_fd_w);
    return 0;
}

static uint64_t
clock_gettime_ns(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC_RAW, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ull + ts.tv_nsec;
}

static void
check_time_info_vs_clock_gettime(int iters)
{
    struct time_info info;
    uint64_t min_diff = (uint64_t)-1;
    uint64_t max_diff = 0;
    long double sum_abs_diff = 0.0L;

    for (int i = 0; i < iters; i++) {
        /* 1. Read user-space high-res clock */
        uint64_t t_clk = clock_gettime_ns();

        /* 2. Read kernel time via our syscall */
        if (syscall(__NR_time_info, &info) != 0) {
            perror("time_info");
            return;
        }
        uint64_t t_sys = info.now_ns;

        /* 3. Compute signed difference: syscall - clock_gettime */
        long long diff = (long long)(t_sys - t_clk);
        uint64_t abs_diff = (diff >= 0) ? (uint64_t)diff : (uint64_t)(-diff);

        if (abs_diff < min_diff)
            min_diff = abs_diff;
        if (abs_diff > max_diff)
            max_diff = abs_diff;

        sum_abs_diff += (long double)abs_diff;
    }

    long double avg_abs = sum_abs_diff / iters;

    printf("\n=== time_info vs clock_gettime(CLOCK_MONOTONIC_RAW) ===\n");
    printf("Samples: %d\n", iters);
    printf("Min |Δ| = %llu ns\n", (unsigned long long)min_diff);
    printf("Max |Δ| = %llu ns\n", (unsigned long long)max_diff);
    printf("Avg |Δ| = %.2Lf ns\n", avg_abs);
}

    printf("\n=== Comparing kernel time_info with Linux clock_gettime ===\n");
    check_time_info_vs_clock_gettime(100000);  // 100k samples
