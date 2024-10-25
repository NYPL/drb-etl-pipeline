from aws_cdk import Stack
import aws_cdk as cdk
import aws_cdk.aws_applicationautoscaling as applicationautoscaling
import aws_cdk.aws_autoscaling as autoscaling
import aws_cdk.aws_cloudwatch as cloudwatch
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_ecs as ecs
import aws_cdk.aws_elasticloadbalancingv2 as elasticloadbalancingv2
import aws_cdk.aws_events as events
import aws_cdk.aws_iam as iam
import aws_cdk.aws_logs as logs
from constructs import Construct

"""
  This template creates an ECS cluster and deploys drupal as a service on that ECS cluster

"""
class DrbEtlPipelineStack(Stack):
  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    # Applying default props
    props = {
      'keyName': cdk.CfnParameter(self, 'keyName', 
        type = 'AWS::EC2::KeyPair::KeyName',
        default = str(kwargs.get('keyName', 'dgdvteam')),
        description = 'Name of an existing EC2 KeyPair to enable SSH access to the ECS instances.',
      ),
      'clusterName': kwargs.get('clusterName', 'sfr-pipeline-production'),
      'serviceName': kwargs.get('serviceName', 'sfr-pipeline-production'),
      'classifyTaskName': kwargs.get('classifyTaskName', 'sfr-classify-process-production'),
      'catalogTaskName': kwargs.get('catalogTaskName', 'sfr-catalog-process-production'),
      's3FilesTaskName': kwargs.get('s3FilesTaskName', 'sfr-s3-files-process-production'),
      'clusterTaskName': kwargs.get('clusterTaskName', 'sfr-cluster-process-production'),
      'coverTaskName': kwargs.get('coverTaskName', 'sfr-cover-process-production'),
      'hathiIngestTaskName': kwargs.get('hathiIngestTaskName', 'sfr-hathi-ingest-production'),
      'doabIngestTaskName': kwargs.get('doabIngestTaskName', 'sfr-doab-ingest-production'),
      'locIngestTaskName': kwargs.get('locIngestTaskName', 'sfr-loc-ingest-production'),
      'gutenbergIngestTaskName': kwargs.get('gutenbergIngestTaskName', 'sfr-gutenberg-ingest-production'),
      'nyplIngestTaskName': kwargs.get('nyplIngestTaskName', 'sfr-nypl-ingest-production'),
      'museIngestTaskName': kwargs.get('museIngestTaskName', 'sfr-muse-ingest-production'),
      'metIngestTaskName': kwargs.get('metIngestTaskName', 'sfr-met-ingest-production'),
      'databaseMaintenanceTaskName': kwargs.get('databaseMaintenanceTaskName', 'sfr-db-maintenance'),
      'ecrImage': kwargs.get('ecrImage', '946183545209.dkr.ecr.us-east-1.amazonaws.com/sfr_ingest_pipeline:production'),
      'loadBalancerCertificateArn': kwargs.get('loadBalancerCertificateArn', 'arn:aws:acm:us-east-1:946183545209:certificate/aee40806-85d9-4e4f-973d-4430105a0369'),
      'vpcId': cdk.CfnParameter(self, 'vpcId', 
        type = 'AWS::EC2::VPC::Id',
        default = str(kwargs.get('vpcId', 'vpc-4f76d329')),
        description = 'Select a VPC that allows instances to access the Internet.',
      ),
      'privateSubnets': cdk.CfnParameter(self, 'privateSubnets', 
        type = 'List<AWS::EC2::Subnet::Id>',
        default = str(kwargs.get('privateSubnets', 'subnet-03c66c36710360d09,subnet-d979eb82')),
        description = 'Select at two PRIVATE subnets in your selected VPC.',
      ),
      'publicSubnets': cdk.CfnParameter(self, 'publicSubnets', 
        type = 'List<AWS::EC2::Subnet::Id>',
        default = str(kwargs.get('publicSubnets', 'subnet-0a9668b917ead3ab7,subnet-f778eaac')),
        description = 'Select at two PUBLIC subnets in your selected VPC.',
      ),
      'taskCount': kwargs.get('taskCount', 2),
      'desiredCapacity': kwargs.get('desiredCapacity', 2),
      'maxSize': kwargs.get('maxSize', 4),
      'instanceType': kwargs.get('instanceType', 't3.large'),
      'alertSnsTopicArn': kwargs.get('alertSnsTopicArn', 'arn:aws:sns:us-east-1:491147561046:ecs-sfr-production'),
      'environment': kwargs.get('environment', 'production'),
      'elasticSearchScheme': kwargs.get('elasticSearchScheme', 'http'),
      'elasticSearchHost': kwargs.get('elasticSearchHost', '10.229.161.96, 10.229.163.144, 10.229.133.166'),
      'elasticSearchPort': kwargs.get('elasticSearchPort', '9200'),
      'elasticSearchIndex': kwargs.get('elasticSearchIndex', 'drb_dcdw_prod_new_cluster'),
      'elasticsearchUser': kwargs.get('elasticsearchUser', 'arn:aws:ssm:us-east-1:946183545209:parameter/drb/production/elasticsearch/user'),
      'elasticsearchPassword': kwargs.get('elasticsearchPassword', 'arn:aws:ssm:us-east-1:946183545209:parameter/drb/production/elasticsearch/pswd'),
      'postgreSqlUser': kwargs.get('postgreSqlUser', 'arn:aws:ssm:us-east-1:946183545209:parameter/drb/production/postgres/user'),
      'postgreSqlPassword': kwargs.get('postgreSqlPassword', 'arn:aws:ssm:us-east-1:946183545209:parameter/drb/production/postgres/pswd'),
      'nyplPostgreSqlUser': kwargs.get('nyplPostgreSqlUser', 'arn:aws:ssm:us-east-1:946183545209:parameter/drb/production/postgres/nypl-user'),
      'nyplPostgreSqlPassword': kwargs.get('nyplPostgreSqlPassword', 'arn:aws:ssm:us-east-1:946183545209:parameter/drb/production/postgres/nypl-pswd'),
      'oclcKey': kwargs.get('oclcKey', 'arn:aws:ssm:us-east-1:946183545209:parameter/drb/production/oclc-key'),
      'oclcClassifyKey': kwargs.get('oclcClassifyKey', 'arn:aws:ssm:us-east-1:946183545209:parameter/drb/production/oclc-classify-key'),
      'nyplApiClientId': kwargs.get('nyplApiClientId', 'arn:aws:ssm:us-east-1:946183545209:parameter/drb/production/nypl-api/client-id'),
      'nyplApiClientSecret': kwargs.get('nyplApiClientSecret', 'arn:aws:ssm:us-east-1:946183545209:parameter/drb/production/nypl-api/client-secret'),
      'nyplApiPublicKey': kwargs.get('nyplApiPublicKey', 'arn:aws:ssm:us-east-1:946183545209:parameter/drb/production/nypl-api/public-key'),
      'rabbitMqUser': kwargs.get('rabbitMqUser', 'arn:aws:ssm:us-east-1:946183545209:parameter/drb/production/rabbit-user'),
      'rabbitMqPassword': kwargs.get('rabbitMqPassword', 'arn:aws:ssm:us-east-1:946183545209:parameter/drb/production/rabbit-pswd'),
      's3awsAccessKey': kwargs.get('s3awsAccessKey', 'arn:aws:ssm:us-east-1:946183545209:parameter/drb/production/aws/access-key'),
      's3awsSecretKey': kwargs.get('s3awsSecretKey', 'arn:aws:ssm:us-east-1:946183545209:parameter/drb/production/aws/secret-key'),
      'githubApiKey': kwargs.get('githubApiKey', 'arn:aws:ssm:us-east-1:946183545209:parameter/drb/production/github-key'),
      'contentCafeUser': kwargs.get('contentCafeUser', 'arn:aws:ssm:us-east-1:946183545209:parameter/drb/production/contentcafe/user'),
      'contentCafePassword': kwargs.get('contentCafePassword', 'arn:aws:ssm:us-east-1:946183545209:parameter/drb/production/contentcafe/pswd'),
      'googleBooksApiKey': kwargs.get('googleBooksApiKey', 'arn:aws:ssm:us-east-1:946183545209:parameter/drb/production/google-books/api-key'),
      'hathiTrustApiAccessKey': kwargs.get('hathiTrustApiAccessKey', 'arn:aws:ssm:us-east-1:946183545209:parameter/drb/production/hathitrust/api-key'),
      'hathiTrustApiSecretKey': kwargs.get('hathiTrustApiSecretKey', 'arn:aws:ssm:us-east-1:946183545209:parameter/drb/production/hathitrust/api-secret'),
      'newRelicLicenseKey': kwargs.get('newRelicLicenseKey', 'arn:aws:ssm:us-east-1:946183545209:parameter/drb/qa/newrelic/key'),
      'ecsAmiParameterKey': cdk.CfnParameter(self, 'ecsAmiParameterKey', 
        type = 'AWS::SSM::Parameter::Value<String>',
        default = str(kwargs.get('ecsAmiParameterKey', '/ami/ecs/latest')),
        description = 'SSM Parameter Store String containing the Latest ECS Baked image',
      ),
    }

    # Resources
    autoscalingRole = iam.CfnRole(self, 'AutoscalingRole',
          assume_role_policy_document = {
            'Statement': [
              {
                'Effect': 'Allow',
                'Principal': {
                  'Service': [
                    'application-autoscaling.amazonaws.com',
                  ],
                },
                'Action': [
                  'sts:AssumeRole',
                ],
              },
            ],
          },
          path = '/',
          policies = [
            {
              'policyName': 'service-autoscaling',
              'policyDocument': {
                'Statement': [
                  {
                    'Effect': 'Allow',
                    'Action': [
                      'application-autoscaling:*',
                      'cloudwatch:DescribeAlarms',
                      'cloudwatch:PutMetricAlarm',
                      'ecs:DescribeServices',
                      'ecs:UpdateService',
                    ],
                    'Resource': '*',
                  },
                ],
              },
            },
          ],
        )

    cloudwatchLogsGroup = logs.CfnLogGroup(self, 'CloudwatchLogsGroup',
          log_group_name = '-'.join([
            'ECSLogGroup',
            self.stack_name,
          ]),
          retention_in_days = 14,
        )

    ec2InstanceProfileRole = iam.CfnRole(self, 'EC2InstanceProfileRole',
          assume_role_policy_document = {
            'Statement': [
              {
                'Effect': 'Allow',
                'Principal': {
                  'Service': [
                    'ec2.amazonaws.com',
                  ],
                },
                'Action': [
                  'sts:AssumeRole',
                ],
              },
            ],
          },
          path = '/',
          policies = [
            {
              'policyName': 'ecs-service',
              'policyDocument': {
                'Statement': [
                  {
                    'Effect': 'Allow',
                    'Action': [
                      'ecs:CreateCluster',
                      'ecs:DeregisterContainerInstance',
                      'ecs:DiscoverPollEndpoint',
                      'ecs:Poll',
                      'ecs:RegisterContainerInstance',
                      'ecs:StartTelemetrySession',
                      'ecs:Submit*',
                      'logs:CreateLogStream',
                      'logs:PutLogEvents',
                      'ecr:BatchCheckLayerAvailability',
                      'ecr:BatchGetImage',
                      'ecr:GetDownloadUrlForLayer',
                      'ecr:GetAuthorizationToken',
                      'ssm:GetParameter',
                      'ec2:DescribeInstances',
                      's3:GetObject',
                    ],
                    'Resource': '*',
                  },
                ],
              },
            },
          ],
        )

    ecsCluster = ecs.CfnCluster(self, 'ECSCluster',
          cluster_name = props['clusterName'],
        )

    ecsEventTaskRole = iam.CfnRole(self, 'ECSEventTaskRole',
          assume_role_policy_document = {
            'Statement': [
              {
                'Effect': 'Allow',
                'Principal': {
                  'Service': [
                    'events.amazonaws.com',
                  ],
                },
                'Action': [
                  'sts:AssumeRole',
                ],
              },
            ],
          },
          path = '/',
          policies = [
            {
              'policyName': '-'.join([
                self.stack_name,
                'ecstask-policy',
              ]),
              'policyDocument': {
                'Statement': [
                  {
                    'Effect': 'Allow',
                    'Action': [
                      'ecs:RunTask',
                    ],
                    'Resource': [
                      '*',
                    ],
                  },
                  {
                    'Effect': 'Allow',
                    'Action': 'iam:PassRole',
                    'Resource': [
                      '*',
                    ],
                    'Condition': {
                      'StringLike': {
                        'iam:PassedToService': 'ecs-tasks.amazonaws.com',
                      },
                    },
                  },
                ],
              },
            },
          ],
        )

    ecsSecurityGroup = ec2.CfnSecurityGroup(self, 'ECSSecurityGroup',
          group_description = 'ECS Security Group',
          vpc_id = props['vpcId'],
        )

    ecsServiceRole = iam.CfnRole(self, 'ECSServiceRole',
          assume_role_policy_document = {
            'Statement': [
              {
                'Effect': 'Allow',
                'Principal': {
                  'Service': [
                    'ecs.amazonaws.com',
                  ],
                },
                'Action': [
                  'sts:AssumeRole',
                ],
              },
            ],
          },
          path = '/',
          policies = [
            {
              'policyName': '-'.join([
                self.stack_name,
                'ecs-policy',
              ]),
              'policyDocument': {
                'Statement': [
                  {
                    'Effect': 'Allow',
                    'Action': [
                      'elasticloadbalancing:DeregisterInstancesFromLoadBalancer',
                      'elasticloadbalancing:DeregisterTargets',
                      'elasticloadbalancing:Describe*',
                      'elasticloadbalancing:RegisterInstancesWithLoadBalancer',
                      'elasticloadbalancing:RegisterTargets',
                      'ec2:Describe*',
                      'ec2:AuthorizeSecurityGroupIngress',
                      'ecr:BatchCheckLayerAvailability',
                      'ecr:BatchGetImage',
                      'ecr:GetDownloadUrlForLayer',
                      'ecr:GetAuthorizationToken',
                      'logs:CreateLogGroup',
                      'logs:CreateLogStream',
                      'logs:PutLogStream',
                      'logs:PutLogEvents',
                      'logs:DescribeLogStreams',
                    ],
                    'Resource': '*',
                  },
                ],
              },
            },
          ],
        )

    ecsTaskRole = iam.CfnRole(self, 'ECSTaskRole',
          assume_role_policy_document = {
            'Statement': [
              {
                'Effect': 'Allow',
                'Principal': {
                  'Service': [
                    'ecs-tasks.amazonaws.com',
                  ],
                },
                'Action': [
                  'sts:AssumeRole',
                ],
              },
            ],
          },
          path = '/',
          policies = [
            {
              'policyName': '-'.join([
                self.stack_name,
                'ecstask-policy',
              ]),
              'policyDocument': {
                'Statement': [
                  {
                    'Effect': 'Allow',
                    'Action': [
                      'ssm:GetParameters',
                      'kms:Decrypt',
                    ],
                    'Resource': [
                      props['postgreSqlUser'],
                      props['postgreSqlPassword'],
                      props['oclcKey'],
                      props['oclcClassifyKey'],
                      props['nyplApiClientId'],
                      props['nyplApiClientSecret'],
                      props['nyplPostgreSqlUser'],
                      props['nyplPostgreSqlPassword'],
                      props['rabbitMqUser'],
                      props['rabbitMqPassword'],
                      props['s3awsAccessKey'],
                      props['s3awsSecretKey'],
                      props['githubApiKey'],
                      props['contentCafeUser'],
                      props['contentCafePassword'],
                      props['googleBooksApiKey'],
                      props['hathiTrustApiAccessKey'],
                      props['hathiTrustApiSecretKey'],
                      props['nyplApiPublicKey'],
                      props['elasticsearchUser'],
                      props['elasticsearchPassword'],
                      props['newRelicLicenseKey'],
                    ],
                  },
                  {
                    'Effect': 'Allow',
                    'Action': [
                      'ecr:BatchCheckLayerAvailability',
                      'ecr:BatchGetImage',
                      'ecr:GetDownloadUrlForLayer',
                      'ecr:GetAuthorizationToken',
                      'logs:CreateLogGroup',
                      'logs:CreateLogStream',
                      'logs:PutLogStream',
                      'logs:PutLogEvents',
                      'logs:DescribeLogStreams',
                      'iam:PassRole',
                    ],
                    'Resource': '*',
                  },
                ],
              },
            },
          ],
        )

    ec2InstanceProfile = iam.CfnInstanceProfile(self, 'EC2InstanceProfile',
          path = '/',
          roles = [
            ec2InstanceProfileRole.ref,
          ],
        )

    ecsalb = elasticloadbalancingv2.CfnLoadBalancer(self, 'ECSALB',
          scheme = 'internet-facing',
          load_balancer_attributes = [
            {
              'key': 'idle_timeout.timeout_seconds',
              'value': '30',
            },
          ],
          subnets = [
            cdk.Fn.select(0, props['publicSubnets']),
            cdk.Fn.select(1, props['publicSubnets']),
          ],
          security_groups = [
            ecsSecurityGroup.ref,
          ],
        )

    ecsSecurityGroupAlBports = ec2.CfnSecurityGroupIngress(self, 'ECSSecurityGroupALBports',
          group_id = ecsSecurityGroup.ref,
          ip_protocol = 'tcp',
          from_port = 31000,
          to_port = 61000,
          source_security_group_id = ecsSecurityGroup.ref,
        )

    ecsSecurityGroupHttpSinbound = ec2.CfnSecurityGroupIngress(self, 'ECSSecurityGroupHTTPSinbound',
          group_id = ecsSecurityGroup.ref,
          ip_protocol = 'tcp',
          from_port = 443,
          to_port = 443,
          cidr_ip = '0.0.0.0/0',
        )

    ecsSecurityGroupHttPinbound = ec2.CfnSecurityGroupIngress(self, 'ECSSecurityGroupHTTPinbound',
          group_id = ecsSecurityGroup.ref,
          ip_protocol = 'tcp',
          from_port = 80,
          to_port = 80,
          cidr_ip = '0.0.0.0/0',
        )

    ecsSecurityGroupSsHinbound = ec2.CfnSecurityGroupIngress(self, 'ECSSecurityGroupSSHinbound',
          group_id = ecsSecurityGroup.ref,
          ip_protocol = 'tcp',
          from_port = 22,
          to_port = 22,
          cidr_ip = '0.0.0.0/0',
        )

    ecsTaskDefinition = ecs.CfnTaskDefinition(self, 'ECSTaskDefinition',
          family = props['serviceName'],
          execution_role_arn = ecsTaskRole.ref,
          container_definitions = [
            {
              'name': props['serviceName'],
              'essential': True,
              'image': props['ecrImage'],
              'memory': 1024,
              'command': [
                '--process',
                'APIProcess',
                '--environment',
                'production',
              ],
              'environment': [
                {
                  'name': 'ENVIRONMENT',
                  'value': props['environment'],
                },
                {
                  'name': 'ELASTICSEARCH_SCHEME',
                  'value': props['elasticSearchScheme'],
                },
                {
                  'name': 'ELASTICSEARCH_HOST',
                  'value': props['elasticSearchHost'],
                },
                {
                  'name': 'ELASTICSEARCH_INDEX',
                  'value': props['elasticSearchIndex'],
                },
                {
                  'name': 'ELASTICSEARCH_PORT',
                  'value': props['elasticSearchPort'],
                },
                {
                  'name': 'REDIS_HOST',
                  'value': cdk.Fn.import_value('-'.join([
                    'oRedisHost',
                    props['pMasterStackName'],
                  ])),
                },
              ],
              'secrets': [
                {
                  'name': 'POSTGRES_USER',
                  'valueFrom': props['postgreSqlUser'],
                },
                {
                  'name': 'POSTGRES_PSWD',
                  'valueFrom': props['postgreSqlPassword'],
                },
                {
                  'name': 'ELASTICSEARCH_USER',
                  'valueFrom': props['elasticsearchUser'],
                },
                {
                  'name': 'ELASTICSEARCH_PSWD',
                  'valueFrom': props['elasticsearchPassword'],
                },
                {
                  'name': 'NYPL_API_CLIENT_PUBLIC_KEY',
                  'valueFrom': props['nyplApiPublicKey'],
                },
                {
                  'name': 'NEW_RELIC_LICENSE_KEY',
                  'valueFrom': props['newRelicLicenseKey'],
                },
              ],
              'logConfiguration': {
                'logDriver': 'awslogs',
                'options': {
                  'awslogs-group': cloudwatchLogsGroup.ref,
                  'awslogs-region': self.region,
                  'awslogs-stream-prefix': props['serviceName'],
                },
              },
              'portMappings': [
                {
                  'containerPort': 80,
                  'hostPort': 0,
                },
              ],
            },
          ],
        )

    ecsTaskDefinitionCatalogScheduled = ecs.CfnTaskDefinition(self, 'ECSTaskDefinitionCatalogScheduled',
          family = props['catalogTaskName'],
          execution_role_arn = ecsTaskRole.ref,
          container_definitions = [
            {
              'name': props['catalogTaskName'],
              'essential': True,
              'image': props['ecrImage'],
              'memory': 512,
              'command': [
                '--process',
                'CatalogProcess',
                '--environment',
                'production',
              ],
              'environment': [
                {
                  'name': 'ENVIRONMENT',
                  'value': props['environment'],
                },
                {
                  'name': 'ELASTICSEARCH_HOST',
                  'value': props['elasticSearchHost'],
                },
                {
                  'name': 'ELASTICSEARCH_INDEX',
                  'value': props['elasticSearchIndex'],
                },
              ],
              'secrets': [
                {
                  'name': 'POSTGRES_USER',
                  'valueFrom': props['postgreSqlUser'],
                },
                {
                  'name': 'POSTGRES_PSWD',
                  'valueFrom': props['postgreSqlPassword'],
                },
                {
                  'name': 'RABBIT_USER',
                  'valueFrom': props['rabbitMqUser'],
                },
                {
                  'name': 'RABBIT_PSWD',
                  'valueFrom': props['rabbitMqPassword'],
                },
                {
                  'name': 'OCLC_API_KEY',
                  'valueFrom': props['oclcKey'],
                },
                {
                  'name': 'NEW_RELIC_LICENSE_KEY',
                  'valueFrom': props['newRelicLicenseKey'],
                },
              ],
              'logConfiguration': {
                'logDriver': 'awslogs',
                'options': {
                  'awslogs-group': cloudwatchLogsGroup.ref,
                  'awslogs-region': self.region,
                  'awslogs-stream-prefix': props['catalogTaskName'],
                },
              },
            },
          ],
        )

    ecsTaskDefinitionClassifyBacklogScheduled = ecs.CfnTaskDefinition(self, 'ECSTaskDefinitionClassifyBacklogScheduled',
          family = props['classifyTaskName'],
          execution_role_arn = ecsTaskRole.ref,
          container_definitions = [
            {
              'name': props['classifyTaskName'],
              'essential': True,
              'image': props['ecrImage'],
              'memory': 256,
              'command': [
                '--process',
                'ClassifyProcess',
                '--environment',
                'production',
                '--ingestType',
                'complete',
                '--limit',
                10000,
              ],
              'environment': [
                {
                  'name': 'ENVIRONMENT',
                  'value': props['environment'],
                },
                {
                  'name': 'ELASTICSEARCH_HOST',
                  'value': props['elasticSearchHost'],
                },
                {
                  'name': 'ELASTICSEARCH_INDEX',
                  'value': props['elasticSearchIndex'],
                },
                {
                  'name': 'REDIS_HOST',
                  'value': cdk.Fn.import_value('-'.join([
                    'oRedisHost',
                    props['pMasterStackName'],
                  ])),
                },
              ],
              'secrets': [
                {
                  'name': 'POSTGRES_USER',
                  'valueFrom': props['postgreSqlUser'],
                },
                {
                  'name': 'POSTGRES_PSWD',
                  'valueFrom': props['postgreSqlPassword'],
                },
                {
                  'name': 'RABBIT_USER',
                  'valueFrom': props['rabbitMqUser'],
                },
                {
                  'name': 'RABBIT_PSWD',
                  'valueFrom': props['rabbitMqPassword'],
                },
                {
                  'name': 'NEW_RELIC_LICENSE_KEY',
                  'valueFrom': props['newRelicLicenseKey'],
                },
                {
                  'name': 'OCLC_CLASSIFY_API_KEY',
                  'valueFrom': props['oclcClassifyKey'],
                },
              ],
              'logConfiguration': {
                'logDriver': 'awslogs',
                'options': {
                  'awslogs-group': cloudwatchLogsGroup.ref,
                  'awslogs-region': self.region,
                  'awslogs-stream-prefix': props['classifyTaskName'],
                },
              },
            },
          ],
        )

    ecsTaskDefinitionClassifyDailyScheduled = ecs.CfnTaskDefinition(self, 'ECSTaskDefinitionClassifyDailyScheduled',
          family = props['classifyTaskName'],
          execution_role_arn = ecsTaskRole.ref,
          container_definitions = [
            {
              'name': props['classifyTaskName'],
              'essential': True,
              'image': props['ecrImage'],
              'memory': 256,
              'command': [
                '--process',
                'ClassifyProcess',
                '--environment',
                'production',
                '--ingestType',
                'daily',
              ],
              'environment': [
                {
                  'name': 'ENVIRONMENT',
                  'value': props['environment'],
                },
                {
                  'name': 'ELASTICSEARCH_HOST',
                  'value': props['elasticSearchHost'],
                },
                {
                  'name': 'ELASTICSEARCH_INDEX',
                  'value': props['elasticSearchIndex'],
                },
                {
                  'name': 'REDIS_HOST',
                  'value': cdk.Fn.import_value('-'.join([
                    'oRedisHost',
                    props['pMasterStackName'],
                  ])),
                },
              ],
              'secrets': [
                {
                  'name': 'POSTGRES_USER',
                  'valueFrom': props['postgreSqlUser'],
                },
                {
                  'name': 'POSTGRES_PSWD',
                  'valueFrom': props['postgreSqlPassword'],
                },
                {
                  'name': 'RABBIT_USER',
                  'valueFrom': props['rabbitMqUser'],
                },
                {
                  'name': 'RABBIT_PSWD',
                  'valueFrom': props['rabbitMqPassword'],
                },
                {
                  'name': 'NEW_RELIC_LICENSE_KEY',
                  'valueFrom': props['newRelicLicenseKey'],
                },
                {
                  'name': 'OCLC_CLASSIFY_API_KEY',
                  'valueFrom': props['oclcClassifyKey'],
                },
              ],
              'logConfiguration': {
                'logDriver': 'awslogs',
                'options': {
                  'awslogs-group': cloudwatchLogsGroup.ref,
                  'awslogs-region': self.region,
                  'awslogs-stream-prefix': props['classifyTaskName'],
                },
              },
            },
          ],
        )

    ecsTaskDefinitionClusterScheduled = ecs.CfnTaskDefinition(self, 'ECSTaskDefinitionClusterScheduled',
          family = props['clusterTaskName'],
          execution_role_arn = ecsTaskRole.ref,
          container_definitions = [
            {
              'name': props['clusterTaskName'],
              'essential': True,
              'image': props['ecrImage'],
              'memory': 2048,
              'command': [
                '--process',
                'ClusterProcess',
                '--environment',
                'production',
                '--ingestType',
                'daily',
              ],
              'environment': [
                {
                  'name': 'ENVIRONMENT',
                  'value': props['environment'],
                },
                {
                  'name': 'ELASTICSEARCH_SCHEME',
                  'value': props['elasticSearchScheme'],
                },
                {
                  'name': 'ELASTICSEARCH_HOST',
                  'value': props['elasticSearchHost'],
                },
                {
                  'name': 'ELASTICSEARCH_INDEX',
                  'value': props['elasticSearchIndex'],
                },
                {
                  'name': 'ELASTICSEARCH_PORT',
                  'value': props['elasticSearchPort'],
                },
                {
                  'name': 'REDIS_HOST',
                  'value': cdk.Fn.import_value('-'.join([
                    'oRedisHost',
                    props['pMasterStackName'],
                  ])),
                },
              ],
              'secrets': [
                {
                  'name': 'POSTGRES_USER',
                  'valueFrom': props['postgreSqlUser'],
                },
                {
                  'name': 'POSTGRES_PSWD',
                  'valueFrom': props['postgreSqlPassword'],
                },
                {
                  'name': 'ELASTICSEARCH_USER',
                  'valueFrom': props['elasticsearchUser'],
                },
                {
                  'name': 'ELASTICSEARCH_PSWD',
                  'valueFrom': props['elasticsearchPassword'],
                },
                {
                  'name': 'NEW_RELIC_LICENSE_KEY',
                  'valueFrom': props['newRelicLicenseKey'],
                },
              ],
              'logConfiguration': {
                'logDriver': 'awslogs',
                'options': {
                  'awslogs-group': cloudwatchLogsGroup.ref,
                  'awslogs-region': self.region,
                  'awslogs-stream-prefix': props['clusterTaskName'],
                },
              },
            },
          ],
        )

    ecsTaskDefinitionCoverScheduled = ecs.CfnTaskDefinition(self, 'ECSTaskDefinitionCoverScheduled',
          family = props['coverTaskName'],
          execution_role_arn = ecsTaskRole.ref,
          container_definitions = [
            {
              'name': props['coverTaskName'],
              'essential': True,
              'image': props['ecrImage'],
              'memory': 256,
              'command': [
                '--process',
                'CoverProcess',
                '--environment',
                'production',
                '--ingestType',
                'complete',
              ],
              'environment': [
                {
                  'name': 'ENVIRONMENT',
                  'value': props['environment'],
                },
                {
                  'name': 'ELASTICSEARCH_HOST',
                  'value': props['elasticSearchHost'],
                },
                {
                  'name': 'ELASTICSEARCH_INDEX',
                  'value': props['elasticSearchIndex'],
                },
                {
                  'name': 'REDIS_HOST',
                  'value': cdk.Fn.import_value('-'.join([
                    'oRedisHost',
                    props['pMasterStackName'],
                  ])),
                },
              ],
              'secrets': [
                {
                  'name': 'POSTGRES_USER',
                  'valueFrom': props['postgreSqlUser'],
                },
                {
                  'name': 'POSTGRES_PSWD',
                  'valueFrom': props['postgreSqlPassword'],
                },
                {
                  'name': 'AWS_ACCESS',
                  'valueFrom': props['s3awsAccessKey'],
                },
                {
                  'name': 'AWS_SECRET',
                  'valueFrom': props['s3awsSecretKey'],
                },
                {
                  'name': 'CONTENT_CAFE_USER',
                  'valueFrom': props['contentCafeUser'],
                },
                {
                  'name': 'CONTENT_CAFE_PSWD',
                  'valueFrom': props['contentCafePassword'],
                },
                {
                  'name': 'HATHI_API_KEY',
                  'valueFrom': props['hathiTrustApiAccessKey'],
                },
                {
                  'name': 'HATHI_API_SECRET',
                  'valueFrom': props['hathiTrustApiSecretKey'],
                },
                {
                  'name': 'GOOGLE_BOOKS_KEY',
                  'valueFrom': props['googleBooksApiKey'],
                },
                {
                  'name': 'NEW_RELIC_LICENSE_KEY',
                  'valueFrom': props['newRelicLicenseKey'],
                },
              ],
              'logConfiguration': {
                'logDriver': 'awslogs',
                'options': {
                  'awslogs-group': cloudwatchLogsGroup.ref,
                  'awslogs-region': self.region,
                  'awslogs-stream-prefix': props['coverTaskName'],
                },
              },
            },
          ],
        )

    ecsTaskDefinitionDoabIngestScheduled = ecs.CfnTaskDefinition(self, 'ECSTaskDefinitionDOABIngestScheduled',
          family = props['doabIngestTaskName'],
          execution_role_arn = ecsTaskRole.ref,
          container_definitions = [
            {
              'name': props['doabIngestTaskName'],
              'essential': True,
              'image': props['ecrImage'],
              'memory': 256,
              'command': [
                '--process',
                'DOABProcess',
                '--environment',
                'production',
                '--ingestType',
                'daily',
              ],
              'environment': [
                {
                  'name': 'ENVIRONMENT',
                  'value': props['environment'],
                },
                {
                  'name': 'ELASTICSEARCH_HOST',
                  'value': props['elasticSearchHost'],
                },
                {
                  'name': 'ELASTICSEARCH_INDEX',
                  'value': props['elasticSearchIndex'],
                },
              ],
              'secrets': [
                {
                  'name': 'POSTGRES_USER',
                  'valueFrom': props['postgreSqlUser'],
                },
                {
                  'name': 'POSTGRES_PSWD',
                  'valueFrom': props['postgreSqlPassword'],
                },
                {
                  'name': 'AWS_ACCESS',
                  'valueFrom': props['s3awsAccessKey'],
                },
                {
                  'name': 'AWS_SECRET',
                  'valueFrom': props['s3awsSecretKey'],
                },
                {
                  'name': 'RABBIT_USER',
                  'valueFrom': props['rabbitMqUser'],
                },
                {
                  'name': 'RABBIT_PSWD',
                  'valueFrom': props['rabbitMqPassword'],
                },
                {
                  'name': 'NEW_RELIC_LICENSE_KEY',
                  'valueFrom': props['newRelicLicenseKey'],
                },
              ],
              'logConfiguration': {
                'logDriver': 'awslogs',
                'options': {
                  'awslogs-group': cloudwatchLogsGroup.ref,
                  'awslogs-region': self.region,
                  'awslogs-stream-prefix': props['doabIngestTaskName'],
                },
              },
            },
          ],
        )

    ecsTaskDefinitionDatabaseMaintenanceScheduled = ecs.CfnTaskDefinition(self, 'ECSTaskDefinitionDatabaseMaintenanceScheduled',
          family = props['databaseMaintenanceTaskName'],
          execution_role_arn = ecsTaskRole.ref,
          container_definitions = [
            {
              'name': props['databaseMaintenanceTaskName'],
              'essential': True,
              'image': props['ecrImage'],
              'memory': 512,
              'command': [
                '--process',
                'DatabaseMaintenanceProcess',
                '--environment',
                'production',
              ],
              'environment': [
                {
                  'name': 'ENVIRONMENT',
                  'value': props['environment'],
                },
                {
                  'name': 'ELASTICSEARCH_SCHEME',
                  'value': props['elasticSearchScheme'],
                },
                {
                  'name': 'ELASTICSEARCH_HOST',
                  'value': props['elasticSearchHost'],
                },
                {
                  'name': 'ELASTICSEARCH_INDEX',
                  'value': props['elasticSearchIndex'],
                },
                {
                  'name': 'ELASTICSEARCH_PORT',
                  'value': props['elasticSearchPort'],
                },
              ],
              'secrets': [
                {
                  'name': 'POSTGRES_USER',
                  'valueFrom': props['postgreSqlUser'],
                },
                {
                  'name': 'POSTGRES_PSWD',
                  'valueFrom': props['postgreSqlPassword'],
                },
                {
                  'name': 'ELASTICSEARCH_USER',
                  'valueFrom': props['elasticsearchUser'],
                },
                {
                  'name': 'ELASTICSEARCH_PSWD',
                  'valueFrom': props['elasticsearchPassword'],
                },
              ],
              'logConfiguration': {
                'logDriver': 'awslogs',
                'options': {
                  'awslogs-group': cloudwatchLogsGroup.ref,
                  'awslogs-region': self.region,
                  'awslogs-stream-prefix': props['databaseMaintenanceTaskName'],
                },
              },
            },
          ],
        )

    ecsTaskDefinitionGutenbergIngestScheduled = ecs.CfnTaskDefinition(self, 'ECSTaskDefinitionGutenbergIngestScheduled',
          family = props['gutenbergIngestTaskName'],
          execution_role_arn = ecsTaskRole.ref,
          container_definitions = [
            {
              'name': props['gutenbergIngestTaskName'],
              'essential': True,
              'image': props['ecrImage'],
              'memory': 256,
              'command': [
                '--process',
                'GutenbergProcess',
                '--environment',
                'production',
                '--ingestType',
                'daily',
              ],
              'environment': [
                {
                  'name': 'ENVIRONMENT',
                  'value': props['environment'],
                },
                {
                  'name': 'ELASTICSEARCH_HOST',
                  'value': props['elasticSearchHost'],
                },
                {
                  'name': 'ELASTICSEARCH_INDEX',
                  'value': props['elasticSearchIndex'],
                },
              ],
              'secrets': [
                {
                  'name': 'POSTGRES_USER',
                  'valueFrom': props['postgreSqlUser'],
                },
                {
                  'name': 'POSTGRES_PSWD',
                  'valueFrom': props['postgreSqlPassword'],
                },
                {
                  'name': 'RABBIT_USER',
                  'valueFrom': props['rabbitMqUser'],
                },
                {
                  'name': 'RABBIT_PSWD',
                  'valueFrom': props['rabbitMqPassword'],
                },
                {
                  'name': 'AWS_ACCESS',
                  'valueFrom': props['s3awsAccessKey'],
                },
                {
                  'name': 'AWS_SECRET',
                  'valueFrom': props['s3awsSecretKey'],
                },
                {
                  'name': 'GITHUB_API_KEY',
                  'valueFrom': props['githubApiKey'],
                },
                {
                  'name': 'NEW_RELIC_LICENSE_KEY',
                  'valueFrom': props['newRelicLicenseKey'],
                },
              ],
              'logConfiguration': {
                'logDriver': 'awslogs',
                'options': {
                  'awslogs-group': cloudwatchLogsGroup.ref,
                  'awslogs-region': self.region,
                  'awslogs-stream-prefix': props['gutenbergIngestTaskName'],
                },
              },
            },
          ],
        )

    ecsTaskDefinitionHathiIngestScheduled = ecs.CfnTaskDefinition(self, 'ECSTaskDefinitionHathiIngestScheduled',
          family = props['hathiIngestTaskName'],
          execution_role_arn = ecsTaskRole.ref,
          container_definitions = [
            {
              'name': props['hathiIngestTaskName'],
              'essential': True,
              'image': props['ecrImage'],
              'memory': 256,
              'command': [
                '--process',
                'HathiTrustProcess',
                '--environment',
                'production',
                '--ingestType',
                'daily',
              ],
              'environment': [
                {
                  'name': 'ENVIRONMENT',
                  'value': props['environment'],
                },
                {
                  'name': 'ELASTICSEARCH_HOST',
                  'value': props['elasticSearchHost'],
                },
                {
                  'name': 'ELASTICSEARCH_INDEX',
                  'value': props['elasticSearchIndex'],
                },
              ],
              'secrets': [
                {
                  'name': 'POSTGRES_USER',
                  'valueFrom': props['postgreSqlUser'],
                },
                {
                  'name': 'POSTGRES_PSWD',
                  'valueFrom': props['postgreSqlPassword'],
                },
                {
                  'name': 'NEW_RELIC_LICENSE_KEY',
                  'valueFrom': props['newRelicLicenseKey'],
                },
              ],
              'logConfiguration': {
                'logDriver': 'awslogs',
                'options': {
                  'awslogs-group': cloudwatchLogsGroup.ref,
                  'awslogs-region': self.region,
                  'awslogs-stream-prefix': props['hathiIngestTaskName'],
                },
              },
            },
          ],
        )

    ecsTaskDefinitionLocIngestScheduled = ecs.CfnTaskDefinition(self, 'ECSTaskDefinitionLOCIngestScheduled',
          family = props['locIngestTaskName'],
          execution_role_arn = ecsTaskRole.ref,
          container_definitions = [
            {
              'name': props['locIngestTaskName'],
              'essential': True,
              'image': props['ecrImage'],
              'memory': 256,
              'command': [
                '--process',
                'LOCProcess',
                '--environment',
                'production',
                '--ingestType',
                'weekly',
              ],
              'environment': [
                {
                  'name': 'ENVIRONMENT',
                  'value': props['environment'],
                },
                {
                  'name': 'ELASTICSEARCH_HOST',
                  'value': props['elasticSearchHost'],
                },
                {
                  'name': 'ELASTICSEARCH_INDEX',
                  'value': props['elasticSearchIndex'],
                },
              ],
              'secrets': [
                {
                  'name': 'POSTGRES_USER',
                  'valueFrom': props['postgreSqlUser'],
                },
                {
                  'name': 'POSTGRES_PSWD',
                  'valueFrom': props['postgreSqlPassword'],
                },
                {
                  'name': 'RABBIT_USER',
                  'valueFrom': props['rabbitMqUser'],
                },
                {
                  'name': 'RABBIT_PSWD',
                  'valueFrom': props['rabbitMqPassword'],
                },
                {
                  'name': 'AWS_ACCESS',
                  'valueFrom': props['s3awsAccessKey'],
                },
                {
                  'name': 'AWS_SECRET',
                  'valueFrom': props['s3awsSecretKey'],
                },
                {
                  'name': 'NEW_RELIC_LICENSE_KEY',
                  'valueFrom': props['newRelicLicenseKey'],
                },
              ],
              'logConfiguration': {
                'logDriver': 'awslogs',
                'options': {
                  'awslogs-group': cloudwatchLogsGroup.ref,
                  'awslogs-region': self.region,
                  'awslogs-stream-prefix': props['locIngestTaskName'],
                },
              },
            },
          ],
        )

    ecsTaskDefinitionMetIngestScheduled = ecs.CfnTaskDefinition(self, 'ECSTaskDefinitionMETIngestScheduled',
          family = props['metIngestTaskName'],
          execution_role_arn = ecsTaskRole.ref,
          container_definitions = [
            {
              'name': props['metIngestTaskName'],
              'essential': True,
              'image': props['ecrImage'],
              'memory': 128,
              'command': [
                '--process',
                'METProcess',
                '--environment',
                'production',
                '--ingestType',
                'daily',
              ],
              'environment': [
                {
                  'name': 'ENVIRONMENT',
                  'value': props['environment'],
                },
                {
                  'name': 'ELASTICSEARCH_HOST',
                  'value': props['elasticSearchHost'],
                },
                {
                  'name': 'ELASTICSEARCH_INDEX',
                  'value': props['elasticSearchIndex'],
                },
              ],
              'secrets': [
                {
                  'name': 'POSTGRES_USER',
                  'valueFrom': props['postgreSqlUser'],
                },
                {
                  'name': 'POSTGRES_PSWD',
                  'valueFrom': props['postgreSqlPassword'],
                },
                {
                  'name': 'AWS_ACCESS',
                  'valueFrom': props['s3awsAccessKey'],
                },
                {
                  'name': 'AWS_SECRET',
                  'valueFrom': props['s3awsSecretKey'],
                },
                {
                  'name': 'RABBIT_USER',
                  'valueFrom': props['rabbitMqUser'],
                },
                {
                  'name': 'RABBIT_PSWD',
                  'valueFrom': props['rabbitMqPassword'],
                },
                {
                  'name': 'NEW_RELIC_LICENSE_KEY',
                  'valueFrom': props['newRelicLicenseKey'],
                },
              ],
              'logConfiguration': {
                'logDriver': 'awslogs',
                'options': {
                  'awslogs-group': cloudwatchLogsGroup.ref,
                  'awslogs-region': self.region,
                  'awslogs-stream-prefix': props['metIngestTaskName'],
                },
              },
            },
          ],
        )

    ecsTaskDefinitionMuseIngestScheduled = ecs.CfnTaskDefinition(self, 'ECSTaskDefinitionMUSEIngestScheduled',
          family = props['museIngestTaskName'],
          execution_role_arn = ecsTaskRole.ref,
          container_definitions = [
            {
              'name': props['museIngestTaskName'],
              'essential': True,
              'image': props['ecrImage'],
              'memory': 256,
              'command': [
                '--process',
                'MUSEProcess',
                '--environment',
                'production',
                '--ingestType',
                'daily',
              ],
              'environment': [
                {
                  'name': 'ENVIRONMENT',
                  'value': props['environment'],
                },
                {
                  'name': 'ELASTICSEARCH_HOST',
                  'value': props['elasticSearchHost'],
                },
                {
                  'name': 'ELASTICSEARCH_INDEX',
                  'value': props['elasticSearchIndex'],
                },
              ],
              'secrets': [
                {
                  'name': 'POSTGRES_USER',
                  'valueFrom': props['postgreSqlUser'],
                },
                {
                  'name': 'POSTGRES_PSWD',
                  'valueFrom': props['postgreSqlPassword'],
                },
                {
                  'name': 'AWS_ACCESS',
                  'valueFrom': props['s3awsAccessKey'],
                },
                {
                  'name': 'AWS_SECRET',
                  'valueFrom': props['s3awsSecretKey'],
                },
                {
                  'name': 'RABBIT_USER',
                  'valueFrom': props['rabbitMqUser'],
                },
                {
                  'name': 'RABBIT_PSWD',
                  'valueFrom': props['rabbitMqPassword'],
                },
                {
                  'name': 'NEW_RELIC_LICENSE_KEY',
                  'valueFrom': props['newRelicLicenseKey'],
                },
              ],
              'logConfiguration': {
                'logDriver': 'awslogs',
                'options': {
                  'awslogs-group': cloudwatchLogsGroup.ref,
                  'awslogs-region': self.region,
                  'awslogs-stream-prefix': props['museIngestTaskName'],
                },
              },
            },
          ],
        )

    ecsTaskDefinitionNyplIngestScheduled = ecs.CfnTaskDefinition(self, 'ECSTaskDefinitionNYPLIngestScheduled',
          family = props['nyplIngestTaskName'],
          execution_role_arn = ecsTaskRole.ref,
          container_definitions = [
            {
              'name': props['nyplIngestTaskName'],
              'essential': True,
              'image': props['ecrImage'],
              'memory': 256,
              'command': [
                '--process',
                'NYPLProcess',
                '--environment',
                'production',
                '--ingestType',
                'daily',
              ],
              'environment': [
                {
                  'name': 'ENVIRONMENT',
                  'value': props['environment'],
                },
                {
                  'name': 'ELASTICSEARCH_HOST',
                  'value': props['elasticSearchHost'],
                },
                {
                  'name': 'ELASTICSEARCH_INDEX',
                  'value': props['elasticSearchIndex'],
                },
              ],
              'secrets': [
                {
                  'name': 'POSTGRES_USER',
                  'valueFrom': props['postgreSqlUser'],
                },
                {
                  'name': 'POSTGRES_PSWD',
                  'valueFrom': props['postgreSqlPassword'],
                },
                {
                  'name': 'NYPL_API_CLIENT_ID',
                  'valueFrom': props['nyplApiClientId'],
                },
                {
                  'name': 'NYPL_API_CLIENT_SECRET',
                  'valueFrom': props['nyplApiClientSecret'],
                },
                {
                  'name': 'NYPL_BIB_USER',
                  'valueFrom': props['nyplPostgreSqlUser'],
                },
                {
                  'name': 'NYPL_BIB_PSWD',
                  'valueFrom': props['nyplPostgreSqlPassword'],
                },
                {
                  'name': 'NEW_RELIC_LICENSE_KEY',
                  'valueFrom': props['newRelicLicenseKey'],
                },
              ],
              'logConfiguration': {
                'logDriver': 'awslogs',
                'options': {
                  'awslogs-group': cloudwatchLogsGroup.ref,
                  'awslogs-region': self.region,
                  'awslogs-stream-prefix': props['nyplIngestTaskName'],
                },
              },
            },
          ],
        )

    ecsTaskDefinitionS3FilesScheduled = ecs.CfnTaskDefinition(self, 'ECSTaskDefinitionS3FilesScheduled',
          family = props['s3FilesTaskName'],
          execution_role_arn = ecsTaskRole.ref,
          container_definitions = [
            {
              'name': props['s3FilesTaskName'],
              'essential': True,
              'image': props['ecrImage'],
              'memory': 1024,
              'command': [
                '--process',
                'S3Process',
                '--environment',
                'production',
              ],
              'environment': [
                {
                  'name': 'ENVIRONMENT',
                  'value': props['environment'],
                },
                {
                  'name': 'ELASTICSEARCH_HOST',
                  'value': props['elasticSearchHost'],
                },
                {
                  'name': 'ELASTICSEARCH_INDEX',
                  'value': props['elasticSearchIndex'],
                },
              ],
              'secrets': [
                {
                  'name': 'POSTGRES_USER',
                  'valueFrom': props['postgreSqlUser'],
                },
                {
                  'name': 'POSTGRES_PSWD',
                  'valueFrom': props['postgreSqlPassword'],
                },
                {
                  'name': 'RABBIT_USER',
                  'valueFrom': props['rabbitMqUser'],
                },
                {
                  'name': 'RABBIT_PSWD',
                  'valueFrom': props['rabbitMqPassword'],
                },
                {
                  'name': 'AWS_ACCESS',
                  'valueFrom': props['s3awsAccessKey'],
                },
                {
                  'name': 'AWS_SECRET',
                  'valueFrom': props['s3awsSecretKey'],
                },
                {
                  'name': 'NEW_RELIC_LICENSE_KEY',
                  'valueFrom': props['newRelicLicenseKey'],
                },
              ],
              'logConfiguration': {
                'logDriver': 'awslogs',
                'options': {
                  'awslogs-group': cloudwatchLogsGroup.ref,
                  'awslogs-region': self.region,
                  'awslogs-stream-prefix': props['s3FilesTaskName'],
                },
              },
            },
          ],
        )

    ecsalbTargerGroup = elasticloadbalancingv2.CfnTargetGroup(self, 'ECSALBTargerGroup',
          health_check_interval_seconds = 15,
          health_check_path = '/',
          health_check_protocol = 'HTTP',
          health_check_timeout_seconds = 10,
          healthy_threshold_count = 2,
          matcher = {
            'httpCode': '200,301,302,401,400',
          },
          port = 80,
          protocol = 'HTTP',
          unhealthy_threshold_count = 2,
          vpc_id = props['vpcId'],
        )
    ecsalbTargerGroup.add_dependency(ecsalb)

    ecsClusteringTaskSchedule = events.CfnRule(self, 'ECSClusteringTaskSchedule',
          description = 'Cluster processed records',
          name = 'sfr-clustering-process-production',
          schedule_expression = 'cron(0 10 * * ? *)',
          state = 'ENABLED',
          targets = [
            {
              'id': 'sfr-cluster-process',
              'arn': ecsCluster.attr_arn,
              'ecsParameters': {
                'taskDefinitionArn': ecsTaskDefinitionClusterScheduled.ref,
              },
              'roleArn': ecsEventTaskRole.attr_arn,
            },
            {
              'id': 'sfr-cover-process',
              'arn': ecsCluster.attr_arn,
              'ecsParameters': {
                'taskDefinitionArn': ecsTaskDefinitionCoverScheduled.ref,
              },
              'roleArn': ecsEventTaskRole.attr_arn,
            },
          ],
        )

    ecshttpalbListener = elasticloadbalancingv2.CfnListener(self, 'ECSHTTPALBListener',
          default_actions = [
            {
              'type': 'redirect',
              'redirectConfig': {
                'protocol': 'HTTPS',
                'port': '443',
                'statusCode': 'HTTP_301',
              },
            },
          ],
          load_balancer_arn = ecsalb.ref,
          port = 80,
          protocol = 'HTTP',
        )
    ecshttpalbListener.add_dependency(ecsServiceRole)

    ecsIngestBatch2TaskSchedule = events.CfnRule(self, 'ECSIngestBatch2TaskSchedule',
          description = 'Import data daily from ingest sources',
          name = 'sfr-ingest-process-batch-2-production',
          schedule_expression = 'cron(0 6 * * ? *)',
          state = 'DISABLED',
          targets = [
            {
              'id': props['metIngestTaskName'],
              'arn': ecsCluster.attr_arn,
              'ecsParameters': {
                'taskDefinitionArn': ecsTaskDefinitionMetIngestScheduled.ref,
              },
              'roleArn': ecsEventTaskRole.attr_arn,
            },
          ],
        )

    ecsIngestTaskSchedule = events.CfnRule(self, 'ECSIngestTaskSchedule',
          description = 'Import data daily from ingest sources',
          name = 'sfr-ingest-process-production',
          schedule_expression = 'cron(0 6 * * ? *)',
          state = 'DISABLED',
          targets = [
            {
              'id': props['hathiIngestTaskName'],
              'arn': ecsCluster.attr_arn,
              'ecsParameters': {
                'taskDefinitionArn': ecsTaskDefinitionHathiIngestScheduled.ref,
              },
              'roleArn': ecsEventTaskRole.attr_arn,
            },
            {
              'id': props['doabIngestTaskName'],
              'arn': ecsCluster.attr_arn,
              'ecsParameters': {
                'taskDefinitionArn': ecsTaskDefinitionDoabIngestScheduled.ref,
              },
              'roleArn': ecsEventTaskRole.attr_arn,
            },
            {
              'id': props['gutenbergIngestTaskName'],
              'arn': ecsCluster.attr_arn,
              'ecsParameters': {
                'taskDefinitionArn': ecsTaskDefinitionGutenbergIngestScheduled.ref,
              },
              'roleArn': ecsEventTaskRole.attr_arn,
            },
            {
              'id': props['nyplIngestTaskName'],
              'arn': ecsCluster.attr_arn,
              'ecsParameters': {
                'taskDefinitionArn': ecsTaskDefinitionNyplIngestScheduled.ref,
              },
              'roleArn': ecsEventTaskRole.attr_arn,
            },
            {
              'id': props['museIngestTaskName'],
              'arn': ecsCluster.attr_arn,
              'ecsParameters': {
                'taskDefinitionArn': ecsTaskDefinitionMuseIngestScheduled.ref,
              },
              'roleArn': ecsEventTaskRole.attr_arn,
            },
          ],
        )

    ecsIngestTaskWeeklySchedule = events.CfnRule(self, 'ECSIngestTaskWeeklySchedule',
          description = 'Import data weekly from ingest sources',
          name = 'sfr-ingest-process-batch-3-production',
          schedule_expression = 'cron(0 14 ? * 2 *)',
          state = 'DISABLED',
          targets = [
            {
              'id': props['locIngestTaskName'],
              'arn': ecsCluster.attr_arn,
              'ecsParameters': {
                'taskDefinitionArn': ecsTaskDefinitionLocIngestScheduled.ref,
              },
              'roleArn': ecsEventTaskRole.attr_arn,
            },
          ],
        )

    ecsLaunchConfiguration = autoscaling.CfnLaunchConfiguration(self, 'ECSLaunchConfiguration',
          image_id = props['ecsAmiParameterKey'],
          security_groups = [
            ecsSecurityGroup.ref,
          ],
          instance_type = props['instanceType'],
          iam_instance_profile = ec2InstanceProfile.ref,
          key_name = props['keyName'],
          user_data = cdk.Fn.base64(''.join([
            '#!/bin/bash -xe\n',
            'yum update -y\n',
            'echo ECS_CLUSTER=',
            ecsCluster.ref,
            ' >> /etc/ecs/ecs.config\n',
            'yum install -y aws-cfn-bootstrap\n',
            '/opt/aws/bin/cfn-signal -e $? ',
            '         --stack ',
            self.stack_name,
            '         --resource ECSAutoScalingGroup ',
            '         --region ',
            self.region,
            '\n',
            'yum install -y awscli\n',
            'echo \"display_name: ',
            props['serviceName'],
            ' ($(curl http://169.254.169.254/latest/meta-data/instance-id))',
            '\" | sudo tee /etc/newrelic-infra.yml\n',
            'echo \"license_key: $(aws ssm get-parameter --region ',
            self.region,
            ' --name /drb/production/newrelic/key --with-decryption --query \'Parameter.Value\')\"',
            ' | sudo tee -a /etc/newrelic-infra.yml\n',
            'sudo curl -o /etc/yum.repos.d/newrelic-infra.repo ',
            'https://download.newrelic.com/infrastructure_agent/linux/yum/amazonlinux/2/x86_64/newrelic-infra.repo\n',
            'sudo yum -q makecache -y --disablerepo=\'*\' --enablerepo=\'newrelic-infra\'\n',
            'sudo yum install newrelic-infra -y\n',
            'curl https://nypl-newrelic-config.s3.amazonaws.com/logging.yml ',
            '| sudo tee /etc/newrelic-infra/logging.d/logging.yml\n',
            'sudo systemctl enable newrelic-infra\n',
            'sudo systemctl start newrelic-infra\n',
            'curl https://nypl-provisioning.s3.amazonaws.com/provision-yumbased-linux.sh | bash\n',
            'reboot\n',
          ])),
        )

    ecsMaintenanceTaskSchedule = events.CfnRule(self, 'ECSMaintenanceTaskSchedule',
          description = 'Perform Database Maintenance',
          name = 'sfr-db-maintenance-task-production',
          schedule_expression = 'cron(0 1 ? * 3 *)',
          state = 'ENABLED',
          targets = [
            {
              'id': 'sfr-db-maintenance',
              'arn': ecsCluster.attr_arn,
              'ecsParameters': {
                'taskDefinitionArn': ecsTaskDefinitionDatabaseMaintenanceScheduled.ref,
              },
              'roleArn': ecsEventTaskRole.attr_arn,
            },
          ],
        )

    ecsProcessingTaskSchedule = events.CfnRule(self, 'ECSProcessingTaskSchedule',
          description = 'Process data ingested from sources',
          name = 'sfr-processing-process-production',
          schedule_expression = 'cron(0 8 * * ? *)',
          state = 'ENABLED',
          targets = [
            {
              'id': 'sfr-s3-files-process',
              'arn': ecsCluster.attr_arn,
              'ecsParameters': {
                'taskDefinitionArn': ecsTaskDefinitionS3FilesScheduled.ref,
              },
              'roleArn': ecsEventTaskRole.attr_arn,
            },
          ],
        )

    ecsAutoScalingGroup = autoscaling.CfnAutoScalingGroup(self, 'ECSAutoScalingGroup',
          vpc_zone_identifier = props['privateSubnets'],
          launch_configuration_name = ecsLaunchConfiguration.ref,
          min_size = '1',
          max_size = props['maxSize'],
          desired_capacity = props['desiredCapacity'],
        )
    ecsAutoScalingGroup.cfn_options.update_policy = {
      'AutoScalingReplacingUpdate': {
        'WillReplace': 'true',
      },
    }
    ecshttpsalbListener = elasticloadbalancingv2.CfnListener(self, 'ECSHTTPSALBListener',
          certificates = [
            {
              'certificateArn': props['loadBalancerCertificateArn'],
            },
          ],
          default_actions = [
            {
              'type': 'forward',
              'targetGroupArn': ecsalbTargerGroup.ref,
            },
          ],
          load_balancer_arn = ecsalb.ref,
          port = 443,
          protocol = 'HTTPS',
        )
    ecshttpsalbListener.add_dependency(ecsServiceRole)

    ecsService = ecs.CfnService(self, 'ECSService',
          cluster = ecsCluster.ref,
          service_name = props['serviceName'],
          desired_count = props['taskCount'],
          load_balancers = [
            {
              'containerName': props['serviceName'],
              'containerPort': 80,
              'targetGroupArn': ecsalbTargerGroup.ref,
            },
          ],
          role = ecsServiceRole.ref,
          task_definition = ecsTaskDefinition.ref,
        )
    ecsService.add_dependency(ecshttpsalbListener)
    ecsService.add_dependency(ecshttpalbListener)

    cpuScaleInAlarm = cloudwatch.CfnAlarm(self, 'CPUScaleInAlarm',
          alarm_name = '-'.join([
            props['pMasterStackName'],
            'CPU utilization greater than 35%',
          ]),
          alarm_description = 'Alarm if cpu utilization greater than 35% of reserved cpu',
          namespace = 'AWS/ECS',
          metric_name = 'CPUUtilization',
          dimensions = [
            {
              'name': 'ClusterName',
              'value': ecsCluster.ref,
            },
            {
              'name': 'ServiceName',
              'value': ecsService.attr_name,
            },
          ],
          statistic = 'Maximum',
          period = 60,
          evaluation_periods = 10,
          threshold = 35,
          comparison_operator = 'GreaterThanThreshold',
          alarm_actions = [
            props['alertSnsTopicArn'],
          ],
        )

    serviceScalingTarget = applicationautoscaling.CfnScalableTarget(self, 'ServiceScalingTarget',
          max_capacity = 2,
          min_capacity = 1,
          resource_id = ''.join([
            'service/',
            ecsCluster.ref,
            '/',
            ecsService.attr_name,
          ]),
          role_arn = autoscalingRole.attr_arn,
          scalable_dimension = 'ecs:service:DesiredCount',
          service_namespace = 'ecs',
        )
    serviceScalingTarget.add_dependency(ecsService)

    serviceScalingPolicy = applicationautoscaling.CfnScalingPolicy(self, 'ServiceScalingPolicy',
          policy_name = 'AStepPolicy',
          policy_type = 'StepScaling',
          scaling_target_id = serviceScalingTarget.ref,
          step_scaling_policy_configuration = {
            'adjustmentType': 'PercentChangeInCapacity',
            'cooldown': 60,
            'metricAggregationType': 'Average',
            'stepAdjustments': [
              {
                'metricIntervalLowerBound': 0,
                'scalingAdjustment': 200,
              },
            ],
          },
        )

    alb500sAlarmScaleUp = cloudwatch.CfnAlarm(self, 'ALB500sAlarmScaleUp',
          evaluation_periods = 1,
          statistic = 'Average',
          threshold = 10,
          alarm_description = 'Alarm if our ALB generates too many HTTP 500s.',
          period = 60,
          alarm_actions = [
            serviceScalingPolicy.ref,
          ],
          namespace = 'AWS/ApplicationELB',
          dimensions = [
            {
              'name': 'LoadBalancer',
              'value': ecsalb.attr_load_balancer_full_name,
            },
          ],
          comparison_operator = 'GreaterThanThreshold',
          metric_name = 'HTTPCode_ELB_5XX_Count',
        )

    # Outputs
    """
      ECS Service Name
    """
    self.ecs_service = ecsService.ref
    cdk.CfnOutput(self, 'CfnOutputECSService', 
      key = 'ECSService',
      description = 'ECS Service Name',
      export_name = '-'.join([
        'oECSService',
        props['pMasterStackName'],
      ]),
      value = str(self.ecs_service),
    )

    """
      ECS Cluster Name
    """
    self.ecs_cluster = ecsCluster.ref
    cdk.CfnOutput(self, 'CfnOutputECSCluster', 
      key = 'ECSCluster',
      description = 'ECS Cluster Name',
      export_name = '-'.join([
        'oECSCluster',
        props['pMasterStackName'],
      ]),
      value = str(self.ecs_cluster),
    )

    """
      ECS ALB DNS endpoint
    """
    self.ecsalb = ecsalb.attr_dns_name
    cdk.CfnOutput(self, 'CfnOutputECSALB', 
      key = 'ECSALB',
      description = 'ECS ALB DNS endpoint',
      export_name = '-'.join([
        'oECSALB',
        props['pMasterStackName'],
      ]),
      value = str(self.ecsalb),
    )

    """
      ECS Task definition
    """
    self.ecs_taskdef = ecsTaskDefinition.ref
    cdk.CfnOutput(self, 'CfnOutputECSTaskdef', 
      key = 'ECSTaskdef',
      description = 'ECS Task definition',
      export_name = '-'.join([
        'oECSTaskdef',
        props['pMasterStackName'],
      ]),
      value = str(self.ecs_taskdef),
    )



