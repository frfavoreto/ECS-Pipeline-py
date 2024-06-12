import aws_cdk as cdk
from constructs import Construct
from aws_cdk.pipelines import CodePipeline, CodePipelineSource, ShellStep
from ecs_pipeline.ecs_pipeline_app_stage import MyPipelineAppStage
import ecs_pipeline.accounts as accounts

class EcsPipelineStack(cdk.Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        pipeline =  CodePipeline(self, "Pipeline",
                        pipeline_name="CDKEcsPipeline",
                        self_mutation=False, # to avoid immediate pipeline action when still developing the resources
                        cross_account_keys=True, # need it for cross-account deployments
                        synth=ShellStep("Synth",
                            input=CodePipelineSource.git_hub("frfavoreto/EcsPipeline", "main"),
                            commands=["npm install -g aws-cdk",
                                "python -m pip install -r requirements.txt",
                                "cdk synth"]
                        )
        )
        
        test_stage = pipeline.add_stage(MyPipelineAppStage(self, "testEcsDeployment", 
            env=cdk.Environment(account=accounts.envs['TEST_ACC'], region="eu-west-1"),
            )
        )
        # test_stage.add_pre(ManualApprovalSetp('PromoteToProd'))

        prod_stage = pipeline.add_stage(MyPipelineAppStage(self, "prodEcsDeployment", 
            env=cdk.Environment(account=accounts.envs['PROD_ACC'], region="eu-west-1")
            )
        )

    # If we wanted to deploy stages in parallel, this would be:
        # wave = pipeline.add_wave("allInParalel")
        # wave.add_stage(MyPipelineAppStage(self, "testEcsDeployment", 
        #             env=cdk.Environment(account="914808949154", region="eu-west-1"))
        # )
        
        # wave.add_stage(MyPipelineAppStage(self, "prodEcsDeployment", 
        #             env=cdk.Environment(account="879316307891", region="eu-west-1"))
        # )