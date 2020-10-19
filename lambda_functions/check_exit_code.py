def handler(event, context):
    if event == 1 or event == "nocode":
        return False
    else:
        return True
