# Same-Day Acceptance Checklist

An implementation is considered complete only if all of the following are true.

## Success Criteria

- [ ] An investigation can be started with the required input fields.
- [ ] The runtime investigates the defined readiness probe scenario.
- [ ] The runtime collects evidence from Kubernetes-native sources.
- [ ] The runtime produces a structured investigation report.
- [ ] The report includes:
  - [ ] Cause
  - [ ] Confidence
  - [ ] Evidence references
  - [ ] Alternatives or uncertainty
  - [ ] Recommendation
- [ ] Running the same investigation against the same cluster produces equivalent results.

## Failure Conditions

The implementation is incomplete if any of the following occur.

- [ ] The investigation cannot be started from the required input.
- [ ] The runtime fails to identify the readiness probe incident.
- [ ] The report is missing any required field.
- [ ] The diagnosis cannot be traced back to collected evidence.
- [ ] The implementation depends on features outside the defined same-day scope.