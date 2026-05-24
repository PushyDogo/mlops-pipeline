#!/usr/bin/env bash
  set -euo pipefail

  NAMESPACE="${NAMESPACE:-ml-test}"

  echo "Cleaning MLOps project resources from namespace: ${NAMESPACE}"

  echo "Helm releases in namespace:"
  helm list -n "${NAMESPACE}" || true

  echo "Uninstalling Helm releases..."
  for release in $(helm list -n "${NAMESPACE}" -q); do
    echo "Uninstalling ${release}"
    helm uninstall "${release}" -n "${NAMESPACE}" || true
  done

  echo "Deleting remaining namespaced Kubernetes resources..."
  kubectl delete all --all -n "${NAMESPACE}" --ignore-not-found=true
  kubectl delete configmap --all -n "${NAMESPACE}" --ignore-not-found=true
  kubectl delete secret --all -n "${NAMESPACE}" --ignore-not-found=true
  kubectl delete pvc --all -n "${NAMESPACE}" --ignore-not-found=true
  kubectl delete serviceaccount --all -n "${NAMESPACE}" --ignore-not-found=true
  kubectl delete role --all -n "${NAMESPACE}" --ignore-not-found=true
  kubectl delete rolebinding --all -n "${NAMESPACE}" --ignore-not-found=true
  kubectl delete ingress --all -n "${NAMESPACE}" --ignore-not-found=true

  echo
  echo "Namespace was not deleted."
  echo "To delete the namespace too, run:"
  echo "kubectl delete namespace ${NAMESPACE}"
