#!/usr/bin/env python3
"""CDK entry point for SynthESG infrastructure deployment."""

import aws_cdk as cdk

from infrastructure.esg_stack import SynthESGStack

app = cdk.App()
SynthESGStack(
    app, "SynthESGStack",
    env=cdk.Environment(region="ap-southeast-5"),
)
app.synth()
