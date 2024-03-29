#!/usr/bin/env python
import cdktf
from constructs import Construct
from cdktf import App, Fn, TerraformStack, Token
from imports.aws.rds_cluster_instance import RdsClusterInstance
from imports.aws.rds_cluster_parameter_group import RdsClusterParameterGroup
from imports.aws.rds_cluster import RdsCluster
from imports.aws.db_parameter_group import DbParameterGroup, DbParameterGroupParameter
from imports.aws.cloudwatch_metric_alarm import CloudwatchMetricAlarm
from imports.aws.sns_topic import SnsTopic
from imports.aws.db_subnet_group import DbSubnetGroup
from imports.aws.data_aws_caller_identity import DataAwsCallerIdentity
from imports.aws.data_aws_ecr_repository import DataAwsEcrRepositoryImageScanningConfiguration
from imports.aws.data_aws_iam_policy_document import DataAwsIamPolicyDocument, DataAwsIamPolicyDocumentStatement, DataAwsIamPolicyDocumentStatementPrincipals
from imports.aws.db_instance import DbInstance
from imports.aws.ecr_repository import EcrRepository, EcrRepositoryImageScanningConfiguration
from imports.aws.eks_cluster import EksCluster, EksClusterVpcConfig
from imports.aws.iam_role import IamRole
from imports.aws.iam_role_policy_attachment import IamRolePolicyAttachment
from imports.aws.kms_key import KmsKey
from imports.aws.provider import AwsProvider
from imports.aws.route_table_association import RouteTableAssociation
from imports.aws.s3_access_point import S3AccessPoint
from imports.aws.s3_bucket import S3Bucket, S3BucketServerSideEncryptionConfiguration, S3BucketServerSideEncryptionConfigurationRule, S3BucketServerSideEncryptionConfigurationRuleApplyServerSideEncryptionByDefault

from imports.aws.s3_bucket_metric import S3BucketMetric, S3BucketMetricFilter
from imports.aws.s3_bucket_server_side_encryption_configuration import S3BucketServerSideEncryptionConfigurationA, S3BucketServerSideEncryptionConfigurationRuleA, S3BucketServerSideEncryptionConfigurationRuleApplyServerSideEncryptionByDefaultA
from imports.aws.vpc import Vpc
from imports.aws.subnet import Subnet
from imports.aws.internet_gateway import InternetGateway
from imports.aws.route_table import RouteTable, RouteTableRoute
from imports.aws.security_group import SecurityGroup
from imports.aws.security_group_rule import SecurityGroupRule



class MyStack(TerraformStack):
    def __init__(self, scope: Construct, id: str, dbname: str, instance_class: str, password: str, username: str, master_password: str):
        super().__init__(scope, id)
        
#------------------------------INFRASTRUCTUTRE STACK---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
        
        AwsProvider(self, 'Aws', region="us-east-1")

#--------------------------------------NETWORK---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
        my_vpc = Vpc(self, 'MyVpc',
                     cidr_block='10.0.0.0/16',
                     enable_dns_hostnames=True,
                     enable_dns_support=True,
                     instance_tenancy='default',
                     tags={"Name": "E-Vpc"}
                     )

        internet_gateway = InternetGateway(self, "gw",
                                           tags={"Name": "igw"},
                                           vpc_id=my_vpc.id
                                           )

        public_subnet = Subnet(self, 'PublicSubnet',
                               cidr_block="10.0.3.0/24",
                               availability_zone="us-east-1a",
                               map_public_ip_on_launch=True,
                               vpc_id=my_vpc.id,
                               tags={"Name": "Public_Subnet"}
                               )
        
        private_subnet = Subnet(self, 'PrivateSubnet',
                                cidr_block="10.0.5.0/24",
                                availability_zone="us-east-1b",
                                map_public_ip_on_launch=True,
                                vpc_id=my_vpc.id,
                                tags={"Name": "Private_Subnet"}
                                )

        db_subnet = Subnet(self, 'DbSubnet',
                           cidr_block="10.0.1.0/24",
                           availability_zone="us-east-1c",
                           map_public_ip_on_launch=True,
                           vpc_id=my_vpc.id,
                           tags={"Name": "Database_Subnet"}
                           )

        public_route_table = RouteTable(self, 'PublicRouteTable',
                                        vpc_id=my_vpc.id,
                                        tags={"Name": "PRT"}
                                        )

        RouteTable(self, "PublicRoute",
                    route=[
                        RouteTableRoute(
                            cidr_block="0.0.0.0/0",  
                            gateway_id=internet_gateway.id
                        )
                    ],
                    tags={
                        "Name": "PublicRoute"
                    },
                    vpc_id=my_vpc.id
                    )

        routetableassociation = RouteTableAssociation(self, 'PublicRouteTableAssociation',
                                                      subnet_id=public_subnet.id,
                                                      route_table_id=public_route_table.id
                                                      )
        
         # Add Nat Gateway
        
        private_route_table = RouteTable(self, 'PrivateRouteTableAssociation',
                                         vpc_id=my_vpc.id,

                                         tags={"Name": "PrivateRt"}
                                         )
        
        RouteTableAssociation(self, 'PrivateRouteAssociation',
                      subnet_id=private_subnet.id,
                      route_table_id=private_route_table.id  
                      )

        
        db_route_table = RouteTable(self, 'DbRouteTable',
                                    vpc_id=my_vpc.id,
                                    tags={"Name": "Database_Route_Table"}
                                    )
        
        RouteTableAssociation(self, 'DbRouteAssociation',
                              subnet_id=db_subnet.id,
                              route_table_id=db_route_table.id
                              )
        
#--------------------------------------SECURITY GROUP--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#

        security_group = SecurityGroup(self, "SG",
                                      name   =   "vpc-sg",
                                      vpc_id = my_vpc.id,

                                      tags={
                                          "Name" : "vpc-sg"
                                      }
                      
                                       )
        SecurityGroupRule(self, "SGR_SSH", 
                          security_group_id = security_group.id,
                          type        = "ingress",
                          cidr_blocks = ["10.0.5.0/24"],
                          from_port   = 22,
                          to_port     = 22,
                          protocol    = "tcp"
                          )
        
        SecurityGroupRule(self, "SGR_HTTP", 
                          security_group_id = security_group.id,
                          type        = "ingress",
                          cidr_blocks = ["10.0.3.0/24"],
                          from_port   = 80,
                          to_port     = 80,
                          protocol = "tcp"
                          )
        
        SecurityGroupRule(self, "SGR_MYSQL", 
                          security_group_id = security_group.id,
                          type        = "ingress",
                          cidr_blocks = ["10.0.1.0/24"],
                          from_port   = 3306,
                          to_port     = 3306,
                          protocol = "tcp"
                          )
        
        assume_role = DataAwsIamPolicyDocument(self, "assume_role",
                                               statement = [DataAwsIamPolicyDocumentStatement(
                                                   actions = ["sts:AssumeRole"],
                                                   effect  = "Allow",
                                                   principals = [DataAwsIamPolicyDocumentStatementPrincipals(
                                                       identifiers = ["eks.amazonaws.com"],
                                                       type        = "Service"
                                                   )
                                                   ]
                                               )
                                               ]
                                        )
        
#--------------------------------------EKS IAM---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
        
        eks_role=IamRole(self, "eks_role",
            assume_role_policy=Token.as_string(
                Fn.jsonencode({
                    "Statement": [{
                        "Action": "sts:AssumeRole",
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "eks.amazonaws.com"
                        },
                        "Sid": ""
                    }
                    ],
                    "Version": "2012-10-17"
                })),
            name="eks-cluster-role",
            tags={
                "Name": "eks_role"
            }
        )

        eks_cluster_policy_attachment = IamRolePolicyAttachment(self, "e-AmazonEKSClusterPolicy",
                                policy_arn="arn:aws:iam::aws:policy/AmazonEKSClusterPolicy",
                                role=eks_role.name
)

        eksvpc_resource_controller_attachment = IamRolePolicyAttachment(self, "e-AmazonEKSVPCResourceController",
                                policy_arn="arn:aws:iam::aws:policy/AmazonEKSVPCResourceController",
                                role=eks_role.name
        )


        eks_cluster = EksCluster(self, "EksCluster",
                         name="MyEksCluster",  # Provide a name for your EKS cluster
                         role_arn=eks_role.arn,
                         vpc_config=EksClusterVpcConfig(
                            subnet_ids=[private_subnet.id, public_subnet.id]
                         )
)

#--------------------------------------Creating an Amazon ECR------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------# 
        
        amazon_ecr = EcrRepository(self, "AmazonEcr",
            image_scanning_configuration=EcrRepositoryImageScanningConfiguration(
                scan_on_push=True
            ),
            image_tag_mutability="MUTABLE",
            name = "platinum_ecr"
            
)
        
#--------------------------------------STORAGE---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
        
        my_key = KmsKey(self, "MyKey",
                        deletion_window_in_days=10,
                        description="key to encrypt bucket objects")
       
        my_bucket = S3Bucket(self, "MyBucket",
                     bucket="unique-hosting",
                     tags={
                         "Name": "Application Hosting"
                     })
        
        s3_bucket_encryption = S3BucketServerSideEncryptionConfigurationA(
                                                                        self,
                                                                        "MyBucketEncryption",
                                                                        bucket=my_bucket.id,
                                                                        rule=[
                                                                            S3BucketServerSideEncryptionConfigurationRuleA(
                                                                                apply_server_side_encryption_by_default=S3BucketServerSideEncryptionConfigurationRuleApplyServerSideEncryptionByDefaultA(
                                                                                    kms_master_key_id=my_key.arn,
                                                                                    sse_algorithm="aws:kms"
                                                                                )
                                                                            )
                                                                        ]
                                                                    )
        s3_access_point = S3AccessPoint(self, "S3AccessPoint",
                                        bucket=my_bucket.id,
                                        name="s3-access-point")

        S3BucketMetric(self, "s3-filtered",
                       bucket=my_bucket.id,
                       filter=S3BucketMetricFilter(
                           access_point=s3_access_point.arn,
                           tags={
                               "class": "red",
                               "priority": "high"
                           }
                       ),
                       name="ExtremelyImportantRedDocuments")
        
#--------------------------------------DATABASE--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
        rds_subnet_group = DbSubnetGroup(self, "RdsSubnetGroup",
                                         name = "rds-subnet-grp",
                                         subnet_ids = [public_subnet.id, db_subnet.id],
                                         tags={
                                             "Name": "RDS Subnet Group"
                                         }
                                        )
        
        aurora_cluster_parameter_group = RdsClusterParameterGroup(self, "AuroraClusterParameterGroup",
                                                                name="aurora-cluster-parameter-group",
                                                                family="aurora-mysql8.0",
                                                                description="Custom parameter group for MySQL 8.0",
                                                                # parameter=[
                                                                #     {
                                                                #         "name": "performance_insight_enabled",
                                                                #         "value": "1"
                                                                #     },

                                                                #     {
                                                                #         "name": "performance_insights_retention_period",
                                                                #         "value": "7"
                                                                #     }
                                                                # ]
                                                            )  

        aurora_cluster =  RdsCluster(self, "AuroraCluster",
                                    cluster_identifier      = "aurora-cluster",
                                    engine                  = "aurora-mysql",
                                    engine_version          = "8.0.mysql_aurora.3.02.0",
                                    availability_zones      = ["us-east-1a", "us-east-1c"],
                                    database_name           = "dbname",
                                    master_username         = username,
                                    master_password         = master_password,
                                    db_cluster_parameter_group_name = aurora_cluster_parameter_group.name,
                                    db_subnet_group_name = rds_subnet_group.name,
                                    skip_final_snapshot     = True,
                                    delete_automated_backups= True,
                                    deletion_protection     = False

                                                                    )
        
        aurora_instance = RdsClusterInstance(self, "AuroraInstance",
                                            identifier = "aurora-cluster-instance",
                                            cluster_identifier = aurora_cluster.cluster_identifier,
                                            instance_class     = "db.r5.large",
                                            engine             = "aurora-mysql",
                                            engine_version     = "8.0.mysql_aurora.3.02.0",
                                            performance_insights_enabled    = True,
                                            performance_insights_kms_key_id = my_key.arn,
                                            performance_insights_retention_period=7

                                            ) 

#---------------------------------------CloudWatch-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
        sns_topic = SnsTopic(self, "MySnsTopic",
                          display_name = " SNS Topic"
                          )
        
        # eks_cpu_alarm = CloudwatchMetricAlarm(self, "EKSCPUAlarm",
                            #         alarm_name="EKSCPUAlarm",
                            #         alarm_description="Alarm for EKS CPU utilization exceeding threshold",
                            #         namespace                         = "AWS/EC2",
                            #         metric_name                       =  "Eks_Cpu_Metric",
                            #         threshold                         = 80,
                            #         evaluation_periods                = 3,
                            #         period                            = 300, 
                            #         comparison_operator               = "GreaterThanOrEqualToThreshold",
                            #         alarm_actions                     = [eks_cluster.arn],
                            #         datapoints_to_alarm               = 1,
                            #         treat_missing_data                = "missing",
                            #         statistic                         = "Average"
                            # )
        

        
        
        

        rds_storage_alarm = CloudwatchMetricAlarm(self, "RdsStorageAlarm",
                                                  alarm_name          = "Rds-Storage-Alarm",
                                                  alarm_description   = "Alarm for RDS storage utilization exceeding threshold",
                                                  comparison_operator = "GreaterThanOrEqualToThreshold",
                                                  namespace           = "AWS/RDS",
                                                  metric_name         = "FreeStorageSpace",
                                                  evaluation_periods  = 3,
                                                  threshold           = 800,
                                                  period              = 3600,
                                                  statistic           = "Average",
                                                  alarm_actions       = [sns_topic.arn],
                                                  datapoints_to_alarm = 1,
                                                  treat_missing_data  = "missing",
                                                  depends_on=[aurora_cluster, aurora_instance]
                    
                                                  )
    



app = App()
MyStack(app, "cloud84", "mydb", "db.t3.micro", "k33ns!1984:pow3R", "admin", "ValidMasterPassword123")
app.synth()
