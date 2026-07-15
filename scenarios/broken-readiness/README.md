# Broken Readiness Scenario

This directory is the filesystem boundary for the first disposable `kind` scenario. Its behavioral contract is defined in [the scenario specification](../../docs/scenarios/broken-readiness.md).

Phase 1 intentionally contains no Kubernetes manifests or setup scripts: nothing in this phase can create a cluster or claim that the scenario is runnable. Phase 2 will add only the manifests and deterministic setup/teardown assets consumed by the first live workflow.
