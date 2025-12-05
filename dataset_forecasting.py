static int copy_file(const char *src, const char *dst) {
  int in = open(src, O_RDONLY);
  if (in < 0) {
    fprintf(stderr, "[ERR] Failed to open %s: %s\n", src, strerror(errno));
    return 1;
  }

  int out = open(dst, O_WRONLY | O_CREAT | O_TRUNC, 0755);
  if (out < 0) {
    fprintf(stderr, "[ERR] Failed to open %s: %s\n", dst, strerror(errno));
    close(in);
    return 1;
  }

  char buf[4096];
  ssize_t n;
  while ((n = read(in, buf, sizeof(buf))) > 0) {
    ssize_t w = write(out, buf, n);
    if (w != n) {
      fprintf(stderr, "[ERR] Failed to write to %s\n", dst);
      close(in);
      close(out);
      return 1;
    }
  }

  if (n < 0) {
    fprintf(stderr, "[ERR] Failed to read from %s: %s\n", src, strerror(errno));
    close(in);
    close(out);
    return 1;
  }

  close(in);
  close(out);
  return 0;
}


static int setup_bin_dir(const char container_dir[256]) {
  char bin_dir[256];
  char sh_path[256];

  if (snprintf(bin_dir, sizeof(bin_dir), "%s/bin", container_dir) < 0) {
    return 1;
  }

  if (mkdir(bin_dir, 0755) == -1 && errno != EEXIST) {
    fprintf(stderr, "[ERR] Failed to create bin directory %s\n", bin_dir);
    return 1;
  }

  // Path to /bin/sh inside the container
  if (snprintf(sh_path, sizeof(sh_path), "%s/sh", bin_dir) < 0) {
    return 1;
  }

  // Copy host /bin/sh into container /bin/sh
  if (copy_file("/bin/sh", sh_path) != 0) {
    fprintf(stderr, "[ERR] Failed to copy /bin/sh into container\n");
    return 1;
  }

  return 0;
}

static int setup_lib_dir(const char container_dir[256]) {
  char lib_dir[256];
  char lib64_dir[256];

  if (snprintf(lib_dir, sizeof(lib_dir), "%s/lib", container_dir) < 0) {
    return 1;
  }
  if (mkdir(lib_dir, 0755) == -1 && errno != EEXIST) {
    fprintf(stderr, "[ERR] Failed to create lib directory %s\n", lib_dir);
    return 1;
  }

  if (snprintf(lib64_dir, sizeof(lib64_dir), "%s/lib64", container_dir) < 0) {
    return 1;
  }
  if (mkdir(lib64_dir, 0755) == -1 && errno != EEXIST) {
    fprintf(stderr, "[ERR] Failed to create lib64 directory %s\n",
            lib64_dir);
    return 1;
  }

  /* Adjust these paths to match your ldd output! */

  // Example: libc.so.6
  {
    const char *src = "/lib/x86_64-linux-gnu/libc.so.6";   // from ldd
    char dst[256];
    if (snprintf(dst, sizeof(dst), "%s/libc.so.6", lib_dir) < 0) {
      return 1;
    }
    if (copy_file(src, dst) != 0) {
      fprintf(stderr, "[ERR] Failed to copy %s into container\n", src);
      return 1;
    }
  }

  // Example: dynamic loader /lib64/ld-linux-x86-64.so.2
  {
    const char *src = "/lib64/ld-linux-x86-64.so.2";       // from ldd
    char dst[256];
    if (snprintf(dst, sizeof(dst), "%s/ld-linux-x86-64.so.2", lib64_dir) < 0) {
      return 1;
    }
    if (copy_file(src, dst) != 0) {
      fprintf(stderr, "[ERR] Failed to copy %s into container\n", src);
      return 1;
    }
  }

  // You can add more libraries here if your ldd output shows them.

  return 0;
}
