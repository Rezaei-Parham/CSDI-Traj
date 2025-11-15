#include <linux/kernel.h>
#include <linux/syscalls.h>
#include <linux/uaccess.h>

SYSCALL_DEFINE1(hello, char __user *, buf)
{
    const char *msg = "Hello from kernel syscall!\n";

    // copy message from kernel → user memory
    if (copy_to_user(buf, msg, strlen(msg) + 1))
        return -EFAULT;

    return 0;
}


#include <stdio.h>
#include <string.h>
#include <sys/syscall.h>
#include <unistd.h>

#define __NR_hello 451   // your syscall number

int main(void)
{
    char buf[128];

    syscall(__NR_hello, buf);

    // NOW it prints to standard output
    printf("%s", buf);

    return 0;
}
