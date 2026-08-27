#!/usr/bin/env bash
# Run smoke, formal custom evaluation, or a deterministic smoke repeat.

set -Eeuo pipefail
IFS=$'\n\t'

readonly MODE="${1:-}"
readonly BENCH_ROOT="/data/USER/deepfake-bench"
readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly PYTHON="${BENCH_ROOT}/envs/genconvit/bin/python"
readonly REPO_DIR="${BENCH_ROOT}/models/GenConViT"
readonly DATA_ROOT="${BENCH_ROOT}/datasets"
readonly RESULT_ROOT="${BENCH_ROOT}/results/genconvit"
readonly SEED=20260818

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

usage() {
  cat >&2 <<'EOF'
Usage: run_genconvit_eval.sh {smoke|full|repeat-smoke}

  smoke         8 real + 8 fake pipeline check; not performance evidence
  full          200 real + 200 fake custom evaluation; requires smoke first
  repeat-smoke  rerun the 8+8 smoke and require bit-identical scores

Before every invocation, inspect nvidia-smi and explicitly export, for example:
  export GENCONVIT_GPU=2
EOF
  exit 64
}

case "${MODE}" in
  smoke)
    dataset_name="mentor_swap_200_smoke"
    dataset_dir="${DATA_ROOT}/${dataset_name}"
    out_dir="${RESULT_ROOT}/${dataset_name}"
    expected_real=8
    expected_fake=8
    evidence_role="pipeline_smoke_only"
    ;;
  full)
    dataset_name="mentor_swap_200"
    dataset_dir="${DATA_ROOT}/${dataset_name}"
    out_dir="${RESULT_ROOT}/${dataset_name}"
    expected_real=200
    expected_fake=200
    evidence_role="custom_evaluation"
    ;;
  repeat-smoke)
    dataset_name="mentor_swap_200_smoke"
    dataset_dir="${DATA_ROOT}/${dataset_name}"
    out_dir="${RESULT_ROOT}/${dataset_name}_repeat"
    expected_real=8
    expected_fake=8
    evidence_role="pipeline_smoke_only"
    ;;
  *)
    usage
    ;;
esac

printf '%s\n' '=== GPU inventory: choose a physical index explicitly ==='
command -v nvidia-smi >/dev/null 2>&1 || die 'nvidia-smi is not available'
nvidia-smi
[[ -n "${GENCONVIT_GPU:-}" ]] || \
  die 'GENCONVIT_GPU is unset. Run: export GENCONVIT_GPU=<idle physical GPU index>'
[[ "${GENCONVIT_GPU}" =~ ^[0-9]+$ ]] || \
  die 'GENCONVIT_GPU must be one numeric physical GPU index'
export GENCONVIT_GPU
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export CUDA_VISIBLE_DEVICES="${GENCONVIT_GPU}"
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export PYTHONHASHSEED="${SEED}"
export PYTHONDONTWRITEBYTECODE=1

nvidia-smi --id="${GENCONVIT_GPU}" \
  --query-gpu=index,uuid,name,memory.total,memory.free,driver_version \
  --format=csv,noheader

[[ -x "${PYTHON}" ]] || die "environment missing; run deploy_genconvit.sh first: ${PYTHON}"
[[ -d "${REPO_DIR}/.git" ]] || die "official clone missing: ${REPO_DIR}"
[[ -r "${dataset_dir}/real" && -r "${dataset_dir}/fake" ]] || \
  die "read access to real/fake dataset directories is required: ${dataset_dir}"
[[ ! -e "${out_dir}" ]] || \
  die "output already exists and will not be overwritten: ${out_dir}"

if [[ "${MODE}" == "full" ]]; then
  smoke_dir="${RESULT_ROOT}/mentor_swap_200_smoke"
  [[ -f "${smoke_dir}/summary.json" ]] || \
    die "verified smoke result required first: ${smoke_dir}/summary.json"
  "${PYTHON}" "${SCRIPT_DIR}/verify_genconvit_result.py" \
    --run-dir "${smoke_dir}" \
    --expected-real 8 \
    --expected-fake 8 \
    --allow-pipeline-smoke
fi

"${PYTHON}" "${SCRIPT_DIR}/genconvit_dataset_eval.py" \
  --repo-dir "${REPO_DIR}" \
  --dataset-dir "${dataset_dir}" \
  --dataset-name "${dataset_name}" \
  --out-dir "${out_dir}" \
  --frames 15 \
  --seed "${SEED}" \
  --bootstrap-seed "${SEED}" \
  --bootstrap-resamples 2000 \
  --precision fp32 \
  --expected-real "${expected_real}" \
  --expected-fake "${expected_fake}" \
  --hash-videos \
  --evidence-role "${evidence_role}"

verify_args=(
  --run-dir "${out_dir}"
  --expected-real "${expected_real}"
  --expected-fake "${expected_fake}"
)
if [[ "${evidence_role}" == "pipeline_smoke_only" ]]; then
  verify_args+=(--allow-pipeline-smoke)
fi
if [[ "${MODE}" == "repeat-smoke" ]]; then
  verify_args+=(
    --repeat-run-dir "${RESULT_ROOT}/mentor_swap_200_smoke"
    --repeat-atol 0
  )
fi
"${PYTHON}" "${SCRIPT_DIR}/verify_genconvit_result.py" "${verify_args[@]}"

git -C "${REPO_DIR}" diff --exit-code
[[ -z "$(git -C "${REPO_DIR}" status --porcelain --untracked-files=all)" ]] || \
  die 'official clone changed during evaluation'

printf 'DONE: %s\n' "${out_dir}"
printf '%s\n' 'Reporting label:'
printf '  %s custom evaluation / OOD status unverified\n' "${dataset_name}"
if [[ "${evidence_role}" == "pipeline_smoke_only" ]]; then
  printf '%s\n' 'This smoke output is pipeline evidence only, not performance evidence.'
else
  printf '%s\n' 'Do not write this custom result to indomain.json.'
fi
