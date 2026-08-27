#!/usr/bin/env bash
# Probe GPU, disk, and Python on the evaluation server. No passwords.
set -u

OUT_DIR="${1:-results}"
mkdir -p "$OUT_DIR"
STAMP="$(date +%Y-%m-%d)"
OUT="$OUT_DIR/probe-$STAMP.txt"

{
  echo "=== date ==="
  date -Is || date
  echo
  echo "=== uname ==="
  uname -a
  echo
  echo "=== nvidia-smi ==="
  if command -v nvidia-smi >/dev/null 2>&1; then
    nvidia-smi
  else
    echo "nvidia-smi not found"
  fi
  echo
  echo "=== df -h ==="
  df -h
  echo
  echo "=== free -h ==="
  if command -v free >/dev/null 2>&1; then
    free -h
  else
    echo "free not found"
  fi
  echo
  echo "=== python ==="
  python3 --version 2>/dev/null || echo "python3 not found"
  which python3 2>/dev/null || true
  echo
  echo "=== conda ==="
  which conda 2>/dev/null || echo "conda not found"
  echo
  echo "=== pwd ==="
  pwd
} | tee "$OUT"

echo
echo "Wrote $OUT"
echo "Use df -h to decide whether FF++ c23 plus at least one cross-dataset set will fit."
echo "If disk is tight, use DFDC preview and report test_set as dfdc_preview."
