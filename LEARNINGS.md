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
