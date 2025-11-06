// spawn_until_fail.c — capped, educational demo
// Compile: gcc -O2 -g -o spawn_until_fail spawn_until_fail.c
// Run:     ./spawn_until_fail

#define _GNU_SOURCE
#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <unistd.h>

#define MAX_TRACK  1024   // track up to 1024 child PIDs

int main(void) {
    pid_t kids[MAX_TRACK];
    int nkids = 0;

    printf("[demo] Starting spawns... (PID=%d)\n", getpid());
    fflush(stdout);

    while (1) {
        pid_t p = fork();
        if (p < 0) {
            perror("[demo] fork failed");
            break;                          // stop when we hit the limit
        }
        if (p == 0) {
            // child: burn a tiny bit of CPU then sleep so we keep the slot
            for (volatile long i = 0; i < 1000000; ++i) {}
            pause();                         // wait until parent kills us
            _exit(0);
        } else {
            // parent
            if (nkids < MAX_TRACK) kids[nkids++] = p;
        }
    }

    printf("[demo] Spawned ~%d children. Cleaning up...\n", nkids);
    // Terminate children we created (so you don’t have to reboot the VM)
    for (int i = 0; i < nkids; ++i) kill(kids[i], SIGTERM);
    for (int i = 0; i < nkids; ++i) waitpid(kids[i], NULL, 0);

    printf("[demo] Done.\n");
    return 0;
}
