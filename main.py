#!/usr/bin/env python
from constructs import Construct
from cdktf import App, TerraformStack
from imports.aws.provider import AwsProvider
from imports.aws.route_table_association import RouteTableAssociation
from imports.aws.vpc import Vpc
from imports.aws.subnet import Subnet
from imports.aws.internet_gateway import InternetGateway
from imports.aws.route_table import RouteTable, RouteTableRoute
from imports.aws.security_group import SecurityGroup
from imports.aws.security_group_rule import SecurityGroupRule


class MyStack(TerraformStack):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

        AwsProvider(self, 'Aws', region="us-east-1")

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
                            cidr_block="0.0.0.0/0",  # Assuming this is your default route
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
                              route_table_id=private_subnet.id
                              )
        
        db_route_table = RouteTable(self, 'DbRouteTable',
                                    vpc_id=my_vpc.id,
                                    tags={"Name": "Database_Route_Table"}
                                    )
        
        RouteTableAssociation(self, 'DbRouteAssociation',
                              subnet_id=db_subnet.id,
                              route_table_id=db_route_table.id
                              )
        
        # Security Group

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

        

        



app = App()
MyStack(app, "cloud84")

app.synth()
