#!/usr/bin/env bash
# Deploy pinned GenConViT code, environment, and weights under the confirmed
# evaluation root. Evaluation datasets remain read-only.

set -Eeuo pipefail
IFS=$'\n\t'

readonly BENCH_ROOT="/data/USER/deepfake-bench"
readonly REPO_DIR="${BENCH_ROOT}/models/GenConViT"
readonly ENV_PREFIX="${BENCH_ROOT}/envs/genconvit"
readonly WEIGHTS_DIR="${BENCH_ROOT}/weights/genconvit"
readonly METADATA_DIR="${BENCH_ROOT}/metadata/genconvit"
readonly OFFLINE_DIR="${BENCH_ROOT}/offline/genconvit"
readonly OFFICIAL_REPO="https://github.com/erprogs/GenConViT.git"
readonly OFFICIAL_COMMIT="2c1d0bd7eecea94926595781a744e3f4b8b55290"
readonly SOURCE_BUNDLE="${OFFLINE_DIR}/GenConViT-${OFFICIAL_COMMIT}.bundle"
readonly HF_REPO="Deressa/GenConViT"
readonly HF_REVISION="32d6e9e3c931a37971cc756da706cf1eef643372"
readonly ED_FILE="genconvit_ed_inference.pth"
readonly VAE_FILE="genconvit_vae_inference.pth"
readonly ED_SHA256="86f0c2e875016435def7d031b357bda5dc0061367290d73de121186df3f03f8c"
readonly VAE_SHA256="53c627c82d1439fc80e18ac462c1ed6969a3babe5376124a5c38d1c0c88c9042"
readonly MIN_FREE_KB=$((15 * 1024 * 1024))
readonly OFFLINE_ARTIFACTS_ONLY="${GENCONVIT_OFFLINE_ARTIFACTS_ONLY:-0}"

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

[[ "${OFFLINE_ARTIFACTS_ONLY}" =~ ^[01]$ ]] || \
  die 'GENCONVIT_OFFLINE_ARTIFACTS_ONLY must be 0 or 1'

printf '%s\n' '=== GPU inventory: choose a physical index explicitly ==='
command -v nvidia-smi >/dev/null 2>&1 || die 'nvidia-smi is not available'
nvidia-smi

if [[ -z "${GENCONVIT_GPU:-}" ]]; then
  die 'GENCONVIT_GPU is unset. Run: export GENCONVIT_GPU=<idle physical GPU index>'
fi
if [[ ! "${GENCONVIT_GPU}" =~ ^[0-9]+$ ]]; then
  die 'GENCONVIT_GPU must be one numeric physical GPU index'
fi
export GENCONVIT_GPU
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export CUDA_VISIBLE_DEVICES="${GENCONVIT_GPU}"
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export HF_HUB_DOWNLOAD_TIMEOUT=60
export PIP_DEFAULT_TIMEOUT=60

printf 'Selected physical GPU index: %s\n' "${GENCONVIT_GPU}"
nvidia-smi --id="${GENCONVIT_GPU}" \
  --query-gpu=index,uuid,name,memory.total,memory.free,driver_version \
  --format=csv,noheader

mkdir -p \
  "${BENCH_ROOT}/models" \
  "${BENCH_ROOT}/envs" \
  "${WEIGHTS_DIR}" \
  "${BENCH_ROOT}/results/genconvit" \
  "${METADATA_DIR}" \
  "${OFFLINE_DIR}"

[[ -w "${BENCH_ROOT}" ]] || die "work root is not writable by $(id -un): ${BENCH_ROOT}"

df -h "${BENCH_ROOT}"
available_kb="$(df -Pk "${BENCH_ROOT}" | awk 'NR == 2 {print $4}')"
[[ "${available_kb}" =~ ^[0-9]+$ ]] || die 'could not determine free disk space'
(( available_kb >= MIN_FREE_KB )) || \
  die "less than 15 GiB is free under ${BENCH_ROOT}; deployment stopped"

code_source=""
if [[ -e "${REPO_DIR}" ]]; then
  [[ -d "${REPO_DIR}/.git" ]] || die "existing path is not a Git clone: ${REPO_DIR}"
  current_commit="$(git -C "${REPO_DIR}" rev-parse HEAD)"
  [[ "${current_commit}" == "${OFFICIAL_COMMIT}" ]] || \
    die "existing clone is at ${current_commit}, expected ${OFFICIAL_COMMIT}; left untouched"
  [[ -z "$(git -C "${REPO_DIR}" status --porcelain --untracked-files=all)" ]] || \
    die "existing official clone is dirty; left untouched: ${REPO_DIR}"
  code_source="existing_verified_clone"
elif [[ -f "${SOURCE_BUNDLE}" ]]; then
  bundle_heads="$(git bundle list-heads "${SOURCE_BUNDLE}")"
  [[ "${bundle_heads}" == *"${OFFICIAL_COMMIT}"* ]] || \
    die "offline Git bundle does not advertise ${OFFICIAL_COMMIT}: ${SOURCE_BUNDLE}"
  git clone --no-checkout "${SOURCE_BUNDLE}" "${REPO_DIR}"
  git -C "${REPO_DIR}" checkout --detach "${OFFICIAL_COMMIT}"
  git -C "${REPO_DIR}" remote set-url origin "${OFFICIAL_REPO}"
  code_source="offline_git_bundle"
else
  [[ "${OFFLINE_ARTIFACTS_ONLY}" != "1" ]] || \
    die "offline-only mode requires Git bundle: ${SOURCE_BUNDLE}"
  git clone "${OFFICIAL_REPO}" "${REPO_DIR}"
  git -C "${REPO_DIR}" checkout --detach "${OFFICIAL_COMMIT}"
  code_source="github_clone"
fi

[[ "$(git -C "${REPO_DIR}" rev-parse HEAD)" == "${OFFICIAL_COMMIT}" ]] || \
  die 'official commit verification failed'
git -C "${REPO_DIR}" diff --exit-code
[[ -z "$(git -C "${REPO_DIR}" status --porcelain --untracked-files=all)" ]] || \
  die 'official clone must remain clean before deployment continues'

conda_exe=""
if command -v conda >/dev/null 2>&1; then
  conda_exe="$(command -v conda)"
else
  for candidate in \
    "${HOME}/miniconda3/bin/conda" \
    "${HOME}/anaconda3/bin/conda" \
    /home/USER/miniconda3/bin/conda \
    /home/USER/anaconda3/bin/conda \
    /opt/conda/bin/conda; do
    if [[ -x "${candidate}" ]]; then
      conda_exe="${candidate}"
      break
    fi
  done
fi
[[ -n "${conda_exe}" ]] || die 'conda not found; install Miniconda under your own home first'

if [[ ! -x "${ENV_PREFIX}/bin/python" ]]; then
  "${conda_exe}" create --prefix "${ENV_PREFIX}" python=3.10 pip=24.3.1 -y
fi
readonly PYTHON="${ENV_PREFIX}/bin/python"
[[ -x "${PYTHON}" ]] || die "environment Python missing: ${PYTHON}"
"${PYTHON}" -c 'import sys; assert sys.version_info[:2] == (3, 10), sys.version'

"${conda_exe}" install --prefix "${ENV_PREFIX}" -c conda-forge \
  dlib=19.24.6 -y

"${PYTHON}" -m pip install \
  setuptools==75.6.0 \
  wheel==0.45.1

"${PYTHON}" -m pip install \
  torch==2.1.2 \
  torchvision==0.16.2 \
  --index-url https://download.pytorch.org/whl/cu118

"${PYTHON}" -m pip install \
  numpy==1.26.4 \
  PyYAML==6.0.2 \
  Pillow==10.4.0 \
  tqdm==4.66.5 \
  scipy==1.11.4 \
  scikit-learn==1.5.2 \
  scikit-image==0.22.0 \
  opencv-python-headless==4.8.1.78 \
  face-recognition==1.3.0 \
  albumentations==1.3.0 \
  qudida==0.0.4 \
  decord==0.6.0 \
  timm==0.6.5 \
  huggingface-hub==0.36.0

readonly HF_BIN="${ENV_PREFIX}/bin/hf"
[[ -x "${HF_BIN}" ]] || die "hf CLI missing after installation: ${HF_BIN}"
"${HF_BIN}" version

offline_ed="${OFFLINE_DIR}/${ED_FILE}"
offline_vae="${OFFLINE_DIR}/${VAE_FILE}"
installed_ed="${WEIGHTS_DIR}/${ED_FILE}"
installed_vae="${WEIGHTS_DIR}/${VAE_FILE}"
weights_source=""

if [[ -f "${installed_ed}" && -f "${installed_vae}" ]]; then
  weights_source="existing_verified_weights"
elif [[ -e "${installed_ed}" || -e "${installed_vae}" ]]; then
  die "only one installed weight exists; preserve and inspect ${WEIGHTS_DIR}"
elif [[ -f "${offline_ed}" && -f "${offline_vae}" ]]; then
  printf '%s  %s\n' "${ED_SHA256}" "${offline_ed}" | sha256sum -c -
  printf '%s  %s\n' "${VAE_SHA256}" "${offline_vae}" | sha256sum -c -
  cp --reflink=auto -- "${offline_ed}" "${installed_ed}"
  cp --reflink=auto -- "${offline_vae}" "${installed_vae}"
  weights_source="offline_uploaded_weights"
elif [[ -e "${offline_ed}" || -e "${offline_vae}" ]]; then
  die "offline staging contains only one weight; upload both files to ${OFFLINE_DIR}"
else
  [[ "${OFFLINE_ARTIFACTS_ONLY}" != "1" ]] || \
    die "offline-only mode requires both weights under ${OFFLINE_DIR}"
  "${HF_BIN}" download "${HF_REPO}" \
    "${ED_FILE}" \
    "${VAE_FILE}" \
    --revision "${HF_REVISION}" \
    --local-dir "${WEIGHTS_DIR}" \
    --max-workers 2
  weights_source="huggingface_download"
fi

printf '%s  %s\n' "${ED_SHA256}" "${installed_ed}" | sha256sum -c -
printf '%s  %s\n' "${VAE_SHA256}" "${installed_vae}" | sha256sum -c -

"${PYTHON}" - <<'PY'
import dlib
import importlib.metadata
import json
import os
import torch

assert torch.__version__.startswith("2.1.2"), torch.__version__
assert torch.cuda.is_available(), "CUDA unavailable in torch cu118 environment"
assert torch.cuda.device_count() == 1, torch.cuda.device_count()
payload = {
    "torch": torch.__version__,
    "torchvision": importlib.metadata.version("torchvision"),
    "torch_cuda": torch.version.cuda,
    "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
    "visible_gpu": torch.cuda.get_device_name(0),
    "dlib_use_cuda": bool(dlib.DLIB_USE_CUDA),
    "dlib_face_detector_mode": "cnn" if dlib.DLIB_USE_CUDA else "hog",
}
print(json.dumps(payload, indent=2, sort_keys=True))
PY

"${PYTHON}" - <<'PY'
import importlib.metadata
import platform

import decord
from decord import VideoReader, cpu

assert platform.system() == "Linux", platform.platform()
assert platform.machine() == "x86_64", platform.machine()
assert decord.__version__ == "0.6.0", decord.__version__
wheel_metadata = importlib.metadata.distribution("decord").read_text("WHEEL") or ""
known_bad_tag = "Tag: cp36-cp36m-manylinux2010_x86_64"
assert known_bad_tag in wheel_metadata, wheel_metadata
assert VideoReader is not None and cpu is not None
print("decord import probe: OK (upstream WHEEL metadata tag is the known cp36 mis-tag)")
PY

pip_check_status=0
pip_check_output="$("${PYTHON}" -m pip check 2>&1)" || pip_check_status=$?
printf '%s\n' "${pip_check_output}" > "${METADATA_DIR}/pip-check.txt"
if (( pip_check_status != 0 )); then
  if [[ "${pip_check_output}" != 'decord 0.6.0 is not supported on this platform' ]]; then
    printf '%s\n' "${pip_check_output}" >&2
    die 'pip dependency check failed with an unexpected error'
  fi
  printf '%s\n' \
    'WAIVED: decord 0.6.0 has an upstream cp36 WHEEL metadata mis-tag; Linux x86_64 import probe passed.' \
    | tee -a "${METADATA_DIR}/pip-check.txt"
else
  printf '%s\n' "${pip_check_output}"
fi
"${PYTHON}" -m pip freeze > "${METADATA_DIR}/pip-freeze.txt"
git -C "${REPO_DIR}" rev-parse HEAD > "${METADATA_DIR}/official-commit.txt"
printf '%s\n' "${HF_REVISION}" > "${METADATA_DIR}/hf-revision.txt"
printf 'code=%s\nweights=%s\n' \
  "${code_source}" "${weights_source}" \
  > "${METADATA_DIR}/artifact-source.txt"
printf 'offline_artifacts_only=%s\n' "${OFFLINE_ARTIFACTS_ONLY}" \
  >> "${METADATA_DIR}/artifact-source.txt"
printf '%s  %s\n%s  %s\n' \
  "${ED_SHA256}" "${ED_FILE}" \
  "${VAE_SHA256}" "${VAE_FILE}" \
  > "${METADATA_DIR}/weight-sha256.txt"
nvidia-smi --id="${GENCONVIT_GPU}" -q > "${METADATA_DIR}/nvidia-smi-selected-gpu.txt"

# Evaluation disables bytecode writes; tracked or untracked source changes are
# not permitted.
git -C "${REPO_DIR}" diff --exit-code
[[ -z "$(git -C "${REPO_DIR}" status --porcelain --untracked-files=all)" ]] || \
  die 'official clone changed during deployment'

printf '%s\n' 'DEPLOYMENT VERIFIED'
printf '  repo:    %s @ %s\n' "${REPO_DIR}" "${OFFICIAL_COMMIT}"
printf '  env:     %s\n' "${ENV_PREFIX}"
printf '  weights: %s (HF revision %s)\n' "${WEIGHTS_DIR}" "${HF_REVISION}"
printf '  detector mode will be: %s\n' \
  "$("${PYTHON}" -c 'import dlib; print("cnn" if dlib.DLIB_USE_CUDA else "hog")')"
printf '%s\n' 'No evaluation dataset was downloaded or modified.'
