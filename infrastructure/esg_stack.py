from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_kms as kms,
    aws_logs as logs,
    aws_apigateway as apigateway,
    aws_s3_deployment as s3deploy,
    RemovalPolicy
)
from constructs import Construct

class ESGReportingStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # KMS Key for encryption
        self.kms_key = kms.Key(
            self, "ESGDataKey",
            description="KMS key for ESG data encryption",
            enable_key_rotation=True
        )
        
        # S3 Buckets (with unique names)
        self.raw_data_bucket = s3.Bucket(
            self, "ESGRawDataBucket",
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.kms_key,
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY
        )
        
        self.reports_bucket = s3.Bucket(
            self, "ESGReportsBucket",
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.kms_key,
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY
        )
        
        # DynamoDB Table
        self.esg_table = dynamodb.Table(
            self, "ESGProcessedData",
            table_name="esg-processed-data",
            partition_key=dynamodb.Attribute(
                name="id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            removal_policy=RemovalPolicy.DESTROY
        )
        
        # IAM Role for Lambda functions
        self.lambda_role = iam.Role(
            self, "ESGLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        
        # Add permissions to Lambda role
        self.lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "textract:StartDocumentAnalysis",
                    "textract:GetDocumentAnalysis",
                    "bedrock:InvokeModel",
                    "kendra:Query",
                    "kendra:Retrieve"
                ],
                resources=["*"]
            )
        )
        
        # Grant permissions for S3 and DynamoDB
        self.raw_data_bucket.grant_read_write(self.lambda_role)
        self.reports_bucket.grant_read_write(self.lambda_role)
        self.esg_table.grant_read_write_data(self.lambda_role)
        self.kms_key.grant_encrypt_decrypt(self.lambda_role)
        
        # Lambda Functions
        self.data_ingestion_lambda = _lambda.Function(
            self, "DataIngestionFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="data_ingestion.lambda_handler",
            code=_lambda.Code.from_asset("src/lambda_functions"),
            role=self.lambda_role,
            timeout=Duration.minutes(5),
            memory_size=512,
            environment={
                "RAW_DATA_BUCKET": self.raw_data_bucket.bucket_name,
                "KMS_KEY_ID": self.kms_key.key_id
            }
        )
        
        self.data_processing_lambda = _lambda.Function(
            self, "DataProcessingFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="data_processing.lambda_handler",
            code=_lambda.Code.from_asset("src/lambda_functions"),
            role=self.lambda_role,
            timeout=Duration.minutes(5),
            memory_size=1024,
            environment={
                "ESG_TABLE_NAME": self.esg_table.table_name,
                "KMS_KEY_ID": self.kms_key.key_id
            }
        )
        
        self.report_generation_lambda = _lambda.Function(
            self, "ReportGenerationFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="report_generation.lambda_handler",
            code=_lambda.Code.from_asset("src/lambda_functions"),
            role=self.lambda_role,
            timeout=Duration.minutes(10),
            memory_size=2048,
            environment={
                "ESG_TABLE_NAME": self.esg_table.table_name,
                "REPORTS_BUCKET": self.reports_bucket.bucket_name,
                "KMS_KEY_ID": self.kms_key.key_id
            }
        )
        
        # Production ESG Scraper Function (FINAL VERSION)
        self.esg_scraper_lambda = _lambda.Function(
            self, "ESGScraperFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="production_esg_scraper.lambda_handler",
            code=_lambda.Code.from_asset("src/lambda_functions"),
            role=self.lambda_role,
            timeout=Duration.minutes(5),
            memory_size=1024,
            environment={
                "ESG_TABLE_NAME": self.esg_table.table_name,
                "RAW_DATA_BUCKET": self.raw_data_bucket.bucket_name,
                "KMS_KEY_ID": self.kms_key.key_id
            }
        )
        
        # Report Generation Function (PRODUCTION)
        self.report_generation_lambda = _lambda.Function(
            self, "ReportGenerationFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="professional_report_generator.lambda_handler",
            code=_lambda.Code.from_asset("src/lambda_functions"),
            role=self.lambda_role,
            timeout=Duration.minutes(10),
            memory_size=2048,
            environment={
                "ESG_TABLE_NAME": self.esg_table.table_name,
                "REPORTS_BUCKET": self.reports_bucket.bucket_name,
                "KMS_KEY_ID": self.kms_key.key_id
            }
        )
        
        # CloudWatch Log Groups
        logs.LogGroup(
            self, "DataIngestionLogs",
            log_group_name=f"/aws/lambda/{self.data_ingestion_lambda.function_name}",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY
        )
        
        logs.LogGroup(
            self, "DataProcessingLogs",
            log_group_name=f"/aws/lambda/{self.data_processing_lambda.function_name}",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY
        )
        
        logs.LogGroup(
            self, "ReportGenerationLogs",
            log_group_name=f"/aws/lambda/{self.report_generation_lambda.function_name}",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY
        )
        
        logs.LogGroup(
            self, "ESGScraperLogs",
            log_group_name=f"/aws/lambda/{self.esg_scraper_lambda.function_name}",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY
        )
        
        # S3 Bucket for Frontend Website
        self.frontend_bucket = s3.Bucket(
            self, "ESGFrontendBucket",
            website_index_document="index.html",
            public_read_access=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ACLS,
            removal_policy=RemovalPolicy.DESTROY
        )
        
        # API Gateway
        self.api = apigateway.RestApi(
            self, "ESGApi",
            rest_api_name="ESGenius AI API",
            description="Global ESG Intelligence Platform API",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "Authorization"]
            )
        )
        
        # API Gateway Integrations (PRODUCTION)
        scraper_integration = apigateway.LambdaIntegration(self.esg_scraper_lambda)
        report_integration = apigateway.LambdaIntegration(self.report_generation_lambda)
        
        # API Routes
        api_v1 = self.api.root.add_resource("api").add_resource("v1")
        
        analyze_resource = api_v1.add_resource("analyze")
        analyze_resource.add_method("POST", scraper_integration)
        
        report_resource = api_v1.add_resource("report")
        report_resource.add_method("POST", report_integration)
        
        # Deploy Frontend to S3
        s3deploy.BucketDeployment(
            self, "DeployFrontend",
            sources=[s3deploy.Source.asset("frontend")],
            destination_bucket=self.frontend_bucket
        )
