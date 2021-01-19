def handler(event, context):
    # Exit code 5 is empty tile output.
    valid_exits = [0, 5]
    valid = True
    for code in event:
        if code not in valid_exits:
            valid = False
    return valid
