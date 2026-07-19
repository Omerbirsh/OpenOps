# Broken-Readiness Demonstration

The Phase 2 demonstration uses the exact lifecycle and CLI commands in the
[quick start](../user/quick-start.md).

## Verified ground truth

- NGINX remains running and answers its valid `/` endpoint.
- The injected Deployment probe requests `/ready` on port 80.
- `/ready` returns HTTP 404.
- The Pod remains Running but not Ready, with zero container restarts.
- The Deployment has zero available replicas.
- Kubernetes emits an `Unhealthy` readiness-probe Event containing HTTP 404.

OpenOps collects only the configured probe, bounded Deployment status, bounded Pod status, and
target Events. Its diagnosis must cite all three evidence categories and recommend aligning the
probe with a successful endpoint without applying the change.

The checked-in `broken-readiness-trace.json` is generated from the live cluster with the deterministic
fake provider. It demonstrates the sanitized trace shape without containing raw Event messages,
Kubernetes objects, or credentials. The live provider produces the same schema and is independently
validated by the runtime.
