// kernel/myfield_syscalls.c

#include <linux/kernel.h>
#include <linux/syscalls.h>
#include <linux/sched.h>   // for current and struct task_struct

/*
 * Set my_field for the calling process.
 */
SYSCALL_DEFINE1(set_my_field, long, value)
{
    current->my_field = value;
    return 0;
}

/*
 * Get my_field for the calling process.
 */
SYSCALL_DEFINE0(get_my_field)
{
    return current->my_field;
}

#define _GNU_SOURCE
#include <unistd.h>
#include <sys/syscall.h>
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>

#define __NR_set_my_field 452
#define __NR_get_my_field 453

int main(int argc, char *argv[])
{
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <value>\n", argv[0]);
        return 1;
    }

    long newval = strtol(argv[1], NULL, 10);

    /* --- 1. Set the new field --- */
    long ret = syscall(__NR_set_my_field, newval);
    if (ret == -1) {
        perror("set_my_field syscall failed");
        return 1;
    }
    printf("Called set_my_field(%ld)\n", newval);

    /* --- 2. Get it back --- */
    long got = syscall(__NR_get_my_field);
    if (got == -1 && errno != 0) {
        perror("get_my_field syscall failed");
        return 1;
    }

    printf("get_my_field() returned %ld\n", got);

    /* --- 3. Verification --- */
    if (got == newval)
        printf("SUCCESS: field updated correctly!\n");
    else
        printf("ERROR: field did not update!\n");

    return 0;
}
