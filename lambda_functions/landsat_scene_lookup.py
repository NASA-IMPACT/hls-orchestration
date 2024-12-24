import boto3

s3_client = boto3.client("s3")
inputbucket = "usgs-landsat"
s3_basepath = "collection02/level-1/standard/oli-tirs"


def handler(event, context):
    scene_ids = []
    date = event["date"]
    year = date[:4]
    for pathrow in event["pathrows"]:
        print(pathrow)
        path = pathrow[:3]
        row = pathrow[3:]
        prefix = f"{s3_basepath}/{year}/{path}/{row}/"
        list_result = s3_client.list_objects_v2(
            Bucket=inputbucket, Prefix=prefix, RequestPayer="requester", Delimiter="/"
        )
        common_prefixes = list_result.get("CommonPrefixes")
        if common_prefixes:
            updated_key = [
                prefix["Prefix"]
                for prefix in common_prefixes
                if prefix["Prefix"].split("_")[3] == date
            ]
            if len(updated_key) > 0:
                scene_id = updated_key[0].split("/")[-2]
                print(scene_id)
                scene_ids.append(scene_id)
    return {"scenes": scene_ids, "prefix": prefix, "bucket": inputbucket}
