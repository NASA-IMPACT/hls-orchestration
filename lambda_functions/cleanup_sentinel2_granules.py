"""
HLS: Remove Sentinel-2 granules after successful processing

This Lambda function is connected in our workflow after the check for
failures in the "success" pathway. As such we do not need to ensure the
granule has been successfully processed within this scope.

The only complication involved is handling of "twin" granules because
we need to ensure the first granule processing workflow does not delete
the 2nd of the "twin" granules. A "twin" granule occurs when the same
tile and date are acquired twice due to the satellite switching receiving
stations during the downlink. Two granules exist for the same date and tile,
and for complete coverage we must process and combine the two granules
together.

A "twin" granule is processed in two steps,

1. The first of the "twin" is downloaded into the input bucket, triggering a
   workflow to process this granule.
2. This first workflow only finds one of the two granules that will eventually be
   downloaded, and only processes the first.
3. The second of the "twin" granules is downloaded into the input bucket, triggering
   a workflow to process this granule.
4. This second workflow finds two input granule IDs, and processes them both.

In this scenario we only want to delete the inputs for the second workflow.
"""

import os

import boto3


s3 = boto3.client("s3")
bucket = os.getenv("SENTINEL_INPUT_BUCKET", None)
if bucket is None:
    raise Exception("No Input Bucket set")


def handler(event: dict, context: dict):
    # We may receive 2 granules split by a comma if this is a twin granule workflow
    granules = event["granule"].split(",")

    prefixes = {granule[0:-6] for granule in granules}
    if len(prefixes) != 1:
        raise ValueError(f"Received {len(prefixes)} granule prefixes")
    prefix = list(prefixes)[0]

    response = s3.list_objects_v2(
        Bucket=bucket,
        Prefix=prefix,
    )

    granule_zips = [obj["Key"] for obj in response["Contents"]]

    # We have three possible cases,
    # 1. Non-twin granule (1 ID, 1 zip)
    # 2. Twin granule input and twin granule job (2 IDs, 2 zips)
    if len(granules) == len(granule_zips):
        if len(granules) > 1:
            print(f"Deleting inputs of twin granule case: {granule_zips}")
        else:
            print(f"Deleting input of single granule case: {granule_zips[0]}")

        for granule_zip in granule_zips:
            s3.delete_object(Bucket=bucket, Key=granule_zip)
        return granule_zips

    # 3. Twin granules downloaded but only one was processed in this workflow
    else:
        print(
            "Twin granule case detected but this workflow did not process it. "
            f"Skipping deletion (IDs={granules}, zips={granule_zips})"
        )
        return []
