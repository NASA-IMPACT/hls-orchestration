import os
from aws_cdk import core
from stack import HlsStack
        
STACKNAME = os.getenv("STACKNAME", "hls")

app = core.App()
hls_stack = HlsStack(
    app,
    STACKNAME,
    stack_name=STACKNAME,
)
app.synth()
