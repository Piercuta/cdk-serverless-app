from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    aws_s3 as s3,
    aws_iam as iam,
    Duration,
    CfnOutput,
    RemovalPolicy,
    BundlingOptions
)
from constructs import Construct
from config import Config


class ImageProcessingStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Créer le bucket S3 pour les images redimensionnées
        destination_bucket = s3.Bucket(
            self, "ResizedImagesBucket",
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            cors=[
                s3.CorsRule(
                    allowed_headers=["*"],
                    allowed_methods=[s3.HttpMethods.GET, s3.HttpMethods.PUT,
                                     s3.HttpMethods.POST, s3.HttpMethods.DELETE, s3.HttpMethods.HEAD],
                    # Spécifiez vos origines
                    allowed_origins=[
                        "https://" + Config.get_domain_name(),
                        "http://localhost:3000"
                    ],
                    exposed_headers=["ETag"],
                    max_age=3000
                )
            ]
        )

        # Créer la Lambda avec bundling
        image_processor = lambda_.Function(
            self, "ImageProcessor",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="app.lambda_handler",
            code=lambda_.Code.from_asset(
                "lambda/image_processor",
                bundling=BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_11.bundling_image,
                    command=[
                        "bash", "-c",
                        "pip install -r requirements.txt -t /asset-output && cp -r . /asset-output"
                    ]
                )
            ),
            timeout=Duration.seconds(Config.get_lambda_timeout()),
            memory_size=Config.get_lambda_memory_size(),
            environment={
                "DESTINATION_BUCKET": destination_bucket.bucket_name
            }
        )

        # Ajouter les permissions S3 à la Lambda
        destination_bucket.grant_put(image_processor)
        destination_bucket.grant_read(image_processor)

        # Ajouter les permissions CloudWatch Logs
        image_processor.add_to_role_policy(
            iam.PolicyStatement(
                actions=["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
                resources=["*"]
            )
        )

        # Output les informations importantes
        CfnOutput(
            self, "DestinationBucketName",
            value=destination_bucket.bucket_name,
            description="Nom du bucket de destination"
        )

        CfnOutput(
            self, "ImageProcessorArn",
            value=image_processor.function_arn,
            description="ARN de la fonction Lambda"
        )

        # Exposer la Lambda pour l'API Gateway
        self.image_processor = image_processor
