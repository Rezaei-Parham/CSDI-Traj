// demo_profile_opt.c
// Build:
//   gcc -O2 -g -fno-omit-frame-pointer -o demo_opt demo_profile_opt.c
// Run:
//   ./demo_opt            # or ./demo_opt 2

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

/* -------- Optimized Fibonacci (O(n)) -------- */
static long fib_fast(int n) {
    long a = 0, b = 1;
    for (int i = 0; i < n; i++) {
        long t = a + b;
        a = b;
        b = t;
    }
    return a;
}

/* -------- qsort replacement for bubble sort -------- */
static int cmp_int(const void *pa, const void *pb) {
    int a = *(const int*)pa, b = *(const int*)pb;
    return (a > b) - (a < b);
}

/* -------- Efficient string builder (exponential growth) -------- */
typedef struct {
    char   *buf;
    size_t  len;
    size_t  cap;
} sbuf;

static void sb_init(sbuf *s) { s->buf = NULL; s->len = 0; s->cap = 0; }

static int sb_reserve(sbuf *s, size_t need_more) {
    size_t need = s->len + need_more + 1;   // +1 for '\0'
    if (need <= s->cap) return 0;
    size_t newcap = s->cap ? s->cap : 64;
    while (newcap < need) newcap <<= 1;
    char *p = (char*)realloc(s->buf, newcap);
    if (!p) return -1;
    s->buf = p; s->cap = newcap;
    return 0;
}

static int sb_append(sbuf *s, const char *add) {
    size_t addl = strlen(add);
    if (sb_reserve(s, addl) < 0) return -1;
    memcpy(s->buf + s->len, add, addl + 1);
    s->len += addl;
    return 0;
}

static void sb_free(sbuf *s) { free(s->buf); s->buf = NULL; s->len = s->cap = 0; }

/* ---------------- Main ---------------- */
int main(int argc, char **argv) {
    int scale = (argc > 1) ? atoi(argv[1]) : 1;
    if (scale < 1) scale = 1;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);

    /* 1) Sort a big array (now O(n log n) via qsort) */
    int n = 15000 * scale;
    int *arr = (int*)malloc((size_t)n * sizeof(int));
    if (!arr) { perror("malloc"); return 1; }
    for (int i = 0; i < n; i++) arr[i] = rand();
    qsort(arr, n, sizeof(int), cmp_int);

    /* 2) Fast Fibonacci */
    long fibsum = 0;
    for (int i = 0; i < 2 * scale; i++) fibsum += fib_fast(42);

    /* 3) Efficient string builder */
    sbuf sb; sb_init(&sb);
    for (int i = 0; i < 20000 * scale; i++) {
        if (sb_append(&sb, "x") < 0) { fprintf(stderr, "alloc failed\n"); break; }
    }

    free(arr);
    clock_gettime(CLOCK_MONOTONIC, &t1);

    double dt = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec)/1e9;
    printf("Done (optimized). scale=%d, time=%.3f s, fibsum=%ld, strlen=%zu\n",
           scale, dt, fibsum, sb.len);

    sb_free(&sb);
    return 0;
}

# save folded stacks
perf script | ./FlameGraph/stackcollapse-perf.pl > before.folded
# (re-run optimized) …
perf script | ./FlameGraph/stackcollapse-perf.pl > after.folded
./FlameGraph/difffolded.pl before.folded after.folded \
  | ./FlameGraph/flamegraph.pl --negate > flame-diff.svg
