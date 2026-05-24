# MLOps Taxi Tip Prediction

This repository is a slow, interview-oriented walkthrough of a complete MLOps
pipeline on Kubernetes.

The project predicts NYC yellow taxi tip amount from tabular trip data. The
model will stay deliberately simple; the learning value is in the production
system around it:

1. Reproducible local training
2. Data versioning with DVC
3. Experiment tracking and model registry with MLflow
4. Cluster services on Kubernetes
5. Feature management with Feast
6. Workflow orchestration with Airflow and Kubeflow Pipelines
7. Serving with FastAPI first, then KServe
8. Monitoring with Evidently, Prometheus, and Grafana
9. Drift-triggered retraining

## Current Checkpoint

We are at **Week 0: Bootstrap**.

The goal of this checkpoint is not to train a model yet. The goal is to make the
project reproducible enough that every later MLOps tool has a clear reason to
exist.

## Local Environment Snapshot

Checked on 2026-05-24:

- `kubectl` is installed.
- `uv` is installed.
- `python3` is installed at version 3.13.5.
- `kind` is not installed.
- `helm` is not installed.
- Standalone `kustomize` is not installed, though `kubectl` includes kustomize
  support.
- The current Kubernetes context points to an EKS cluster and `kubectl get nodes`
  succeeds when network access is allowed.
- The `.git` directory currently exists but is empty, so this directory is not
  recognized as a Git repository yet.

## Learning Style

For each stage we will answer four questions before implementing:

1. What pain are we solving?
2. What tool or framework are we introducing?
3. What tradeoff does that tool create?
4. What interview story can we tell from this step?

Then we will implement the smallest useful version and record gotchas in
`LEARNINGS.md`.

## Repository Layout

```text
data/                  # DVC-tracked data later
src/
  features/            # Feature engineering and Feast definitions later
  training/            # Training scripts and pipeline components
  serving/             # FastAPI and KServe serving code
  monitoring/          # Drift and service monitoring jobs
pipelines/
  airflow_dags/        # Airflow DAGs
  kfp_pipelines/       # Kubeflow Pipelines definitions
infra/
  k8s/                 # Kubernetes manifests and Helm values
  terraform/           # Optional cloud IaC later
notebooks/             # EDA only, not production pipeline code
tests/                 # Unit, data, training, and serving tests
```

## Next Step

Checkpoint 0.1 is to finish the local bootstrap:

1. Decide whether this project should use the existing EKS cluster or a local
   throwaway `kind` cluster.
2. Install `helm`.
3. Resolve Git initialization.
4. Add the first tiny data download script.
