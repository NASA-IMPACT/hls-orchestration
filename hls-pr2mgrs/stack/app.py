"""app."""

from aws_cdk import core
from stack import LambdaStack

app = core.App()
LambdaStack(app, "HLSPathRow2MGRS")
app.synth()
