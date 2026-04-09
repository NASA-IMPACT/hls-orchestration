## Task Metrics

The HLS science container supports optional per-task metrics collection for Batch jobs running the Sentinel-2 (S30),
Landsat AC (L30-AC), and Landsat Tile (L30-Tile) workflows. When enabled, each instrumented task emits a structured log
event in
[CloudWatch Embedded Metrics Format (EMF)](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format.html)
at the end of its execution. CloudWatch Logs Insights can query the raw log lines, while CloudWatch Metrics
automatically extracts the numeric values for dashboards and alarms.

The primary use case is performance comparison across code or configuration changes — for example, measuring the
wall-clock time and peak memory of Fmask v4 vs. v5 side-by-side using experiment dimensions.

### Enabling Metrics

Two environment variables control metrics. Set them in the GitHub environment for your deployment target (or in
`environment.sh` locally) before running `cdk deploy`.

| Variable                           | Required              | Description                                                                                                                                                            |
| ---------------------------------- | --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `HLS_METRIC_LOG_GROUP_NAME`        | Yes                   | Name of the CloudWatch Logs log group (e.g. `/hls/nextgen/metrics`). The log group is always created by the CDK stack regardless of whether instrumentation is active. |
| `HLS_INSTRUMENT_SCIENCE_CONTAINER` | No (default: `false`) | Set to `true` to forward `METRIC_LOG_GROUP_NAME` to containers and grant `logs:PutLogEvents` to Batch task roles.                                                      |

Setting `HLS_METRIC_LOG_GROUP_NAME` without enabling `HLS_INSTRUMENT_SCIENCE_CONTAINER` is safe and intentional: it
ensures the log group exists before instrumentation is turned on, so there is no "log group already exists" conflict
when toggling.

The log stream for each job is the `AWS_BATCH_JOB_ID`. The log group and stream must exist before metrics can be emitted
— the science container will not create them. The log group is managed by the CDK stack with a 90-day retention policy
and `RemovalPolicy.RETAIN` (it will not be deleted on stack teardown).

### Experiment Dimensions

Any environment variable prefixed with `HLS_EXPERIMENT_` in the GitHub environment is baked into the Batch JobDefinition
and forwarded to the container when `HLS_INSTRUMENT_SCIENCE_CONTAINER=true`. The prefix is stripped to form the
CloudWatch dimension name:

```
HLS_EXPERIMENT_FMASK_VERSION=v5   →   dimension: fmask_version=v5
HLS_EXPERIMENT_LASRC_VERSION=2.1  →   dimension: lasrc_version=3.5.8
```

These dimensions appear on every metric emitted during the job, making it straightforward to filter or compare in
CloudWatch Metrics and Logs Insights.

### Metrics Collected

Three metrics are captured per instrumented task execution:

| Metric            | Unit      | Description                                                |
| ----------------- | --------- | ---------------------------------------------------------- |
| `runtime_seconds` | Seconds   | Wall-clock time from task start to finish                  |
| `peak_memory_mb`  | Megabytes | Peak RSS across the Python process and all child processes |
| `max_cpu_percent` | Percent   | Maximum combined CPU utilisation across the process tree   |

Memory and CPU are sampled at 1-second intervals in a background polling thread, covering both Python-level work and any
subprocesses (e.g. the LaSRC or Fmask executables).

### Instrumented Tasks

Not every task is instrumented — only the computationally significant ones opt in. This also only works with the
"nextgen" `hls-science-container` that updates the within-container orchestration.

| Workflow | Task                                 |
| -------- | ------------------------------------ |
| S30      | `RunFmask`, `RunFmaskV5`, `RunLaSRC` |
| L30-AC   | `RunFmask`, `RunFmaskV5`, `RunLaSRC` |
| L30-Tile | `ProcessPathRows`, `RunNbar`         |

### Querying Metrics

**CloudWatch Logs Insights** — raw EMF records are queryable as structured JSON:

```
fields @timestamp, task_name, runtime_seconds, peak_memory_mb, fmask_version
| filter ispresent(fmask_version)
| sort @timestamp desc
```

**CloudWatch Metrics** — EMF records are auto-extracted into the `HLS/Tasks` namespace with the following dimensions per
record:

- `task_class` — Python class name of the task
- `task_name` — instance name assigned in the workflow
- `job_id` — `AWS_BATCH_JOB_ID`
- `granule_id` — set for per-granule mapped tasks (S30 and L30-AC)
- Any `HLS_EXPERIMENT_*` dimensions defined at deploy time
