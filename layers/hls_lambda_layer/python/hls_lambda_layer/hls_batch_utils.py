import json


def parse_jobinfo(key, event):
    if "Cause" in event[key].keys():
        try:
            jobinfo = json.loads(event[key]["Cause"])
            jobid = jobinfo["JobId"]
            jobinfostring = json.dumps(jobinfo)
        except ValueError:
            jobinfo = {"cause": event[key]["Cause"]}
            jobid = None
            jobinfostring = json.dumps(jobinfo)
    else:
        jobinfo = event[key]
        jobid = jobinfo["JobId"]
        jobinfostring = json.dumps(event[key])

    try:
        exitcode = jobinfo["Attempts"][0]["Container"]["ExitCode"]
    except KeyError:
        exitcode = "nocode"
    except TypeError:
        exitcode = "nocode"

    output = {
        "jobinfo": jobinfo,
        "jobid": jobid,
        "jobinfostring": jobinfostring,
        "exitcode": exitcode,
    }
    return output
