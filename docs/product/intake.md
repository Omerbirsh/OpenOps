# Investigation Input Contract

Every investigation starts with a single intake request.

## Required Fields

`cluster_context` - Kubernetes cluster context to investigate 
`namespace` - Namespace containing the workload 
`workload_kind` - Kubernetes workload type
`workload_name` - Name of the workload 
`symptom` - Short description of the observed problem 

## Optional Fields

`time_window` - Time range to constrain evidence collection (If not provided, the fallback is the last 30 minutes) 
