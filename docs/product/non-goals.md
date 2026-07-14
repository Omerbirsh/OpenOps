# v0 Non-Goals

The following capabilities are outside the first implementation and must not shape its module structure or control flow.

## Evidence and investigations

- Application or container logs
- Prometheus, Grafana, Elasticsearch, or third-party evidence
- Additional Kubernetes incident scenarios
- Arbitrary Kubernetes resources or cluster-wide discovery
- Cross-cluster investigation

## Runtime

- Model-directed tool selection
- Adaptive or iterative investigation loops
- Generic tool or plugin registries
- Multiple model calls, providers, or agents
- Investigation memory or background scheduling
- Automatic retries or autonomous recovery behavior

## Interfaces and infrastructure

- Web interface
- REST or gRPC service
- Database or persistent raw-artifact store
- Cloud deployment
- Production authentication or multi-user authorization
- Production-scale performance work

## Actions

- Kubernetes writes
- Pod or node command execution
- Automatic remediation
- Applying the report recommendation

These are deferred capabilities, not hidden requirements for v0.
