// demo_profile.c
// Build (slow build for profiling):
//   gcc -O0 -g -fno-omit-frame-pointer -o demo demo_profile.c
// Run:
//   ./demo             # or ./demo 2 to make it slower

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static long fib_slow(int n) {          // exponential-time on purpose
    if (n <= 1) return n;
    return fib_slow(n-1) + fib_slow(n-2);
}

static void bubble_sort(int *a, int n) { // O(n^2) on purpose
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n - 1; j++)
            if (a[j] > a[j+1]) {
                int t = a[j]; a[j] = a[j+1]; a[j+1] = t;
            }
}

static char* append_slow(char *s, const char *add) { // realloc each time
    size_t old = s ? strlen(s) : 0, addl = strlen(add);
    char *p = realloc(s, old + addl + 1);
    if (!p) { free(s); return NULL; }
    memcpy(p + old, add, addl + 1);
    return p;
}

int main(int argc, char **argv) {
    int scale = (argc > 1) ? atoi(argv[1]) : 1;
    if (scale < 1) scale = 1;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);

    // 1) Bubble sort a big array (hotspot #1)
    int n = 15000 * scale;
    int *arr = (int*)malloc(n * sizeof(int));
    if (!arr) { perror("malloc"); return 1; }
    for (int i = 0; i < n; i++) arr[i] = rand();
    bubble_sort(arr, n);

    // 2) Naive Fibonacci a few times (hotspot #2)
    long fibsum = 0;
    for (int i = 0; i < 2 * scale; i++) fibsum += fib_slow(42);

    // 3) Terrible string builder (hotspot #3)
    char *s = NULL;
    for (int i = 0; i < 20000 * scale; i++) {
        s = append_slow(s, "x");
        if (!s) { fprintf(stderr, "alloc failed\n"); break; }
    }

    free(s);
    free(arr);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double dt = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec)/1e9;
    printf("Done. scale=%d, time=%.2f s, fibsum=%ld, strlen=%zu\n",
           scale, dt, fibsum, s ? strlen(s) : 0);
    return 0;
}
