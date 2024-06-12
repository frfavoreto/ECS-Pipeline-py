"""Definitions of container service and capacity provider running application tasks"""
from aws_cdk import Stack, Duration
from aws_cdk import aws_autoscaling as autoscaling
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import custom_resources as cr
from constructs import Construct


class ECS(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs,
    ):
        super().__init__(scope, construct_id, **kwargs)

        myVPC = ec2.Vpc(self, "EcsClusterVPC",
            subnet_configuration = [
                ec2.SubnetConfiguration(
                name = 'Public-Subent',
                subnet_type=ec2.SubnetType.PUBLIC
                )
            ],
            max_azs=1
         )

        ecs_cluster = ecs.Cluster(
            self,
            "my-ecs-cluster",
            cluster_name="my-ecs-cluster",
            container_insights=True,
            vpc=myVPC,
        )
        
        port_mapping = ecs.PortMapping(
            container_port=80,
            protocol=ecs.Protocol.TCP
        )

        asg=autoscaling.AutoScalingGroup(self, "EcsASG",
            vpc=myVPC,
            instance_type=ec2.InstanceType("t3.xlarge"),
            machine_image=ecs.EcsOptimizedImage.amazon_linux2(),
            # desired_capacity=2,
            max_capacity=5,
            min_capacity=2,
        )

        capacity_provider = ecs.AsgCapacityProvider(
            self,
            "my-capacity-provider",
            capacity_provider_name="my-capacity-provider",
            enable_managed_scaling=True,
            enable_managed_termination_protection=False,  # if False adds LifecycleHook
            auto_scaling_group=asg,
        )

        ecs_cluster.add_asg_capacity_provider(capacity_provider)

        task_definition_project = ecs.Ec2TaskDefinition(
            self,
            "my-task-definition",
            family="my-task-definition",
        )

        self.container_project = task_definition_project.add_container(
            "my-app-container",
            container_name="my-container",
            image=ecs.ContainerImage.from_registry("amazon/amazon-ecs-sample"),
            cpu=2048,
            memory_reservation_mib=1324,
            logging=ecs.LogDriver.aws_logs(stream_prefix="Felgan"),
            health_check=ecs.HealthCheck(
                command=["CMD-SHELL", "curl -f http://172.17.0.2:80 || exit 1"],
                interval=Duration.seconds(60),  # max 300 sec
                retries=2,  # max 10
                start_period=Duration.seconds(240),
                timeout=Duration.seconds(10),
            ),
        )

        self.container_project.add_port_mappings(port_mapping)

        self.ec2_service_project = ecs.Ec2Service(
            self,
            "ecs-service",
            service_name="ecs-service",
            task_definition=task_definition_project,
            placement_strategies=[
                ecs.PlacementStrategy.spread_across_instances(),
            ],
            max_healthy_percent=200,
            min_healthy_percent=100,
            cluster=ecs_cluster,
            desired_count=2,
            capacity_provider_strategies=[
                ecs.CapacityProviderStrategy(
                    capacity_provider=capacity_provider.capacity_provider_name,
                    base=1,
                    weight=1,
                )
            ],
        )

        asg_parameters = {
            "AutoScalingGroupName": asg.auto_scaling_group_name,
            "ForceDelete": True,
        }

        asg_sdk_call_params = {
            "action": "deleteAutoScalingGroup",
            "service": "AutoScaling",
            "parameters": asg_parameters,
            "physical_resource_id": cr.PhysicalResourceId.of(asg.node.id),
        }

        asg_force_delete = cr.AwsCustomResource(
            self,
            "my-cr-delete-asg",
            install_latest_aws_sdk=False,
            on_delete=cr.AwsSdkCall(**asg_sdk_call_params),
            policy=cr.AwsCustomResourcePolicy.from_sdk_calls(
                resources=cr.AwsCustomResourcePolicy.ANY_RESOURCE
            ),
        )

        # This fixes the CFN mess when deleting the stack. CR forces ASG deletion and avoids CFN breaking into DELETE_FAILED
        asg_force_delete.node.add_dependency(asg)
        asg_force_delete.node.add_dependency(ecs_cluster)

