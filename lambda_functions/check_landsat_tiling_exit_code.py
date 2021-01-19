def handler(event, context):
    # Exit code 5 is empty tile output.
    valid_exits = [0, 5]
    valid = True
    for code in event:
        if isinstance(code, int):
            if code not in valid_exits:
                valid = False
        else:
            if code == "nocode":
                valid = False
    return valid
