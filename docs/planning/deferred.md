# Deferred Capabilities

This file records capabilities intentionally excluded from v0. It does not define designs or active tasks.

## Next investigation capabilities

- Application and container log collection
- Additional Kubernetes failure scenarios
- Broader workload and resource support
- Deterministic retries and richer partial-failure policies
- Sanitized trace persistence and replay
- Machine-readable report output

## Later evidence and runtime capabilities

- Prometheus and other external evidence sources
- Multiple clusters or providers
- Persistent investigation storage and memory
- Adaptive planning or model-directed tool selection
- Generic collector, tool, or plugin systems
- Background or service execution

## Later product capabilities

- REST or gRPC API
- Web interface
- Multi-user authentication and authorization
- Cloud and production deployment
- Controlled remediation and Kubernetes writes

## Planning rules

- Deferred items must not create current modules, interfaces, schema fields, or dependencies.
- A capability moves into scope only with a concrete scenario and acceptance gate.
- The current Markdown contracts take precedence over earlier planning assumptions in `BuildingRoadMap.pdf`.
- In particular, the roadmap's Phase 2 container-log collector is superseded: v0 uses Deployment, Pod, and Event evidence only.
