import aws_cdk as cdk
from constructs import Construct
from ecs_pipeline.ecs_pipeline_cluster_stack import ECS

class MyPipelineAppStage(cdk.Stage):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ECSStack = ECS(self, "ECSstack")
