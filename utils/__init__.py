from typing import Dict
import json

def aws_env(env: Dict):
    env_parsed=[]
    for key, value in env.items():
        env_parsed.append(
            {
                'name': key,
                'value': value
            }
        )
    return json.dumps(env_parsed)

def align(code_doc: str):
    code_split=code_doc.split('\n')
    spaces=code_split.pop()
    return '\n'.join([l.replace(spaces,'',1) for l in code_split])