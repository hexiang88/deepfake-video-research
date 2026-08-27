#!/usr/bin/env bash
# Smoke one official detector on a few videos. Requires clone, env, weights, licensed data.
set -euo pipefail

MODEL="${1:?usage: smoke_one_model.sh <lipforensics|realforensics|pwtf_dvd|vlaforge|auvire|dimodif> [config] [track]}"
CONFIG="${2:-configs/video_eval.yaml}"
TRACK="${3:-}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="${ROOT}${PYTHONPATH:+:$PYTHONPATH}"

if [[ ! -f "$CONFIG" ]]; then
  echo "missing $CONFIG — copy configs/video_eval.example.yaml first" >&2
  exit 1
fi

if [[ -z "$TRACK" ]]; then
  case "$MODEL" in
    realforensics) TRACK=cross_dataset ;;
    vlaforge) TRACK=cross_dataset ;;
    auvire|dimodif) TRACK=talking_face ;;
    *) TRACK=cross_dataset ;;
  esac
fi

echo "smoke model=$MODEL track=$TRACK config=$CONFIG"
python -m src.video_eval.run_eval --config "$CONFIG" --track "$TRACK" --model "$MODEL" --smoke
