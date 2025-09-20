#!/usr/bin/env python3
import aws_cdk as cdk
from infrastructure.esg_stack import ESGReportingStack

app = cdk.App()

# Deploy to Malaysia region (ap-southeast-5) as required
ESGReportingStack(
    app, 
    "ESGReportingStack",
    env=cdk.Environment(
        region="ap-southeast-5"  # Malaysia region
    )
)

app.synth()
