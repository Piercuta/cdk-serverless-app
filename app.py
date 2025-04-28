#!/usr/bin/env python3
from aws_cdk import App, Environment
from stacks.front_stack import FrontStack
from stacks.image_processing_stack import ImageProcessingStack
from stacks.api_gateway_stack import ApiGatewayStack
from config import Config

app = App()

# Créer la stack de traitement d'images
image_processing_stack = ImageProcessingStack(
    app, "ImageProcessingStack",
    env=Environment(**Config.get_env())
)

# Créer la stack API Gateway
api_gateway_stack = ApiGatewayStack(
    app, "ApiGatewayStack",
    image_processor_lambda=image_processing_stack.image_processor,
    env=Environment(**Config.get_env())
)

# Créer la stack frontend
front_stack = FrontStack(
    app, "FrontStack",
    description="Deploy a React website to AWS CloudFront",
    api_url=api_gateway_stack.api_url,
    env=Environment(**Config.get_env())
)

app.synth()
