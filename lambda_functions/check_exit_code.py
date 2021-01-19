def handler(event, context):
    # Exit code 3 is invalid solar zenith angle.
    # Exit code 4 is cloud cover over threshold.
    if event == 0 or event == 3 or event == 4:
        return True
    else:
        return False
