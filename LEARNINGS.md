# Learnings

This file records concrete gotchas, decisions, and interview-ready explanations
as we build the pipeline.

## Week 0: Bootstrap

- The workspace had only `PLAN.md`; no implementation existed yet.
- `kubectl` and `uv` were available, but `kind`, `helm`, and standalone
  `kustomize` were not on PATH.
- `python3` was available as Python 3.13.5, while `python` was not on PATH.
- The current Kubernetes context points at an EKS cluster, and `kubectl get nodes`
  succeeds when network access is allowed.
- An empty `.git` directory existed, which prevents this directory from being a
  valid Git repository until it is removed or replaced.

## Week 1: Baseline Training and Tracking

- One month of NYC yellow taxi data had 2,964,624 raw rows.
- After cleaning invalid targets, invalid fares, invalid distances, invalid durations, missing values, and
out-of-month timestamps, the training dataset had 2,752,434 rows.
- A random train/test split gave MAE 0.9885 and RMSE 2.0673.
- A time-based split gave MAE 0.9666 and RMSE 1.9680.
- The raw January 2024 file contained a small number of invalid timestamps, including records outside
January 2024. This showed why data validation matters before model evaluation.
- We saved metrics manually first to understand the pain MLflow solves.
- MLflow Tracking now records params, metrics, model artifacts, metrics artifacts, timestamps, and run
IDs.
- Python dependency compatibility mattered: MLflow stable required compatible versions of pandas, pyarrow,
protobuf, and setuptools.
- DVC tracks large files by committing small `.dvc` pointer files to Git and storing actual file contents
in a DVC cache/remote.
- A broad `.gitignore` pattern can accidentally interfere with DVC file discovery unless `.dvc` pointer
files and their parent directories are explicitly unignored.
- A local DVC remote proved the workflow before introducing MinIO/S3.
- Deleting local data and restoring it with `dvc pull` reproduced the same training metrics: MAE 0.9666
and RMSE 1.9680.