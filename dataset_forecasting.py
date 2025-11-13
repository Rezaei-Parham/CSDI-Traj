int run_container(struct config cfg) {
    pid_t pid;

    // 1) Create a new PID namespace for future children
    if (unshare(CLONE_NEWPID) == -1) {
        perror("unshare(CLONE_NEWPID)");
        return 1;
    }

    // 2) Fork: parent stays in old PID namespace; child enters new one
    pid = fork();
    if (pid < 0) {
        perror("fork");
        return 1;
    }

    if (pid == 0) {
        // ---------- Child: runs inside the new PID namespace ----------
        printf("[Child] getpid(): %d (should be 1 in new PID namespace)\n", getpid());

        char buf[256];
        ssize_t n = readlink("/proc/self/ns/pid", buf, sizeof(buf) - 1);
        if (n >= 0) {
            buf[n] = '\0';
            printf("[Child] PID namespace: %s\n", buf);
        } else {
            perror("[Child] readlink /proc/self/ns/pid");
        }

        // Now exec the user command (e.g. "readlink /proc/self/ns/pid")
        execl("/bin/sh", "sh", "-c", cfg.command, NULL);

        // Only reached if execl fails
        perror("execl");
        _exit(1);
    } else {
        // ---------- Parent: still in the host PID namespace ----------
        printf("[Parent] running child with host pid: %d\n", pid);

        char buf[256];
        ssize_t n = readlink("/proc/self/ns/pid", buf, sizeof(buf) - 1);
        if (n >= 0) {
            buf[n] = '\0';
            printf("[Parent] PID namespace: %s\n", buf);
        } else {
            perror("[Parent] readlink /proc/self/ns/pid");
        }

        printf("[Parent] Stopping...\n");
        // Parent exits so that only the child remains as "init" of the new namespace
        exit(0);
    }

    return 0;
}
