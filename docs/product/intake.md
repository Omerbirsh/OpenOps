# Investigation Intake Contract v0

The CLI accepts one investigation request and validates it before creating `InvestigationState`. Invalid input causes a non-zero CLI exit and no Kubernetes or model call.

## CLI shape

The v0 command is:

```text
openops investigate \
  --cluster-context openops-reader@kind-openops-lab \
  --namespace openops-lab \
  --workload-kind Deployment \
  --workload-name readiness-demo \
  --symptom "Pod is Running but not Ready"
```

The implementation may follow the host shell's line-continuation syntax; the option names and values above are the contract.

## Fields

| Field | Type | v0 rule |
| --- | --- | --- |
| `cluster_context` | non-empty string | Must equal `openops-reader@kind-openops-lab`; there is no implicit current-context fallback and the administrative `kind-openops-lab` context is rejected. |
| `namespace` | non-empty string | Must equal `openops-lab`. |
| `workload_kind` | enum | Must equal `Deployment`. |
| `workload_name` | non-empty string | Must equal `readiness-demo`. |
| `symptom` | string, 1-500 characters | Engineer-provided observation; treated as context, not evidence. |
| `time_window` | optional duration | Applies only to Events. Defaults to `30m`; must be greater than zero and no more than `60m`. |

`time_window` is exposed as `--time-window`. All other fields are required options.

## Validated output

Successful validation produces an immutable investigation objective with the six fields above. The runtime copies that objective into `InvestigationState.objective`.

The runtime must not accept arbitrary resource kinds, namespaces, cluster contexts, Kubernetes verbs, resource paths, commands, or model-authored intake values in v0.

## CLI exit codes

| Code | Meaning |
| --- | --- |
| `0` | Completed investigation report rendered. |
| `2` | CLI usage, intake, or local configuration error; no investigation ran. |
| `3` | Kubernetes authentication or authorization failure. |
| `4` | Target, collection, normalization, or no-evidence failure. |
| `5` | Decision-model configuration or call failure. |
| `6` | Candidate diagnosis failed mechanical validation. |

Errors are written to standard error. A diagnosis report is written to standard output only for exit code `0`.
