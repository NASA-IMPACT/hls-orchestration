import os
from aws_cdk import core
from stack import HlsStack

STACKNAME = os.getenv("HLS_STACKNAME", "hls")

app = core.App()
hls_stack = HlsStack(app, STACKNAME, stack_name=STACKNAME,env={'account': '418960797021', 'region': 'us-west-2'})
app.synth()
