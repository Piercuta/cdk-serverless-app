from aws_cdk import (
    Stack,
    aws_apigatewayv2 as apigatewayv2,
    aws_lambda as lambda_,
    CfnOutput
)
from aws_cdk.aws_apigatewayv2_integrations import HttpLambdaIntegration
from constructs import Construct


class ApiGatewayStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, image_processor_lambda: lambda_.Function, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        lambda_integration = HttpLambdaIntegration(
            "LambdaIntegration",
            handler=image_processor_lambda
        )

        http_api = apigatewayv2.HttpApi(
            self, "ImageProcessingHttpApi",
            cors_preflight=apigatewayv2.CorsPreflightOptions(
                allow_headers=["*"],
                allow_methods=[apigatewayv2.CorsHttpMethod.ANY],
                allow_origins=["*"]
            )
        )

        http_api.add_routes(
            path="/resize-image",
            methods=[apigatewayv2.HttpMethod.POST],
            integration=lambda_integration
        )

        CfnOutput(
            self, "HttpApiUrl",
            value=http_api.default_stage.url,
            description="URL de l'API HTTP Gateway"
        )

        self.api_url = http_api.default_stage.url
