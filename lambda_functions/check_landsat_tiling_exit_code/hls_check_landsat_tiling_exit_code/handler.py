def handler(event, context):
    if 1 in event or None in event:
        return False
    else:
        return True
