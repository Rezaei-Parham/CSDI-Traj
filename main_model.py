#define _GNU_SOURCE
#include <stdio.h>
#include <stdint.h>
#include <unistd.h>
#include <sys/syscall.h>
#include <fcntl.h>
#include <errno.h>

/*
 * Adjust these two numbers to match your syscall table:
 *   arch/x86/entry/syscalls/syscall_64.tbl   (or arch-specific equivalent)
 */
#define __NR_time_info     454   // <-- change to your time_info number
#define __NR_get_pcb_times 455   // <-- change to your get_pcb_times number

/* Must match kernel structs exactly */
struct time_info {
    uint64_t now_ns;
};

struct pcb_times {
    uint64_t enter_ns;
    uint64_t exit_ns;
};

/* --- Helpers to call the syscalls --- */

static int get_time_info(struct time_info *out)
{
    long ret = syscall(__NR_time_info, out);
    if (ret < 0) {
        perror("time_info");
        return -1;
    }
    return 0;
}

static int get_pcb_times(struct pcb_times *out)
{
    long ret = syscall(__NR_get_pcb_times, out);
    if (ret < 0) {
        perror("get_pcb_times");
        return -1;
    }
    return 0;
}

static void print_with_segments(const char *name,
                                uint64_t t_before,
                                uint64_t t_kernel_start,
                                uint64_t t_kernel_end,
                                uint64_t t_after)
{
    printf("\n=== %s ===\n", name);
    printf("time_before_user      = %llu ns\n",
           (unsigned long long)t_before);
    printf("time_start_in_kernel  = %llu ns\n",
           (unsigned long long)t_kernel_start);
    printf("time_end_in_kernel    = %llu ns\n",
           (unsigned long long)t_kernel_end);
    printf("time_after_user       = %llu ns\n",
           (unsigned long long)t_after);

    if (t_kernel_start >= t_before &&
        t_kernel_end   >= t_kernel_start &&
        t_after        >= t_kernel_end) {

        uint64_t user_to_kernel = t_kernel_start - t_before;
        uint64_t kernel_body    = t_kernel_end   - t_kernel_start;
        uint64_t kernel_to_user = t_after        - t_kernel_end;
        uint64_t total          = t_after        - t_before;

        printf("User -> Kernel        = %llu ns\n",
               (unsigned long long)user_to_kernel);
        printf("Kernel body           = %llu ns\n",
               (unsigned long long)kernel_body);
        printf("Kernel -> User        = %llu ns\n",
               (unsigned long long)kernel_to_user);
        printf("Total                 = %llu ns\n",
               (unsigned long long)total);
    } else {
        printf("Warning: timestamps not monotonic, see raw values above.\n");
    }
}

/* ---------- Test getpid ---------- */

static void test_getpid_once(void)
{
    struct time_info tb, ta;
    struct pcb_times pcb;

    if (get_time_info(&tb) < 0)
        return;

    pid_t pid = getpid();
    (void)pid;  // just to avoid unused warning

    if (get_time_info(&ta) < 0)
        return;

    if (get_pcb_times(&pcb) < 0)
        return;

    print_with_segments("getpid",
                        tb.now_ns,
                        pcb.enter_ns,
                        pcb.exit_ns,
                        ta.now_ns);
}

/* ---------- Test read ---------- */

static void test_read_once(void)
{
    int fd = open("testfile_read.bin", O_RDONLY);
    if (fd < 0) {
        perror("open testfile_read.bin");
        return;
    }

    char buf[16];
    struct time_info tb, ta;
    struct pcb_times pcb;

    if (get_time_info(&tb) < 0) {
        close(fd);
        return;
    }

    ssize_t n = read(fd, buf, sizeof(buf));
    if (n < 0) {
        perror("read");
        close(fd);
        return;
    }

    if (get_time_info(&ta) < 0) {
        close(fd);
        return;
    }

    if (get_pcb_times(&pcb) < 0) {
        close(fd);
        return;
    }

    close(fd);

    print_with_segments("read",
                        tb.now_ns,
                        pcb.enter_ns,
                        pcb.exit_ns,
                        ta.now_ns);
}

/* ---------- Test write ---------- */

static void test_write_once(void)
{
    int fd = open("testfile_write.bin", O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (fd < 0) {
        perror("open testfile_write.bin");
        return;
    }

    const char buf[16] = "abcdefghijklmnop";
    struct time_info tb, ta;
    struct pcb_times pcb;

    if (get_time_info(&tb) < 0) {
        close(fd);
        return;
    }

    ssize_t n = write(fd, buf, sizeof(buf));
    if (n < 0) {
        perror("write");
        close(fd);
        return;
    }

    if (get_time_info(&ta) < 0) {
        close(fd);
        return;
    }

    if (get_pcb_times(&pcb) < 0) {
        close(fd);
        return;
    }

    close(fd);

    print_with_segments("write",
                        tb.now_ns,
                        pcb.enter_ns,
                        pcb.exit_ns,
                        ta.now_ns);
}

/* ---------- Test time_info itself (no PCB segments) ---------- */

static void test_time_info_once(void)
{
    /*
     * Here we just measure how long a time_info call itself takes.
     * Since time_info does NOT write PCB fields, pcb.enter_ns/exit_ns
     * would not correspond to this call, so we ignore PCB for this test.
     */

    struct time_info tb, tcall, ta;

    if (get_time_info(&tb) < 0)
        return;

    if (get_time_info(&tcall) < 0)
        return;

    if (get_time_info(&ta) < 0)
        return;

    uint64_t t_before = tb.now_ns;
    uint64_t t_after  = ta.now_ns;
    uint64_t total    = t_after - t_before;

    printf("\n=== time_info (timing the call itself) ===\n");
    printf("time_before_user = %llu ns\n",
           (unsigned long long)t_before);
    printf("time_after_user  = %llu ns\n",
           (unsigned long long)t_after);
    printf("Total (one time_info call, approx) = %llu ns\n",
           (unsigned long long)total);
}

/* ---------- main ---------- */

int main(void)
{
    printf("Syscall timing experiment using time_info:\n");

    test_getpid_once();
    test_read_once();
    test_write_once();
    test_time_info_once();

    return 0;
}
