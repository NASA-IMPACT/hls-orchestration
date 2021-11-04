import json
from typing import Dict


def aws_env(env: Dict):
    env_parsed = []
    for key, value in env.items():
        env_parsed.append({"name": key, "value": value})
    return json.dumps(env_parsed)


def align(code_doc: str):
    code_split = code_doc.split("\n")
    spaces = code_split.pop()
    return "\n".join([line.replace(spaces, "", 1) for line in code_split])
