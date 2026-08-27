# Repository Guidelines

## Project Structure & Module Organization

This repository is a research workspace centered on auditable synthetic-content detection reviews. Keep the layout predictable:

- `src/` — application and research code, organized by feature or pipeline stage.
- `tests/` — automated tests mirroring the relevant `src/` structure.
- `assets/` — small, versioned fixtures and documentation images; keep large datasets and model weights outside Git.
- `scripts/` — repeatable data-preparation, training, evaluation, or utility commands.
- `docs/` — methodology, experiment notes, and reproducibility instructions.
- `research/reports/` — one report per modality.
- `research/source-snapshots/` — dated official-source and repository metadata snapshots.
- `research/datasets/` — dataset roles, download references, and licensing gaps.
- `research/` root — evidence ledger, coverage matrix, evaluation protocol, and reading indexes.

## Build, Test, and Development Commands

Python evaluation wrappers live in `src/video_eval/`. Install and test from a clean checkout:

```bash
pip install -r requirements.txt
python -m pytest tests/video_eval -q
```

Server probe and smoke (Linux eval host):

```bash
bash scripts/probe_server.sh
python -m src.video_eval.run_eval --config configs/video_eval.yaml --track cross_dataset --model lipforensics --dry-run
bash scripts/smoke_one_model.sh lipforensics
```

Copy `configs/video_eval.example.yaml` and `configs/datasets.manifest.example.json` to the untracked local names before running. Do not commit datasets, weights, credentials, or `results/*.json` experiment dumps. Avoid inventing extra build tooling.


## Coding Style & Naming Conventions

Use UTF-8 Markdown, descriptive lowercase filenames, and stable dated snapshot names such as `image-evidence-YYYY-MM-DD.md`. Keep claims concise and attach every metric to its dataset, split, generator, and degradation condition. Use bold only for conclusions and statuses; preserve tables for cross-scheme comparisons. If Python modules are later added, use four-space indentation, type hints, Ruff, and `pytest`.

## Testing Guidelines

For research artifacts, check local Markdown links and confirm that “verified”, “candidate”, and “待核验” statuses are used consistently. Any later Python tests should use `pytest`, name files `test_*.py`, and use small fixtures rather than private or large media datasets. Document required external data and expected results.

## Commit & Pull Request Guidelines

There is no Git history yet, so no existing commit convention can be inferred. Use short imperative commit subjects, such as `Add face-crop validation`, and keep each commit focused. Pull requests should explain the motivation, summarize the approach, list validation commands and results, identify dataset/model changes, and include screenshots or sample outputs when visual behavior changes. Never commit credentials or unlicensed data.

## Security & Configuration

Keep secrets in environment variables or an untracked `.env` file; provide `.env.example` with safe placeholders. Treat downloaded videos, faces, and model artifacts as sensitive: verify licensing, minimize retained personal data, and document provenance and access requirements.
