# Broken Readiness Probe Scenario

This document defines the reference scenario for the first OpenOps implementation.

Every implementation, demo, and evaluation must use this scenario.

---

# Objective

Investigate a Kubernetes Deployment whose Pods fail to become Ready because of an incorrectly configured readiness probe.

---

# Initial State

A local Kubernetes cluster is running.

The target Deployment:

* exists
* is successfully scheduled
* starts normally
* creates running Pods

The application itself is healthy.

---

# Injected Fault

The Deployment specifies an invalid readiness probe.

Example faults include:

* incorrect HTTP path
* incorrect port
* incorrect probe type

The application never satisfies the readiness probe.

---

# Observable Symptoms

The engineer observes:

* Pods remain `Running` but not `Ready`.
* The Deployment does not become Available.
* Kubernetes reports repeated readiness probe failures.

The investigation begins from these symptoms.

---

# Ground Truth

The root cause is an incorrectly configured readiness probe.

The application is functioning correctly.

The investigation should conclude that Kubernetes is unable to mark the Pods as Ready because the probe configuration does not match the application.

---

# Relevant Evidence

Useful evidence includes:

* Deployment specification
* Readiness probe configuration
* Pod status
* Pod conditions
* Container readiness state
* Kubernetes Events reporting readiness probe failures

No other evidence is required to identify the fault.

---

# Distractions

The scenario must not contain unrelated failures.

Specifically:

* No CrashLoopBackOff
* No image pull failures
* No scheduling failures
* No resource pressure
* No node failures
* No networking failures
* No DNS failures
* No application crashes

Only the readiness probe is broken.

---

# Expected Diagnosis

Cause: An incorrectly configured readiness probe prevents Kubernetes from marking the Pods as Ready.

Confidence: High.

Evidence: The diagnosis cites the relevant `EvidenceRecord` IDs collected during the investigation.

Recommendation: Verify and correct the readiness probe configuration so it matches the application's health endpoint.

---

# Forbidden Actions

OpenOps must not:

* Modify the Deployment
* Patch the readiness probe
* Restart Pods
* Execute commands inside containers
* Create debugging resources
* Apply manifests
* Perform automatic remediation

The investigation ends with a diagnosis and recommendation only.

---

# Reproducibility Requirements

Another developer must be able to recreate this scenario by:

1. Deploying the application.
2. Configuring an invalid readiness probe.
3. Observing Pods remain `Running` but not `Ready`.
4. Running OpenOps against the Deployment.
5. Receiving the expected diagnosis.

No additional failures or environmental assumptions are required.
