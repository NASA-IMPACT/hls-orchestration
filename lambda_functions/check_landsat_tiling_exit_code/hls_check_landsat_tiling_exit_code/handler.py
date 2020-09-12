def handler(event, context):
    if 1 in event or "nocode" in event:
        return False
    else:
        return True
