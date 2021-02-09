import os
import boto3
import random

client = boto3.client('batch')
s3 = boto3.resource('s3')
input_bucket = 'hls-sentinel-validation-scenes'
bucket = s3.Bucket(input_bucket)
jobqueue = os.getenv("HLSSTACK_SENTINELJOBQUEUEEXPORT")
jobdefinition = os.getenv("HLSSTACK_SENTINELJOBDEFINITION")

granule_list = bucket.objects.filter(Delimiter='/', Prefix='cloud_free_google/')
for granule in granule_list:
    granule_id = os.path.splitext(granule.key.split('/')[1])[0]
    response = client.submit_job(
        jobName=str(random.randint(1, 1000)),
        jobQueue=jobqueue,
        jobDefinition=jobdefinition,
        containerOverrides={
            'command': ['export && sentinel.sh'],
            'environment': [
                {
                    "name": "GRANULE_LIST",
                    "value": granule_id
                },
                {
                    "name": "INPUT_BUCKET",
                    "value": f'{input_bucket}/cloud_free_google'
                },
                {
                    "name": "LASRC_AUX_DIR",
                    "value": "/var/lasrc_aux"
                },
                {
                    "name": "DEBUG_BUCKET",
                    "value": "hls-debug-output"
                },
                {
                    "name": "OMP_NUM_THREADS",
                    "value": "2"
                },
                {
                    "name": "REPLACE_EXISTING",
                    "value": "replace"
                },
            ],
        }
    )
    print(response)
