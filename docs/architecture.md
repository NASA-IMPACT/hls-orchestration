## HLS Orchestration Architecture
The HLS system employs three major services for processing and status tracking.
- Step Functions - For workflow management and processing state tracking.
- AWS Batch - For managing scalable compute resources for running HLS algorithms on incoming data.
- Aurora (RDS) Serverless - For durable tracking of processing job status and system state.


### Data flows
Upstream raw Landsat and Sentinel 2 data provided by the USGS and ESA respectively continuously arrive in the HLS system for processing. Utilizing Step Functions, AWS Batch jobs are initiated to generate HLS L30 and S30 granules from this data.  The following sections use abstract diagrams which are high level representations of more detailed Step Functions to trace how data flows through the HLS system.

### S30
![S30 diagram](/docs/S30_highlevel_dataflow.png)

Data is continuously downloaded from the ESA International Hub by a separate application (the S2 Serverless Downloader). Once auxiliary MODIS aerosol data is available from the LAADS DAAC, a processing job is created for the granule.  When the job completes its status is logged in the logging database.  If successful the output is written to an external bucket which  triggers notifications for LPDAAC and GIBS that there is new data ready for ingestion.

Jobs can fail for several reasons.  Some of these failures are expected, if a granule is completely cloud obscured or its solar zenith angle exceeds a specified threshold the job will fail with a known exit code.  Some failures are unexpected, these include SPOT market instance interruptions, inconsistencies with input granules and processing timeouts due to aerosol conditions.  A cron timer periodically retries these unexpected failures.

### Step Function Chunking
![Step Function Chunking diagram](/docs/step_function_chunking.png)

Error and incomplete job reprocessing all operate in a similar way.  We manage error reprocessing state with Step Functions but Step Functions have several quota restrictions that require workarounds to scale effectively.  The first is the [rate](https://docs.aws.amazon.com/step-functions/latest/dg/limits-overview.html#service-limits-api-action-throttling-general) at which Step Function executions can be started and the second is the [limit](https://docs.aws.amazon.com/step-functions/latest/dg/limits-overview.html#service-limits-state-machine-executions) of events in a single state machine.  To circumvent the start execution limits we restrict the number of failed jobs which are requested from the log database for each cron run and use the state machine map operator to process multiple errors in a single state machine in parallel.  To circumvent the state machine event limits we split the list of queried errors into discrete chunks so that each parallel execution is restricted and will not exceed the event quota.

### L30
![L30 diagram](/docs/L30_highlevel_dataflow.png)

Due to alignment differences between Landsat collection path rows and the MGRS grid system used by the HLS products, the processing pipeline for L30 products is more complex.  Unlike the Sentinel 2 granules which are directly downloaded into a bucket prior to processing, USGS publishes Landsat data in a public bucket and advertises the publication of new granules via an SNS topic.  The L30 processing workflow is triggered by new SNS messages.  When a notification enters the pipeline, the granule's path row and acquisition information is logged in the logging database.  In addition, we determine the MGRS grid squares which the granule intersects and also log those.  When auxiliary MODIS aerosol data is available, an atmospheric correction processing job is created for the granule.  When the job completes its status is logged in the logging database and if successful the intermediate atmospheric correction data is written to an internal bucket.  

The state machine then proceeds to the MGRS tiling portion of the processing pipeline.  Using the list of MGRS tiles that the granule intersects which was generated at the start of the process, for each MGRS tile we check if all the path rows it intersects have been processed.  If they have, a processing job is created which reads all of the atmospherically corrected path rows from the intermediate bucket and generates an L30 tile.  AWS Batch also has quota restrictions which require workarounds.  Because of the parallel nature of the MGRS/L30 tiling, there is the concern of exceeding the [transactions per second limit](https://docs.aws.amazon.com/batch/latest/userguide/service_limits.html) for batch job submission. To circumvent this we introduce random [jitter](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/) in the state machine to spread the submissions over a longer period.  If the tiling job is successful the output is written to an external bucket which triggers notifications for LPDAAC and GIBS that there is new data ready for ingestion.

### MGRS Incompletes
![MGRS Incompletes diagram](/docs/MGRS_incompletes.png)

Because Landsat data arrives from USGS with irregular frequency and becuase there is no guarantee that all path rows for a specific MGRS tile will succeed in the atmospheric correction step, we have an additional cron process that runs to generate L30 tiles where all of the expected path rows are not available.  This process queries the log database for MGRS tiles older than a specified threshold where L30 tiles haven't been created yet.  Using the chunked Step Function approach described above, these are processed using whatever path rows are available for the tile a processing job is submitted which reads these available atmospherically corrected path rows from the intermediate bucket.

### LAADS Data Downloading
![LAADS data diagram](/docs/LAADS_aux_data.png)

The LASRC algorithm used for HLS atmospheric correction requires a variety of auxiliary data derived from MODIS Aqua/Terra products.  The code used to generate the consolidated products used in this processing is packaged as C library with a Python wrapper.  A cron rule periodically submits a processing job to the AWS Batch queue to check if new MODIS data is available which is then downloaded, consolidated and written to both an EFS mount (used by all of the batch jobs described above) and an S3 bucket for archival storage.
