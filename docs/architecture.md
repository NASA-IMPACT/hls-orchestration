## HLS Orchestration Architecture
The HLS system employs three major services for processing and status tracking.
- Step Functions - For workflow management and processing state tracking.
- AWS Batch - For managing scalable compute resources for running HLS algorithms on incoming data.
- Aurora (RDS) Serverless - For durable tracking of processing job status and system state.


### Data flows
Upstream raw Landsat and Sentinel 2 data provided by the USGS and ESA respectively continuously arrives in the HLS system for processing. Utilizing Step Functions, this AWS Batch jobs are initiated to generate HLS L30 and S30 granules from this data.  The following sections use abstract diagrams which are high level representations of more detailed Step Functions to trace how data flows through the HLS system.

#### S30
![S30 diagram](/docs/S30_highlevel_dataflow.png)

Data is continuously downloaded from the ESA International Hub by a separate application (the S2 Serverless Downloader). Once auxiliary MODIS aerosol data is available from the LAADS DAAC, a processing job is created for the granule.  When the job completes its status is logged in the logging database.

Jobs can fail for several reasons.  Some of these failures are expected, if a granule is completely cloud obscured or its solar zenith angle exceeds a specified threshold the job will fail with a known exit code.  Some failures are unexpected, these include SPOT market instance interruptions, inconsistencies with input granules and processing timeouts due to aerosol conditions.  A cron timer periodically retries these unexpected failures.


#### Step Function Chunking
![Step Function Chunking diagram](/docs/step_function_chunking.png)

Error and incompete job reprocessing all operate in a similar way.  We also manage error reprocessing state with Step Functions but Step Functions have several quota restrictions that require workarounds to scale effectively.  The first is the [rate](https://docs.aws.amazon.com/step-functions/latest/dg/limits-overview.html#service-limits-api-action-throttling-general) at which Step Function executions can be started and the second is the [limit](https://docs.aws.amazon.com/step-functions/latest/dg/limits-overview.html#service-limits-state-machine-executions) of events in a single state machine.  To circumvent the start execution limits we restrict the number of failed jobs which are requested from the log database for each cron run and use the state machine map operator to process multiple errors in a single state machine in parallel.  To circumvent the state machine event limits we split the list of queried errors into discrete chunks so that each parallel execution is restricted and won't exceed the quota.


#### L30
![L30 diagram](/docs/L30_highlevel_dataflow.png)
