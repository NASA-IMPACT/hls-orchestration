import boto3
import os
import json
import time

# Create an SNS client
sns = boto3.client('sns')
c2file = os.path.join(os.path.dirname(__file__), "landsat_c2_granules.txt")
with open(c2file, "r") as keys:
    for key in keys:
        granule = key.split("/")[-1].rstrip()
        stac = f"{key.rstrip()}/{granule}_stac.json"
        message = {
            "Records": [{
                "s3": {
                    "bucket": {
                        "name": "usgs-landsat"
                    },
                    "object": {
                        "key": stac
                    }
                }
            }]
        }
        messagestring = json.dumps(message)
        response = sns.publish(
            TopicArn="arn:aws:sns:us-west-2:018923174646:landsat-collection2-simulate",
            Message=messagestring
        )
        print(response)
        time.sleep(2)
