#!/usr/bin/env python3
import os
import aws_cdk as cdk
from ecs_pipeline.ecs_pipeline_stack import EcsPipelineStack


app = cdk.App()
EcsPipelineStack(app, "CDKEcsPipeline",
    env=cdk.Environment(account="879316307891", region="eu-west-1")
    )

app.synth()
        