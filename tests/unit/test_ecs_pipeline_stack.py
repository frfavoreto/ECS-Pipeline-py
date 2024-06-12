import aws_cdk as core
import aws_cdk.assertions as assertions

from ecs_pipeline.ecs_pipeline_stack import EcsPipelineStack

# example tests. To run these tests, uncomment this file along with the example
# resource in ecs_pipeline/ecs_pipeline_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = EcsPipelineStack(app, "ecs-pipeline")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
