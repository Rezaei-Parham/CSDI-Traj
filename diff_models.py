#!/usr/bin/env bash
set -e

# Usage: ./overlay-build.sh path/to/Dockerfile.simple
DF="${1:-Dockerfile.simple}"

cd /tmp/overlay-lab

# Parse simplified Dockerfile: one BASEDIR, multiple RUN lines
BASEDIR="$(awk '$1=="BASEDIR"{print $2; exit}' "$DF")"
mapfile -t RUNS < <(awk '$1=="RUN"{$1=""; sub(/^ /,""); print}' "$DF")

# Build one upper layer per RUN
for i in "${!RUNS[@]}"; do
  upper="upper$i"
  work="work$i"
  merged="merged$i"

  mkdir -p "$upper" "$work" "$merged"
  rm -rf "$work"/*

  # lowerdir: newest previous upper first, then BASEDIR last
  lowerdir="$BASEDIR"
  for ((j=i-1; j>=0; j--)); do
    lowerdir="$(pwd)/upper$j:$lowerdir"
  done

  sudo mount -t overlay overlay \
    -o "lowerdir=$lowerdir,upperdir=$(pwd)/$upper,workdir=$(pwd)/$work" \
    "$(pwd)/$merged"

  ( cd "$merged" && bash -c "${RUNS[$i]}" )

  sudo umount "$merged"
done
