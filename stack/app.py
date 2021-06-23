import os
from aws_cdk import core
from stack import HlsStack


# Required env settings
STACKNAME = os.environ["HLS_STACKNAME"]

# Optional env settings
if os.getenv("GCC", None) == "true":
    GCC = True
else:
    GCC = False

app = core.App()
if GCC:
    region = os.environ["AWS_DEFAULT_REGION"]
    account = os.environ["HLS_GCC_ACCOUNT"]
    hls_stack = HlsStack(app, STACKNAME, stack_name=STACKNAME,
                         env={"account": account, "region": region})
else:
    hls_stack = HlsStack(app, STACKNAME, stack_name=STACKNAME)

app.synth()
