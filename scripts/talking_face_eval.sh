#!/usr/bin/env bash
# Talking Face / 唇音 / TFL on eval-host (USER). No sudo. Do not use base Python 3.13.
# Usage:
#   bash scripts/talking_face_eval.sh inspect          # eval-host local disks
#   bash scripts/talking_face_eval.sh inspect-mentor   # MENTOR_HOST only
#   bash scripts/talking_face_eval.sh auvire
#   bash scripts/talking_face_eval.sh dimodif
#   bash scripts/talking_face_eval.sh eval-missing   # write data_missing JSON if official sets absent
#   bash scripts/talking_face_eval.sh eval-official  # only after LAV-DF + AVD1M (and FakeAVCeleb for DiMoDif) are official
set -euo pipefail

STAGE="${1:?usage: talking_face_eval.sh <inspect|inspect-mentor|auvire|dimodif|eval-missing|eval-official>}"

export DATA="${DATA:-/data/USER/deepfake-bench}"
export CODE="${CODE:-$DATA/code}"
export CONDA_ROOT="${CONDA_ROOT:-/home/USER/miniconda3}"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-1}"
# yaml gpu: cuda:0 maps to this visible device. Do not edit yaml gpu.

TUNA_FORGE="https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge"
PIP_TUNA="https://pypi.tuna.tsinghua.edu.cn/simple"
# Mentor host MENTOR_HOST only — NOT expected on eval-host unless later NFS-mounted.
MENTOR_FA="/data/MENTOR_DATASETS/FakeAVCeleb"
MENTOR_DS="/data/MENTOR_DATASETS"

LAV_PTH="lavdf_b_avhubert_t_cnn_cnn_h_8_d_128_l_r2d2_w_15_o_subtraction_rl_r2d3u3s2_rm_av_aa_vv_f_True_conv_lr-_c_focal_diou_rec.pth"
AVD_PTH="avdeepfake1m_b_avhubert_t_cnn_cnn_h_8_d_128_l_r1d1_w_15_o_subtraction_rl_r2d1u1s2_rm_av_aa_vv_f_True_conv_lr-_c_focal_diou_rec.pth"
LAV_JSON="lavdf_b_avhubert_t_cnn_cnn_h_8_d_128_l_r2d2_w_15_o_subtraction_rl_r2d3u3s2_rm_av_aa_vv_f_True_conv_lr-_c_focal_diou_rec.json"
AVD_JSON="avdeepfake1m_b_avhubert_t_cnn_cnn_h_8_d_128_l_r1d1_w_15_o_subtraction_rl_r2d1u1s2_rm_av_aa_vv_f_True_conv_lr-_c_focal_diou_rec.json"
# Official Zenodo 17698401 / 17701536 (same pth bytes + md5). Do not replace with HF safetensors.
LAV_MD5="a694ab3fce5a1706f03d51d7f04e0261"
AVD_MD5="098cb9d0676276e3705a5ab5f57507ad"
LAV_BYTES="145514674"
AVD_BYTES="107377358"
ZENODO_API="https://zenodo.org/api/records/17698401/files"

ensure_auvire_repo() {
  local dest="$DATA/models/AuViRe"
  mkdir -p "$DATA/models"
  if [[ -d "$dest/.git" ]]; then
    git -C "$dest" remote -v
    git -C "$dest" fetch origin
    git -C "$dest" checkout origin/main -- .
  elif [[ ! -e "$dest" ]]; then
    git clone https://github.com/mever-team/auvire.git "$dest"
  else
    local tmp="$DATA/models/AuViRe.src.$$"
    git clone https://github.com/mever-team/auvire.git "$tmp"
    # Keep an already-copied fairseq tree; overlay official tracked files.
    (cd "$tmp" && tar cf - --exclude='./fairseq' --exclude='./.git' .) | (cd "$dest" && tar xf -)
    if [[ ! -d "$dest/.git" ]]; then
      mv "$tmp/.git" "$dest/.git"
    fi
    rm -rf "$tmp"
  fi
  test -f "$dest/requirements.txt"
  test -f "$dest/ckpt/$LAV_JSON"
  test -f "$dest/ckpt/$AVD_JSON"
}

download_zenodo_pth() {
  local dest="$1" name="$2" md5="$3" bytes="$4"
  local url="$ZENODO_API/${name}/content"
  local sz head
  if [[ -f "$dest" ]]; then
    sz="$(stat -c%s "$dest")"
    if [[ "$sz" == "$bytes" ]] && echo "$md5  $dest" | md5sum -c -; then
      echo "keep $(basename "$dest") ($sz bytes, md5 ok)"
      return 0
    fi
    head="$(head -c 200 "$dest" || true)"
    echo "corrupt $(basename "$dest") size=$sz expected=$bytes; head=$head"
    rm -f "$dest"
  fi
  mkdir -p "$(dirname "$dest")"
  if command -v curl >/dev/null 2>&1; then
    curl -L --fail --retry 8 --retry-delay 2 -A "curl" -o "$dest" "$url"
  else
    wget --tries=8 --timeout=60 -O "$dest" "$url"
  fi
  sz="$(stat -c%s "$dest")"
  if [[ "$sz" != "$bytes" ]]; then
    echo "REFUSE: size $sz != $bytes for $dest (likely HTML). head:" >&2
    head -c 200 "$dest" >&2 || true
    exit 2
  fi
  echo "$md5  $dest" | md5sum -c -
}

never_base_python() {
  local py="$1"
  local ver
  ver="$("$py" -V 2>&1 || true)"
  echo "python: $py  $ver"
  if echo "$ver" | grep -q "3.13"; then
    echo "REFUSE: do not use base Python 3.13 for detectors" >&2
    exit 2
  fi
}

_search_talking_roots() {
  local root="$1" depth="$2"
  if [[ ! -d "$root" ]]; then
    echo "skip (absent): $root"
    return 0
  fi
  echo "--- find in $root (maxdepth $depth) ---"
  find "$root" -maxdepth "$depth" \( \
    -iname '*FakeAVCeleb*' -o -iname '*fakeavceleb*' -o -iname '*fake_fakeav*' \
    -o -iname '*LAV-DF*' -o -iname '*lavdf*' -o -iname '*lav_df*' \
    -o -iname '*Deepfake1M*' -o -iname '*AV-Deepfake*' -o -iname '*avdeepfake1m*' \
    \) 2>/dev/null | head -n 40 || true
}

inspect_data() {
  echo "=== eval-host inspect (local disks; no downloads) ==="
  echo "NOTE: $MENTOR_DS is the mentor host MENTOR_HOST path."
  echo "It is NOT expected on eval-host. Missing here does not mean FakeAVCeleb is gone from the lab."
  echo "First-batch FF++ / mentor_swap copies live under $DATA/datasets/."
  whoami; echo "HOME=$HOME"; echo "DATA=$DATA"; hostname
  mkdir -p "$DATA"/{datasets,models,envs,weights,results,code}
  nvidia-smi -L || true
  echo "=== df -h ==="
  df -h
  echo "=== findmnt / ls extra roots ==="
  command -v findmnt >/dev/null && findmnt -t ext4,xfs,nfs,nfs4 -o TARGET,SOURCE,FSTYPE,SIZE,AVAIL | head -n 30 || true
  echo "ls extra roots:"; ls -ld /data /mnt /ssd /data/MENTOR_DATASETS 2>/dev/null || true
  echo "ls $DATA/datasets:"; ls -la "$DATA/datasets" 2>/dev/null | head -n 40 || true
  _search_talking_roots "$DATA/datasets" 4
  _search_talking_roots /home/USER 3
  _search_talking_roots /data 3
  _search_talking_roots /mnt 3
  _search_talking_roots /ssd 3
  if [[ -d "$MENTOR_DS" ]]; then
    echo "UNEXPECTED: mentor path is mounted on this host: $MENTOR_DS"
    _search_talking_roots "$MENTOR_DS" 4
  else
    echo "mentor path not mounted (normal on eval-host): $MENTOR_DS"
  fi
  echo "If eval-host still has no official LAV-DF / AV-Deepfake1M tree: TFL = data_missing."
  echo "Do not download full datasets (disk already tight). Do not score wav2lip folders as TFL."
}

inspect_mentor() {
  echo "=== mentor-host inspect ==="
  echo "THIS BLOCK IS FOR MENTOR_HOST, NOT eval-host."
  echo "If hostname is eval-host or $MENTOR_DS is missing, stop and run stage inspect instead."
  hostname; whoami; echo "HOME=$HOME"
  if [[ ! -d "$MENTOR_DS" ]]; then
    echo "NOT the mentor data host (missing $MENTOR_DS). Abort."
    return 2
  fi
  echo "n_mp4=$(find "$MENTOR_FA" -iname '*.mp4' 2>/dev/null | wc -l)"
  ONE="$(find "$MENTOR_FA" -iname '*.mp4' 2>/dev/null | head -n 1 || true)"
  echo "sample=$ONE"
  if [[ -n "$ONE" ]] && command -v ffprobe >/dev/null 2>&1; then
    ffprobe -hide_banner -select_streams a -show_entries stream=codec_name,duration -of default=nw=1 "$ONE" || echo "NO_AUDIO"
  fi
  find "$MENTOR_FA" -maxdepth 2 \( -iname '*meta*' -o -iname '*split*' -o -iname '*label*' -o -iname '*.csv' -o -iname '*.json' \) 2>/dev/null | head || true
  find "$MENTOR_DS" -maxdepth 4 \( -iname '*LAV*' -o -iname '*lav-df*' -o -iname '*Deepfake1M*' -o -iname '*AV-Deepfake*' \) | head || true
}

deploy_auvire() {
  echo "=== AuViRe clone + env + Zenodo detector weights ==="
  mkdir -p "$DATA/models" "$DATA/weights/auvire"
  ensure_auvire_repo
  git -C "$DATA/models/AuViRe" rev-parse HEAD
  ls -lh "$DATA/models/AuViRe/requirements.txt" "$DATA/models/AuViRe/ckpt/$LAV_JSON" "$DATA/models/AuViRe/ckpt/$AVD_JSON"
  PAPER="$DATA/results/paper_json/auvire"
  mkdir -p "$PAPER"
  if [[ -d "$DATA/models/AuViRe/results/test" && ! -e "$PAPER/MOVED" ]]; then
    mv "$DATA/models/AuViRe/results/test" "$PAPER/test"
    date -Is > "$PAPER/MOVED"
    echo "Moved bundled paper JSON to $PAPER/test — do not copy those numbers into 本机 tables."
  fi
  if ! "$CONDA_ROOT/bin/conda" env list | grep -E '^auvire\s' >/dev/null; then
    "$CONDA_ROOT/bin/conda" create --override-channels -c "$TUNA_FORGE" -n auvire python=3.10 -y
  fi
  AV="$CONDA_ROOT/envs/auvire"
  never_base_python "$AV/bin/python"
  "$AV/bin/python" -m pip install -U pip
  "$AV/bin/python" -m pip install torch==2.4.1 torchvision==0.19.1 torchaudio==2.4.1 --index-url https://download.pytorch.org/whl/cu121
  "$CONDA_ROOT/bin/conda" install --override-channels -c "$TUNA_FORGE" -n auvire sox -y
  if [[ ! -d "$DATA/models/av_hubert/.git" ]]; then
    git clone https://github.com/facebookresearch/av_hubert.git "$DATA/models/av_hubert"
  fi
  git -C "$DATA/models/av_hubert" submodule update --init --recursive
  if [[ ! -d "$DATA/models/AuViRe/fairseq" ]]; then
    cp -r "$DATA/models/av_hubert/fairseq" "$DATA/models/AuViRe/fairseq"
  fi
  (
    cd "$DATA/models/AuViRe/fairseq"
    "$AV/bin/python" -m pip install --editable ./ -i "$PIP_TUNA"
  )
  IDX="$DATA/models/AuViRe/fairseq/fairseq/data/indexed_dataset.py"
  if [[ -f "$IDX" ]]; then
    sed -i 's/np\.float/float/g' "$IDX"
  fi
  test -f "$DATA/models/AuViRe/requirements.txt"
  "$AV/bin/python" -m pip install -r "$DATA/models/AuViRe/requirements.txt" -i "$PIP_TUNA"
  mkdir -p "$DATA/models/AuViRe/ckpt" "$DATA/weights/auvire"
  download_zenodo_pth "$DATA/weights/auvire/$LAV_PTH" "$LAV_PTH" "$LAV_MD5" "$LAV_BYTES"
  download_zenodo_pth "$DATA/weights/auvire/$AVD_PTH" "$AVD_PTH" "$AVD_MD5" "$AVD_BYTES"
  ln -sfn "$DATA/weights/auvire/$LAV_PTH" "$DATA/models/AuViRe/ckpt/$LAV_PTH"
  ln -sfn "$DATA/weights/auvire/$AVD_PTH" "$DATA/models/AuViRe/ckpt/$AVD_PTH"
  ls -lh "$DATA/models/AuViRe/ckpt/$LAV_PTH" "$DATA/models/AuViRe/ckpt/$AVD_PTH" \
    "$DATA/models/AuViRe/ckpt/$LAV_JSON" "$DATA/models/AuViRe/ckpt/$AVD_JSON"
  "$AV/bin/python" - <<'PY'
import torch, pathlib, sys
root = pathlib.Path("/data/USER/deepfake-bench/models/AuViRe/ckpt")
need = [
    "lavdf_b_avhubert_t_cnn_cnn_h_8_d_128_l_r2d2_w_15_o_subtraction_rl_r2d3u3s2_rm_av_aa_vv_f_True_conv_lr-_c_focal_diou_rec.pth",
    "avdeepfake1m_b_avhubert_t_cnn_cnn_h_8_d_128_l_r1d1_w_15_o_subtraction_rl_r2d1u1s2_rm_av_aa_vv_f_True_conv_lr-_c_focal_diou_rec.pth",
]
ok = 0
for name in need:
    p = (root / name).resolve()
    if p.stat().st_size < 50_000_000:
        print("REFUSE_TOO_SMALL", p, p.stat().st_size)
        sys.exit(2)
    obj = torch.load(str(p), map_location="cpu")
    keys = list(obj) if isinstance(obj, dict) else type(obj)
    print(p.name, p.stat().st_size, "torch.load_ok", keys)
    ok += 1
print("loaded", ok, "pth files")
if ok != 2:
    sys.exit(2)
PY
  echo "AuViRe detector weights OK. Do NOT extract AV-Hubert features until official LAV-DF / AVD1M exist."
  echo "Do NOT start DiMoDif until the two torch.load_ok lines above printed."
}

deploy_dimodif() {
  echo "=== DiMoDif clone + env + ckpt size check ==="
  mkdir -p "$DATA/models" "$DATA/weights/dimodif"
  if [[ ! -d "$DATA/models/DiMoDif/.git" ]]; then
    git clone https://github.com/mever-team/dimodif.git "$DATA/models/DiMoDif"
  fi
  git -C "$DATA/models/DiMoDif" rev-parse HEAD
  PAPER="$DATA/results/paper_json/dimodif"
  mkdir -p "$PAPER"
  if [[ -d "$DATA/models/DiMoDif/results/generalization" && ! -e "$PAPER/MOVED" ]]; then
    mv "$DATA/models/DiMoDif/results/generalization" "$PAPER/generalization"
    date -Is > "$PAPER/MOVED"
    echo "Moved bundled paper JSON to $PAPER/generalization — do not copy those numbers into 本机 tables."
  fi
  echo "--- ckpt sizes (Git LFS pointer is ~100 bytes → weights_missing; do not invent Drive IDs) ---"
  find "$DATA/models/DiMoDif/ckpt" -name '*.pth' -printf '%s %p\n' | sort
  SMALL="$(find "$DATA/models/DiMoDif/ckpt" -name '*.pth' -size -2k | wc -l)"
  if [[ "$SMALL" -gt 0 ]]; then
    echo "weights_missing: $SMALL pth files look like LFS pointers"
    if command -v git-lfs >/dev/null 2>&1; then
      git -C "$DATA/models/DiMoDif" lfs pull
      find "$DATA/models/DiMoDif/ckpt" -name '*.pth' -printf '%s %p\n' | sort
    else
      echo "git-lfs not installed and no sudo. Record weights_missing. Do not invent Drive IDs."
    fi
  fi
  if ! "$CONDA_ROOT/bin/conda" env list | grep -E '^dimodif\s' >/dev/null; then
    "$CONDA_ROOT/bin/conda" create --override-channels -c "$TUNA_FORGE" -n dimodif python=3.10 -y
  fi
  DM="$CONDA_ROOT/envs/dimodif"
  never_base_python "$DM/bin/python"
  "$DM/bin/python" -m pip install -U pip
  "$DM/bin/python" -m pip install -r "$DATA/models/DiMoDif/requirements.txt" -i "$PIP_TUNA"
  "$CONDA_ROOT/bin/conda" install --override-channels -c "$TUNA_FORGE" -n dimodif sox -y
  "$DM/bin/python" -m pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121
  mkdir -p "$DATA/models/DiMoDif/utils" "$DATA/models/DiMoDif/data"
  RVFA="$DATA/models/DiMoDif/ckpt/dfd/dfd_fakeavceleb_reduceonplateau_64_4_1_3_True_rvfa.pth"
  ls -lh "$RVFA" || echo "RVFA ckpt missing"
  "$DM/bin/python" - <<'PY'
import torch, pathlib
root = pathlib.Path("/data/USER/deepfake-bench/models/DiMoDif/ckpt")
n_ok = 0
for p in sorted(root.rglob("*.pth")):
    if p.stat().st_size < 2048:
        print("SKIP_LFS_POINTER", p, p.stat().st_size)
        continue
    obj = torch.load(str(p), map_location="cpu")
    print(p.relative_to(root), p.stat().st_size, "torch.load_ok")
    n_ok += 1
print("loaded", n_ok, "pth files")
PY
  echo "DiMoDif env OK. AutoAVSR feature extractors (~1.7GB) only after official FakeAVCeleb / LAV-DF / AVD1M exist."
}

eval_missing() {
  echo "=== write data_missing JSON (official LAV-DF / AVD1M / FakeAVCeleb_v1.2 absent) ==="
  never_base_python "${CODE_PY:-$CONDA_ROOT/envs/lipforensics/bin/python}"
  cd "$CODE"
  if [[ ! -f configs/video_eval.yaml ]]; then
    cp configs/video_eval.example.yaml configs/video_eval.yaml
  fi
  if [[ ! -f configs/datasets.manifest.json ]]; then
    cp configs/datasets.manifest.example.json configs/datasets.manifest.json
  fi
  # Keep gpu: cuda:0. Point python at detector envs if already created.
  python_yaml() {
    local env="$1" key="$2"
    local py="$CONDA_ROOT/envs/$env/bin/python"
    if [[ -x "$py" ]]; then
      sed -i "/^  ${key}:/,/^  [a-z]/ s|^    python: python$|    python: $py|" configs/video_eval.yaml || true
    fi
  }
  python_yaml auvire auvire
  python_yaml dimodif dimodif
  WRAP="${CODE_PY:-$CONDA_ROOT/envs/lipforensics/bin/python}"
  export PYTHONPATH="$CODE${PYTHONPATH:+:$PYTHONPATH}"
  "$WRAP" -m src.video_eval.run_eval --config configs/video_eval.yaml --track talking_face --model auvire
  "$WRAP" -m src.video_eval.run_eval --config configs/video_eval.yaml --track tfl --model auvire
  "$WRAP" -m src.video_eval.run_eval --config configs/video_eval.yaml --track talking_face --model dimodif
  "$WRAP" -m src.video_eval.run_eval --config configs/video_eval.yaml --track tfl --model dimodif
  echo "Wrote $DATA/results or ./results talking_face.json / tfl.json (not cross_dataset.json)."
}

eval_official() {
  echo "=== official eval: only if embeddings + metadata exist under each repo data/ ==="
  never_base_python "$CONDA_ROOT/envs/auvire/bin/python"
  never_base_python "$CONDA_ROOT/envs/dimodif/bin/python"
  echo "AuViRe needs AV-Hubert features for lavdf + avdeepfake1m under models/AuViRe/data/"
  echo "DiMoDif needs FakeAVCeleb_emb / LAV-DF_emb / AV-Deepfake1M_emb + meta_data.csv / metadata JSON"
  echo "If those dirs are missing, STOP and use eval-missing. Do not score MyDataSets generator folders."
  if [[ -f "$DATA/models/AuViRe/results/test/task_dfd_training_on_lavdf.json" && ! -f "$DATA/models/AuViRe/results/test/.local_run" ]]; then
    echo "REFUSE: bundled paper JSON still in AuViRe/results/test. Re-run stage auvire (moves it) or mv it to $DATA/results/paper_json/auvire/" >&2
    exit 2
  fi
  if [[ -f "$DATA/models/DiMoDif/results/generalization/dfd_fakeavceleb.json" && ! -f "$DATA/models/DiMoDif/results/generalization/.local_run" ]]; then
    echo "REFUSE: bundled paper JSON still in DiMoDif/results/generalization." >&2
    exit 2
  fi
  export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-1}"
  (
    cd "$DATA/models/AuViRe"
    "$CONDA_ROOT/envs/auvire/bin/python" scripts/test.py
    mkdir -p results/test
    date -Is > results/test/.local_run
  )
  (
    cd "$DATA/models/DiMoDif"
    "$CONDA_ROOT/envs/dimodif/bin/python" scripts/eval.py
    mkdir -p results/generalization
    date -Is > results/generalization/.local_run
  )
  cd "$CODE"
  WRAP="${CODE_PY:-$CONDA_ROOT/envs/lipforensics/bin/python}"
  export PYTHONPATH="$CODE${PYTHONPATH:+:$PYTHONPATH}"
  "$WRAP" -m src.video_eval.run_eval --config configs/video_eval.yaml --track talking_face --model auvire
  "$WRAP" -m src.video_eval.run_eval --config configs/video_eval.yaml --track tfl --model auvire
  "$WRAP" -m src.video_eval.run_eval --config configs/video_eval.yaml --track talking_face --model dimodif
  "$WRAP" -m src.video_eval.run_eval --config configs/video_eval.yaml --track tfl --model dimodif
}

case "$STAGE" in
  inspect) inspect_data ;;
  inspect-mentor) inspect_mentor ;;
  auvire) deploy_auvire ;;
  dimodif) deploy_dimodif ;;
  eval-missing) eval_missing ;;
  eval-official) eval_official ;;
  *) echo "unknown stage $STAGE" >&2; exit 2 ;;
esac
