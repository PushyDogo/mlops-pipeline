# MLOps Sprint: K8s-native tabular pipeline, 4–6 weeks

## The shape of the project

Build an end-to-end MLOps pipeline for a **tabular regression problem** on a **real Kubernetes cluster**, gradually adding tools at each stage and feeling the pain each one is designed to solve. The whole thing converges into a **closed-loop retraining system**: data lands, features are computed, a model trains, gets registered, gets served, gets monitored, drift is detected, and that drift triggers retraining.

The model itself stays boring on purpose — a LightGBM/XGBoost regressor is enough. The interview value comes from the platform around it, not the model.

### Concrete problem: NYC Taxi tip prediction

Predict the tip amount for a NYC yellow-taxi trip.

Why this dataset:
- Hosted publicly, partitioned by month — gives *real, natural time-based concept drift* (COVID year, fare structure changes) so the monitoring/retraining loop fires on real signal.
- Tabular, mixed numeric + categorical, missing values — realistic feature-engineering pain.
- Big enough to feel slow but small enough to run on a laptop's k8s.

Alternatives: credit-default (imbalanced classification, good for monitoring) or Kaggle's "store sales" forecasting.

---

## The full stack (and why each tool earns its place)

| Stage | Tool | Problem it solves | Tradeoff / interview hook |
|---|---|---|---|
| Source control | Git + GitHub | Code versioning | — |
| Data versioning | **DVC** | Code-versioning doesn't handle big files; pin which data version produced which model | DVC vs LakeFS vs Delta Lake — pointer-based vs branched data |
| Experiment tracking | **MLflow Tracking** | "Which hyperparams produced this score?" stops being answerable after run 5 | MLflow vs Weights & Biases vs Neptune |
| Model registry | **MLflow Registry** | Promote model versions through stages (None → Staging → Production) with audit trail | MLflow Registry vs SageMaker Model Registry vs custom |
| Feature store | **Feast** | Training/serving skew: features computed differently in batch vs online | Feast vs Tecton vs Hopsworks; offline-online sync |
| Workflow orchestration (data) | **Apache Airflow** | Scheduled DAGs for data ingestion + batch feature computation | Airflow vs Prefect vs Dagster |
| ML pipeline orchestration | **Kubeflow Pipelines (KFP v2)** | ML-native pipeline with artifact lineage, GPU scheduling, k8s-native | KFP vs Argo Workflows vs Airflow for ML |
| Object storage | **MinIO** (S3-compatible) | Artifacts, datasets, MLflow backend — runs in your cluster | MinIO vs S3/GCS in production |
| Metadata DB | **PostgreSQL** | Backend for MLflow, Airflow, Feast registry | — |
| Container registry | **GHCR** or local | Hosting your built images | — |
| Model serving | **KServe** | Autoscaling, canary, GPU, traffic-split — declaratively on k8s | KServe vs Seldon Core vs BentoML vs raw FastAPI |
| API gateway | **FastAPI** (wrapper stage) | Build it the "wrong" way first so you appreciate KServe | — |
| Monitoring (model) | **Evidently AI** | Detect data drift, prediction drift, target drift | Evidently vs WhyLabs vs Arize |
| Monitoring (system) | **Prometheus + Grafana** | Latency, error rate, throughput — the SRE side | — |
| CI/CD | **GitHub Actions** | Test on push, build images, lint DAGs, run a smoke pipeline | — |
| Infra-as-code (optional W6) | **Terraform + Helm** | Reproducible cluster | — |

You won't install everything upfront. You'll add tools as the pain emerges.

---

## Pacing: 4–6 weeks, ~10 hrs/week

Weeks 1–4 are the core. Weeks 5–6 are polish + a "real cloud cluster" upgrade. If the sprint runs short, ending after W4 still leaves you with a complete, defensible project.

---

## Week 0 (½ day) — Bootstrap

Before W1, knock out the prerequisites once:

1. **Local k8s cluster.** Install `kind` (preferred — works on Linux trivially, faster than minikube, supports multi-node). Bring up a 3-node cluster.
2. **`kubectl`, `helm`, `kustomize`** installed.
3. **Python 3.14 + `uv`** (or poetry) for dependency management. `uv` is the current standard — faster than pip, deterministic.
4. **Repo layout.** Single mono-repo:
   ```
   mlops/
     data/                  # DVC-tracked
     src/
       features/
       training/
       serving/
       monitoring/
     pipelines/
       airflow_dags/
       kfp_pipelines/
     infra/
       k8s/                 # Helm values, manifests
       terraform/           # later
     notebooks/             # EDA only, not pipeline code
     tests/
     .github/workflows/
   ```
5. **Download a small slice** of the taxi data (e.g. 2 months of yellow taxi from NYC TLC) to develop against.

**Output of W0:** `kubectl get nodes` returns 3 nodes; `python -c "import sklearn"` works; repo is initialized and pushed.

---

## Week 1 — Baseline model + experiment tracking + data versioning
*Goal: take the chaos of "I had a model that worked last week and now I can't reproduce it" and make it impossible.*

### Steps
1. **EDA in a notebook.** Understand the data. Drop the notebook in `notebooks/`; do NOT use it in the pipeline.
2. **Baseline training script** (`src/training/train.py`): load CSV → split → train LightGBM regressor → log MAE/RMSE → save model.pkl. ~80 lines.
3. **Add MLflow Tracking** (run locally via `mlflow ui` for now). Wrap the script with `mlflow.start_run()`, log params, metrics, the model itself. Run it 5 times with different params and explore the UI.
4. **Add DVC.** Initialize DVC, push the raw data to an S3-compatible remote (use MinIO once it's up in W2, or a local `dvc-remote` directory for now). Pin the dataset version in `data.dvc` and commit it.
5. **Reproducibility test.** Delete your local data + model, then run `dvc pull && python src/training/train.py` and confirm you get the *same* metrics.

### Interview talking points
- Why hashing data matters: experiment tracking is meaningless if the data underneath silently changes.
- Difference between MLflow Tracking (runs), Models (artifacts), Registry (stages).
- "Why not just commit the CSV?" → git LFS limits, blob-store economics, branching semantics.

### Common gotchas you should hit
- Forgetting to log the *random seed* — reproducibility breaks.
- MLflow `log_model` vs `log_artifact` — when to use which.

### Modeling notes (since you're learning the modeling side too)
- We'll cover: train/val/test split (why we split, why a holdout matters), cross-validation, why LightGBM beats linear regression on tabular data, what MAE vs RMSE measure and when each matters.

---

## Week 2 — Get MLflow + MinIO + Postgres running on Kubernetes
*Goal: stop running services on your laptop. Everything is in the cluster from here on.*

### Steps
1. **Helm install Postgres** (bitnami chart) — backend store for MLflow.
2. **Helm install MinIO** — artifact store for MLflow, DVC remote, and future Feast offline store.
3. **Deploy MLflow Tracking Server** as a Deployment+Service in k8s, configured with Postgres backend and MinIO artifact store. Expose via NodePort or Ingress.
4. **Re-run W1's training** against the cluster MLflow. Same script, just `MLFLOW_TRACKING_URI` env var pointing at the k8s service.
5. **Migrate DVC remote to MinIO.** `dvc remote add ... s3://...` with MinIO endpoint.
6. **Write a Helm `values.yaml`** capturing your config. This is your IaC starting point.

### Interview talking points
- Why separate backend store (metadata) and artifact store (blobs) — scale characteristics differ.
- Service discovery in k8s — how training pods find the MLflow server (cluster DNS).
- Secrets management — MinIO credentials via k8s Secrets, not env files in git.

### Gotchas to hit
- Pod can't reach MLflow → debug with `kubectl exec`, `kubectl logs`, ClusterIP vs NodePort.
- MinIO bucket policy / path-style URL config — classic MLflow pain.

---

## Week 3 — Feature store + orchestration (Airflow + Kubeflow Pipelines)
*Heaviest week. Two orchestrators on purpose, because you'll see why they're not interchangeable.*

### Part A: Feature store with Feast (~3 hrs)
1. **Feast init.** Define an entity (`trip_id` or `pickup_location_id`), a feature view, and the offline source (Parquet on MinIO).
2. **Materialize features** into the online store (Redis, also Helm-installed).
3. **Refactor training** to pull features from Feast's offline store instead of reading CSVs directly.
4. **Test training/serving symmetry.** Write a function that fetches a single record's features from the online store; confirm it matches what training saw.

### Part B: Airflow on k8s (~3 hrs)
1. **Helm install Airflow** with the KubernetesExecutor (each task = a pod).
2. **Write a DAG** `daily_data_ingest`: download latest taxi data → validate schema → land in MinIO → trigger Feast materialization.
3. **Schedule + test.** Trigger it manually, then let it run on schedule.

### Part C: Kubeflow Pipelines (~4 hrs)
1. **Install KFP standalone** (no need for full Kubeflow — just `kfp-standalone` manifests).
2. **Convert your training script to a KFP pipeline** with these components: `load_features` → `train` → `evaluate` → `register_to_mlflow`.
3. **Run it from the KFP UI.** Inspect the artifact lineage view — this is the killer feature.

### Interview talking points
- **The big one:** Why two orchestrators? Airflow owns data-engineering and scheduled jobs; KFP owns ML-pipeline-shaped work where artifact lineage and the ability to swap components matters. In practice teams pick one or hybrid — be ready to argue both sides.
- Training/serving skew is the #1 silent killer of ML in prod — Feast's whole reason for existing.
- Why materialization exists — batch-computed features can't be recomputed at inference latency.

### Gotchas to hit
- Airflow KubernetesExecutor pod templates — image-pull, resource limits.
- KFP v2 component vs v1 — v2 is the current standard, lots of old tutorials are v1.
- Feast online vs offline store consistency lag.

---

## Week 4 — Serving + monitoring + the closed loop
*Goal: model goes from registry to a live HTTP endpoint, and a drift event triggers retraining.*

### Part A: Serve it the "naive" way first (~2 hrs)
1. **FastAPI wrapper** around the registered model. Pull `model://taxi-tip/Production` from MLflow at startup. Containerize. Deploy as a k8s Deployment.
2. **Hit it with `curl`.** Note what's missing: no autoscaling, no canary, no traffic-split, no GPU support, you're managing the rollout yourself.

### Part B: KServe (~3 hrs)
1. **Install KServe** via Helm (depends on Knative + cert-manager — follow KServe install docs).
2. **Define an `InferenceService`** pointing at your MLflow model URI. KServe handles autoscaling (scale-to-zero), model pulling, predictor pod lifecycle.
3. **Canary deploy** a new model version with 10% traffic — observe the split with `curl`.

### Part C: Monitoring (~3 hrs)
1. **Evidently AI** — write a job that compares yesterday's predictions/features against a training reference snapshot, computes drift metrics (PSI, KS test, Wasserstein), writes a report.
2. **Schedule the drift job** via Airflow daily.
3. **Prometheus + Grafana** (kube-prometheus-stack Helm chart) — instrument the FastAPI/KServe endpoint, scrape predict-latency / error-rate / RPS. Build one Grafana dashboard.

### Part D: Close the loop (~2 hrs)
1. **Drift threshold** — if Evidently's drift score exceeds `X`, the Airflow task **triggers the KFP retraining pipeline** via its REST API.
2. **KFP pipeline** retrains, evaluates, and **only registers** the new model if it beats the current Production model by margin `Y`.
3. **Promote** to Staging programmatically; require a manual MLflow-UI click to promote Staging → Production. (Don't auto-promote; that's a real-world safety pattern.)

### Interview talking points
- Why scale-to-zero matters for cost.
- Canary vs blue-green vs shadow deployment — when to use each.
- The difference between **data drift** (input distribution change), **prediction drift** (output distribution change), and **concept drift** (input→output relationship change). You can only directly observe the first two; you infer the third from delayed-label evaluation.
- Why auto-promote-to-prod is dangerous — model can pass validation and still be wrong in subtle ways. Human-in-the-loop gate.

---

## Week 5 — CI/CD + tests + the cloud upgrade

### Steps
1. **GitHub Actions:**
   - On every PR: lint (`ruff`), type-check (`mypy`), unit-test, validate Airflow DAGs parse, validate KFP pipelines compile, build+push training image to GHCR.
   - On `main` merge: bump image tag, optionally trigger a smoke training run.
2. **Tests you actually need:**
   - Data validation: schema test on the ingested data (use `pandera` or `great_expectations`).
   - Training: a tiny synthetic dataset that trains in seconds, smoke-tests the pipeline.
   - Serving: a request/response contract test against the InferenceService.
3. **Cloud upgrade (optional but high-value for interviews):**
   - GKE Autopilot or AWS EKS free tier. Take your Helm charts as-is — `kubectl apply -f` against the cloud cluster.
   - Swap MinIO → GCS/S3. Swap local Postgres → Cloud SQL / RDS.
   - Note what broke and what didn't. That's a great interview anecdote.

---

## Week 6 — IaC, polish, and your "demo script"

1. **Terraform** the cloud resources (cluster, buckets, DB). Even just one module is enough to talk about.
2. **README + architecture diagram** — Excalidraw or draw.io. One diagram showing the whole flow: ingestion → features → training → registry → serving → monitoring → retraining.
3. **A 5-minute demo recording** — `asciinema` or screen capture. Run a pipeline, show drift detection, show a retrain trigger. This is what you reference in interviews.
4. **A `LEARNINGS.md`** — one line per gotcha you hit and how you solved it. This is gold for behavioral interviews.

---

## What I deliberately left out

- **Kafka / streaming features** — adds a week of complexity for marginal interview value at your level. Mention you know it exists.
- **GPU / large-model serving** — your tabular model doesn't need it. The KServe pattern transfers to GPU directly.
- **Multi-tenant / RBAC / governance** — interesting at staff level, not for first MLOps interview.
- **A second model** — temptation will be strong to add one. Don't. One model done well > two models done shallow.

---

## How we execute each week

When starting a week:
1. Re-read the week's goal and pick the first concrete sub-step.
2. Work through it — explain choices, surface gotchas before you hit them.
3. End the week by adding to `LEARNINGS.md`.

---

## Source notes

- [Kanerika — Kubeflow vs Airflow vs Prefect (2026)](https://kanerika.com/blogs/mlops-orchestration/)
- [Valohai — Kubeflow vs Argo](https://valohai.com/blog/kubeflow-vs-argo/)
- [DataCamp — Top 30 MLOps Interview Questions (2026)](https://www.datacamp.com/blog/mlops-interview-questions)
- [DeviDevs — MLOps Tools Comparison 2026](https://devidevs.com/blog/mlops-tools-comparison-2026-complete-stack)
- [Medium — End-to-end MLOps on Kubernetes (Mar 2026)](https://medium.com/@nsalexamy/building-a-production-ready-end-to-end-mlops-pipeline-on-kubernetes-full-walkthrough-aeb5b87cad60)
