# AWS Elastic Container Service

AWS CloudFormation template for deploying ECS Cluster with 3 services and using EC2 container instance. EC2 instance will be deployed using AutoScalingGroup.

This template also deploys VPC, subnets, routable, internetgateway. For nginx container service loadbalancer accessible from public internet will be deployed.
In addition, ElasticCache with Redis engine and RDS instance with Postgres engine will be deployed. 

## Validate template:

```
 aws cloudformation validate-template --template-body file://ecs-cluster.json
```
## Deploy template

```
 aws cloudformation create-stack --stack-name ecs-cluster --template-body file://ecs-cluster.json --capabilities CAPABILITY_NAMED_IAM
```

## Troubleshooting

If cloudformation stack will be stuck, you can ssh into EC2 instance and troubleshoot if all required containers are running, check if ecs agent is running, check container logs.
I.e public elastic ip can be attached temporarily.

Get AWS optimized image AMI for ECS:

```
  aws ssm get-parameters --names /aws/service/ecs/optimized-ami/amazon-linux-2/recommended --region eu-west-1
```