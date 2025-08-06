# HLS Orchestration Database Maintenance

This is a playbook for maintenance of the state tracking database that the
HLS production team has been performing monthly. This maintenance is intended to
help prevent failures within our processing system associated with database issues
(usually timeouts) until we can move to an architecture that doesn't rely on this
state tracking database.

These queries include a filter on the log record timestamp (`ts`) that should be adjusted
to match the maintenance date. We generally want to avoid changing rows within the last
~1 week.

These queries include references to `run_count >= 3` since we only attempt a granule 3 times
before giving up. By resetting the run count to 0 we indicate that the granule should be
picked up by the granule reprocessing task for retries.

## Enforce Retention Policy

As a first step we always want to purge jobs that have succeeded. We do this in two steps,

1. Check how many rows exist.
2. Delete the successful rows.

### Sentinel

The Sentinel logging table has a `succeeded: bool` status column, but others require checking the
AWS Batch job info.

First check how many the delete will affect,
```sql
select count(*) from landsat_ac_log
where jobinfo->'Container'->>'ExitCode' = '0'
and ts < '2025-07-15'
```

Delete successes before some date:

```sql
delete from sentinel_log
where succeeded
and ts < '2025-07-15'
```

### Landsat

The Landsat logging tables do NOT have the `succeeded: bool` column, so we must check the AWS Batch
job status stored in the `jobinfo` column.

```sql
delete from landsat_mgrs_log
where jobinfo->'Container'->>'ExitCode' = '0'
and ts < '2025-05-01'
```

```sql
delete from landsat_ac_log
where jobinfo->'Container'->>'ExitCode' = '0'
and ts < '2025-07-15'
```

## Logging failures

We want to reset the job run count for any granules that have been attempted 3 times
but do not have job statuses. The lack of a job status indicates that the job logging
step had an issue writing to the database.

### Sentinel
```sql
select count(*) from sentinel_log
where jobinfo is null
and run_count >= 3
and ts < '2025-07-15'
```

To mark for reprocessing:

```sql
update sentinel_log
set run_count = 0
where jobinfo is null
and run_count >= 3
and ts < '2025-07-15'
```

### Landsat AC Log

The count of job logging failures should be relatively low for Landsat AC jobs.

```sql
select count(*) from landsat_ac_log
where jobinfo is null
and run_count >= 3
and ts < '2025-07-15'
```

To mark for reprocessing:

```sql
update landsat_ac_log
set run_count = 0
where jobinfo is null
and run_count >= 3
and ts < '2025-07-15'
```


### Landsat MGRS Log

```sql
select count(*) from landsat_mgrs_log
where jobinfo is null
and run_count >= 3
and ts < '2025-07-15'
```

To mark for reprocessing:

```sql
update landsat_mgrs_log
set run_count = 0
where jobinfo is null
and run_count >= 3
and ts < '2025-07-15'
```

## Unexpected Failures

We also want to clear up unexpected failures (usually Spot market issues) for jobs
that cannot be retried on their own.

### Landsat AC Log

The Landsat AC ("atmospheric compensation") step has some acceptable failure exit
codes (137, 3, 4) that we do not need to retry.

```sql
select count(*) from landsat_ac_log
where jobinfo->'Container'->>'ExitCode' not in ('0', '137', '3', '4')
and run_count >= 3
and ts < '2025-07-15'
```

To mark for reprocessing:

```sql
update landsat_ac_log
set run_count = 0
where jobinfo->'Container'->>'ExitCode' not in ('0', '137', '3', '4')
and run_count >= 3
and ts < '2025-07-15'
```

### Landsat MGRS Log

```sql
select count(*) from landsat_mgrs_log
where jobinfo->'Container'->>'ExitCode' != '0'
and run_count >= 3
and ts < '2025-07-15'
```

To mark for reprocessing:

```sql
update landsat_mgrs_log
set run_count = 0
where jobinfo->'Container'->>'ExitCode' != '0'
and run_count >= 3
and ts < '2025-07-15'
```

### Sentinel

```sql
select count(*) from sentinel_log
where unexpected_error
  and run_count >= 3
  and ts < '2025-07-15'
```

To mark for reprocessing:

```sql
update sentinel_log
set run_count = 0
where unexpected_error
  and run_count >= 3
  and ts < '2025-07-15'
```
